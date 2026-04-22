import os
import base64
from io import BytesIO
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from typing import List
from concurrent.futures import ThreadPoolExecutor
import zipfile
import json
import tempfile

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

client = InferenceClient(api_key=HF_TOKEN) if HF_TOKEN else None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BrandRequest(BaseModel):
    prompt: str

class SuggestRequest(BaseModel):
    industry: str

class MediaBuyingRequest(BaseModel):
    company_name: str
    industry: str
    product: str
    usp: str
    objective: str
    audience: str
    pain_points: str
    tone: str
    platforms: List[str]

class KitRequest(BaseModel):
    brand_name: str
    industry: str
    description: str
    color_palette: List[str]
    fonts: List[str]
    formats: List[str]
    tagline: str
    cta_text: str
    language: str

# Frontend payload (new UI sends this shape)
class KitRequestV2(BaseModel):
    brand_name: str
    industry: str
    description: str
    color_palette: List[str]
    display_font: str | None = None
    body_font: str | None = None
    formats: List[str]
    tagline: str
    cta_text: str
    hashtags: str | None = None
    language: str

def query_stable_diffusion(prompt, width=512, height=512):
    """Generate an image with Hugging Face InferenceClient and return PNG bytes."""
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN missing. Add it to your .env to enable image generation.")
    if client is None:
        raise RuntimeError("Hugging Face client unavailable. Check HF_TOKEN in .env.")
    models_to_try = [
        "runwayml/stable-diffusion-v1-5",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "black-forest-labs/FLUX.1-schnell",
        None,  # let HF pick a default provider/model
    ]
    last_error = None

    for model_id in models_to_try:
        try:
            kwargs = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_inference_steps": 20,
            }
            if model_id is not None:
                kwargs["model"] = model_id
            img = client.text_to_image(**kwargs)
            buf = BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Image generation failed for all models. Last error: {last_error}")

@app.post("/api/generate-image")
def generate_image(data: BrandRequest):
    try:
        enhanced_prompt = f"Professional minimalist design for {data.prompt}, high resolution, clean, white background"
        image_bytes = query_stable_diffusion(enhanced_prompt, 512, 512)
        img_base64 = base64.b64encode(image_bytes).decode()
        return {"image": img_base64}
    except Exception as e:
        return {"error": str(e)}

def _fallback_palettes(industry: str) -> list[list[str]]:
    # 5 colors per palette, because the UI has 5 pickers.
    fallback = {
        "Technology": [
            ["#2563EB", "#3B82F6", "#60A5FA", "#1E3A8A", "#0B1220"],
            ["#0EA5E9", "#22C55E", "#F59E0B", "#111827", "#E5E7EB"],
            ["#4F46E5", "#06B6D4", "#A78BFA", "#0F172A", "#F1F5F9"],
        ],
        "Fashion": [
            ["#EC4899", "#F43F5E", "#8B5CF6", "#2DD4BF", "#0F172A"],
            ["#111827", "#F472B6", "#FB7185", "#F5F5F5", "#A78BFA"],
            ["#BE185D", "#F9A8D4", "#FCA5A5", "#0B1220", "#E2E8F0"],
        ],
        "Food": [
            ["#EF4444", "#F59E0B", "#10B981", "#F97316", "#111827"],
            ["#14532D", "#22C55E", "#FDE047", "#FB7185", "#0F172A"],
            ["#991B1B", "#F97316", "#FCD34D", "#065F46", "#F8FAFC"],
        ],
        "Healthcare": [
            ["#0EA5E9", "#14B8A6", "#8B5CF6", "#6366F1", "#0F172A"],
            ["#0F172A", "#22C55E", "#06B6D4", "#F1F5F9", "#94A3B8"],
            ["#0284C7", "#A7F3D0", "#E0E7FF", "#1E293B", "#F8FAFC"],
        ],
        "Finance": [
            ["#0F172A", "#1E293B", "#334155", "#475569", "#E2E8F0"],
            ["#111827", "#2563EB", "#22C55E", "#F8FAFC", "#94A3B8"],
            ["#0B1220", "#0EA5E9", "#A78BFA", "#E5E7EB", "#1F2937"],
        ],
        "Education": [
            ["#F59E0B", "#FCD34D", "#FEF08A", "#FDE047", "#111827"],
            ["#2563EB", "#22C55E", "#F59E0B", "#F8FAFC", "#0F172A"],
            ["#7C3AED", "#60A5FA", "#34D399", "#FCD34D", "#0B1220"],
        ],
        "Entertainment": [
            ["#D946EF", "#F43F5E", "#8B5CF6", "#EC4899", "#0F172A"],
            ["#0F172A", "#22C55E", "#F59E0B", "#60A5FA", "#F8FAFC"],
            ["#701A75", "#A78BFA", "#FB7185", "#06B6D4", "#111827"],
        ],
    }
    return fallback.get(industry, [
        ["#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#111827"],
        ["#4F46E5", "#06B6D4", "#F97316", "#F8FAFC", "#0F172A"],
        ["#22C55E", "#A78BFA", "#FB7185", "#E2E8F0", "#111827"],
    ])

@app.post("/api/suggest-colors")
def suggest_colors_api(data: SuggestRequest):
    # UI expects { palettes: string[][] }
    return {"palettes": _fallback_palettes(data.industry)}

# Backward compatible endpoint (older frontend/script.js expects {colors: [...] })
@app.post("/suggest-colors")
def suggest_colors_legacy(data: SuggestRequest):
    palettes = _fallback_palettes(data.industry)
    return {"colors": palettes[0]}

@app.post("/api/generate-media-strategy")
def generate_media_strategy(data: MediaBuyingRequest):
    try:
        if client is None:
            return {"error": "HF_TOKEN missing. Add it to your .env to enable strategy generation.", "strategy": ""}
        platforms_str = ", ".join(data.platforms)
        
        prompt_text = f"""Act as a Senior Media Buying and Creative Strategy Expert.

BUSINESS CONTEXT:
- Company: {data.company_name}
- Industry: {data.industry}
- Product: {data.product}
- USP: {data.usp}

OBJECTIVE & TARGET:
- Objective: {data.objective}
- Target Audience: {data.audience}
- Problem Solved: {data.pain_points}
- Tone: {data.tone}

Platforms: {platforms_str}

Generate a complete marketing strategy with 3 parts:

PART 1 - STRATEGIC ANALYSIS:
1.1 Main hook/angle (psychological trigger)
1.2 Funnel structure (Top, Middle, Bottom of Funnel)

PART 2 - CREATIVE CONCEPTS:
For each platform, provide 3 concepts:

Platform: [Platform Name]
- Concept 1 (Direct Response): Focus on product/benefit. Include: Hook (first 3 seconds), Script/visual description, CTA
- Concept 2 (Storytelling/Social Proof): Focus on customer experience. Include: Hook, Script/visual description, CTA
- Concept 3 (Education/Entertainment): Focus on problem solved. Include: Hook, Script/visual description, CTA

PART 3 - TECHNICAL RECOMMENDATIONS:
- Targeting advice per platform
- Recommended formats (Reels, Carousel, Search text, etc.)

Be specific, actionable, and use punchy marketing language."""

        response = client.text_generation(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            prompt=prompt_text,
            max_new_tokens=2000,
            temperature=0.7
        )
        return {"strategy": response}
    except Exception as e:
        return {"error": str(e), "strategy": "Error generating strategy"}

def _normalize_format(fmt: str) -> str:
    # The UI sometimes sends "Name (WxH)".
    base = fmt.split(" (", 1)[0].strip()
    mapping = {
        "Instagram Story": "Story",
        "TikTok Post": "Story",
        "WhatsApp Status": "Story",
        "Instagram Post": "Instagram Post",
        "Business Card": "Business Card",
        "YouTube Cover": "YouTube Cover",
    }
    return mapping.get(base, base)

def _generate_images_for_formats(
    brand_name: str,
    industry: str,
    color_palette: list[str],
    formats: list[str],
):
    try:
        images = {}
        industry_moods = {
            "Technology": "futuristic, innovative, digital",
            "Fashion": "elegant, stylish, trendy",
            "Food": "warm, appetizing, fresh",
            "Healthcare": "clean, trustworthy, calming",
        }
        mood = industry_moods.get(industry, "modern, professional")

        for raw_fmt in formats:
            fmt = _normalize_format(raw_fmt)
            if fmt == "Instagram Post":
                prompt = f"Abstract geometric design for {brand_name}, {industry} brand. Colors: {', '.join(color_palette)}. Style: {mood}. No text, no people. 1080x1080"
                img_bytes = query_stable_diffusion(prompt, 1080, 1080)
                images[raw_fmt] = base64.b64encode(img_bytes).decode()
            elif fmt == "Story":
                prompt = f"Abstract vertical design for {brand_name}, {industry}. Colors: {', '.join(color_palette)}. Style: {mood}. No text. 1080x1920"
                img_bytes = query_stable_diffusion(prompt, 1080, 1920)
                images[raw_fmt] = base64.b64encode(img_bytes).decode()
            elif fmt == "YouTube Cover":
                prompt = f"Abstract banner for {brand_name}, {industry}. Colors: {', '.join(color_palette)}. Style: {mood}. No text. 1920x1080"
                img_bytes = query_stable_diffusion(prompt, 1920, 1080)
                images[raw_fmt] = base64.b64encode(img_bytes).decode()
            elif fmt == "Business Card":
                prompt = f"Abstract business card design for {brand_name}, {industry}. Colors: {', '.join(color_palette)}. Style: {mood}. 1000x600"
                img_bytes = query_stable_diffusion(prompt, 1000, 600)
                images[raw_fmt] = base64.b64encode(img_bytes).decode()

        return {"images": images}
    except Exception as e:
        return {"error": str(e), "images": {}}

@app.post("/api/generate-kit")
def generate_kit_api(data: KitRequestV2):
    return _generate_images_for_formats(
        brand_name=data.brand_name,
        industry=data.industry,
        color_palette=data.color_palette,
        formats=data.formats,
    )

# Backward compatible endpoint (older frontend/script.js hits this)
@app.post("/generate-kit")
def generate_kit_legacy(data: KitRequest):
    return _generate_images_for_formats(
        brand_name=data.brand_name,
        industry=data.industry,
        color_palette=data.color_palette,
        formats=data.formats,
    )

@app.post("/api/download-zip")
def download_zip(images: dict):
    """
    Expects a JSON object like { "Format Name": "<base64png>", ... }
    Returns a ZIP containing PNGs.
    """
    tmp = BytesIO()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, b64 in (images or {}).items():
            if not b64 or not isinstance(b64, str):
                continue
            try:
                data = base64.b64decode(b64)
            except Exception:
                continue
            safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_", " ") else "_" for ch in str(name)).strip()
            if not safe_name:
                safe_name = "image"
            zf.writestr(f"{safe_name}.png", data)
    tmp.seek(0)
    return StreamingResponse(
        tmp,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="brand_kit.zip"'},
    )

# Serve the frontend via http://localhost:8000/ to avoid file:// CORS/origin issues.
_frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
import os
import base64
from io import BytesIO
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# 1. Charger les variables secrètes depuis le fichier .env
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# 2. Initialiser le client Hugging Face
# Si le token est vide, une erreur sera affichée au lancement
if not HF_TOKEN:
    print("ERREUR : Le token HF_TOKEN n'est pas trouvé dans le fichier .env")
client = InferenceClient(api_key=HF_TOKEN)

app = FastAPI()

# 3. Configuration CORS (pour que le frontend port 3000 puisse parler au backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles de données pour les requêtes
class BrandRequest(BaseModel):
    prompt: str

# --- ENDPOINT 1 : GÉNÉRATION D'IMAGE (LOGO) ---
@app.post("/generate-image")
def generate_image(data: BrandRequest):
    try:
        # Prompt enrichi pour une meilleure qualité de logo
        enhanced_prompt = f"Professional minimalist vector logo for {data.prompt}, high resolution, clean lines, white background, high quality, 4k"
        
        image = client.text_to_image(
            prompt=enhanced_prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0"
        )

        # Sauvegarde de l'image en mémoire (Buffer)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        
        # Encodage en Base64 pour l'envoi au frontend
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return {"image": img_base64}

    except Exception as e:
        print(f"Erreur Image: {str(e)}")
        return {"error": str(e)}

# --- ENDPOINT 2 : GÉNÉRATION D'INFOS (NOM, SLOGAN, COULEURS) ---
@app.post("/generate-brand-info")
def generate_brand_info(data: BrandRequest):
    try:
        # On demande à Mistral de créer une identité courte
        prompt_text = f"As a branding expert, create a brand identity for: {data.prompt}. Return only: Brand Name, a short Tagline, and 3 Hex color codes."
        
        response = client.text_generation(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            prompt=prompt_text,
            max_new_tokens=150
        )

        return {"brand_data": response}

    except Exception as e:
        print(f"Erreur Texte: {str(e)}")
        return {"error": str(e)}

# Lancer le serveur sur le port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
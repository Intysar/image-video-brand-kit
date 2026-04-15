from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import base64
import os

app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_TOKEN = os.getenv("HF_TOKEN")

# Make sure the URL is complete
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

class PromptInput(BaseModel):
    prompt: str

@app.post("/generate")
def generate(data: PromptInput):
    prompt = data.prompt
    
    print(f"Generating image for: {prompt}")
    print(f"Calling URL: {API_URL}")
    
    # The correct payload format for Hugging Face
    payload = {
        "inputs": prompt,
        "options": {
            "wait_for_model": True  # Wait for model to load
        }
    }
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60  # 60 second timeout
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Success - convert image to base64
            img_base64 = base64.b64encode(response.content).decode()
            return {"image": img_base64}
        else:
            # Error occurred
            return {
                "error": f"API Error: {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
load_dotenv()

from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card

app = FastAPI(title="GitHub Dev Card Generator API")

# Serve frontend
@app.get("/")
def home():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "GitHub Dev Card Generator API 🚀"}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
os.makedirs("static/cards", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Request model
class GenerateRequest(BaseModel):
    username: str

# Generate card API
@app.post("/generate")
async def generate_card(request: GenerateRequest):
    try:
        username = request.username.strip()
        # 1. Scrape GitHub data
        github_data = await scrape_github(username)
        
        # 2. Analyze profile
        analysis = await analyze_profile(github_data)
        
        # 3. Generate HTML
        card_html = await generate_card_html(username, github_data, analysis)
        
        # 4. Save to static
        card_url = await save_card(username, card_html)

        return {
            "status": "success",
            "username": username,
            "card_url": card_url,
            "card_html": card_html
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get card
@app.get("/card/{username}")
async def get_card(username: str):
    username = username.strip()
    path = f"static/cards/{username}.html"
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Card not found")

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Run server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
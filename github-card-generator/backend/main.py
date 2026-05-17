import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from agent import github_card_agent

app = FastAPI(title="GitHub Dev Card Generator API")

# Home route
@app.get("/")
def home():
    return {"message": "Backend running 🚀"}

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
        # Call agent
        result = github_card_agent(request.username)

        # Create HTML card
        card_html = f"""
        <html>
        <head>
            <title>{request.username} Card</title>
        </head>
        <body style="font-family: Arial; text-align: center;">
            <h1>GitHub Card 🚀</h1>
            <h2>{request.username}</h2>
            <p>{result['message']}</p>
        </body>
        </html>
        """

        # Save file
        card_path = f"static/cards/{request.username}.html"
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(card_html)

        return {
            "status": "success",
            "username": request.username,
            "card_url": f"/static/cards/{request.username}.html",
            "card_html": card_html
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get card
@app.get("/card/{username}")
async def get_card(username: str):
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
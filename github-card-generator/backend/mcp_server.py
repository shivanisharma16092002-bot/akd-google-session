import os
import json
import httpx
from google import genai
from mcp.server.fastmcp import FastMCP
from typing import List, Dict
from pathlib import Path

# Create an MCP server
mcp = FastMCP("GitHubDevCard")

# Configure Gemini client
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gemini_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch GitHub stats and top repos for a given username."""
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    async with httpx.AsyncClient() as client:
        # Fetch user profile
        user_url = f"https://api.github.com/users/{username}"
        user_res = await client.get(user_url, headers=headers)
        user_res.raise_for_status()
        user_data = user_res.json()

        # Fetch repos
        repos_url = f"https://api.github.com/users/{username}/repos?sort=stars&per_page=30"
        repos_res = await client.get(repos_url, headers=headers)
        repos_res.raise_for_status()
        repos_data = repos_res.json()

        # Aggregate languages and top 6 repos
        top_6_repos = []
        languages = {}
        for repo in repos_data:
            if len(top_6_repos) < 6:
                top_6_repos.append({
                    "name": repo["name"],
                    "stars": repo["stargazers_count"],
                    "language": repo["language"],
                    "description": repo["description"]
                })
            
            lang = repo["language"]
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "name": user_data.get("name") or username,
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "avatar_url": user_data.get("avatar_url"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "top_repos": top_6_repos,
            "most_used_languages": [l[0] for l in sorted_langs[:5]]
        }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Analyze GitHub data using Gemini to determine developer vibe and theme."""
    if not gemini_client:
        return {
            "developer_vibe": "A passionate developer",
            "top_skills": github_data.get("most_used_languages", ["Code"])[:3],
            "fun_fact": "Loves open source!",
            "card_theme": "builder"
        }

    prompt = f"""
    Analyze this GitHub profile and return a JSON object.
    Profile: {json.dumps(github_data)}

    Return ONLY valid JSON with exactly this structure (no markdown, no code blocks):
    {{
        "developer_vibe": "one sentence personality description",
        "top_skills": ["skill1", "skill2", "skill3"],
        "fun_fact": "something clever inferred from repos",
        "card_theme": "hacker"
    }}
    card_theme must be one of: hacker, builder, researcher, designer, open-source-hero
    """
    
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    
    text = response.text.strip()
    # Strip markdown code blocks if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    return json.loads(text)

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a self-contained HTML card."""
    theme_colors = {
        "hacker": {"bg": "#0f0f0f", "text": "#00ff00", "accent": "#008f11"},
        "builder": {"bg": "#f0f2f5", "text": "#1c1e21", "accent": "#007bff"},
        "researcher": {"bg": "#ffffff", "text": "#2c3e50", "accent": "#34495e"},
        "designer": {"bg": "#fff5f5", "text": "#d63384", "accent": "#fd7e14"},
        "open-source-hero": {"bg": "#e3f2fd", "text": "#0d47a1", "accent": "#1976d2"}
    }
    
    theme = theme_colors.get(analysis["card_theme"], theme_colors["builder"])
    
    repos_html = "".join([
        f'<div style="margin-bottom: 10px; border-left: 3px solid {theme["accent"]}; padding-left: 10px;">'
        f'<strong>{r["name"]}</strong> ⭐ {r["stars"]}<br><small>{r["description"] or ""}</small></div>'
        for r in github_data["top_repos"][:3]
    ])
    
    skills_html = "".join([
        f'<span style="background: {theme["accent"]}; color: white; padding: 2px 8px; border-radius: 12px; margin-right: 5px; font-size: 0.8em;">{s}</span>'
        for s in analysis["top_skills"]
    ])

    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 400px; padding: 20px; border-radius: 15px; background: {theme["bg"]}; color: {theme["text"]}; border: 1px solid #ccc; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <img src="{github_data['avatar_url']}" style="width: 80px; height: 80px; border-radius: 50%; margin-right: 20px; border: 3px solid {theme["accent"]};">
            <div>
                <h2 style="margin: 0;">{github_data['name']}</h2>
                <p style="margin: 5px 0; font-style: italic;">{analysis['developer_vibe']}</p>
            </div>
        </div>
        <div style="margin-bottom: 15px;">{skills_html}</div>
        <div style="display: flex; gap: 20px; margin-bottom: 20px; font-size: 0.9em;">
            <span><strong>{github_data['public_repos']}</strong> Repos</span>
            <span><strong>{github_data['followers']}</strong> Followers</span>
        </div>
        <div style="margin-bottom: 20px;">
            <h4 style="border-bottom: 1px solid {theme['accent']}; padding-bottom: 5px;">Top Projects</h4>
            {repos_html}
        </div>
        <p style="font-size: 0.8em; opacity: 0.8; margin-top: 20px;">💡 {analysis['fun_fact']}</p>
    </div>
    """
    return html

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save the HTML card to the static directory."""
    static_path = Path("static/cards")
    static_path.mkdir(parents=True, exist_ok=True)
    
    file_path = static_path / f"{username}.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    mcp.run()

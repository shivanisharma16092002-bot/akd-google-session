import os
import json
import httpx
from pathlib import Path

# ── Gemini setup ─────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

gemini_client = None
if GOOGLE_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"[WARN] Could not init Gemini client: {e}")

# ── GitHub scraper ────────────────────────────────────────────────────────────
async def scrape_github(username: str) -> dict:
    """Fetch GitHub profile stats and top repos."""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=20) as client:
        user_res = await client.get(
            f"https://api.github.com/users/{username}", headers=headers
        )
        user_res.raise_for_status()
        user = user_res.json()

        repos_res = await client.get(
            f"https://api.github.com/users/{username}/repos?sort=stars&per_page=30",
            headers=headers,
        )
        repos_res.raise_for_status()
        repos = repos_res.json()

    top_repos, languages = [], {}
    for repo in repos:
        if len(top_repos) < 6:
            top_repos.append({
                "name":        repo["name"],
                "stars":       repo["stargazers_count"],
                "language":    repo["language"],
                "description": repo["description"],
            })
        lang = repo["language"]
        if lang:
            languages[lang] = languages.get(lang, 0) + 1

    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)

    return {
        "name":                user.get("name") or username,
        "bio":                 user.get("bio"),
        "location":            user.get("location"),
        "avatar_url":          user.get("avatar_url"),
        "public_repos":        user.get("public_repos"),
        "followers":           user.get("followers"),
        "top_repos":           top_repos,
        "most_used_languages": [l[0] for l in sorted_langs[:5]],
    }

# ── Gemini profile analyser ───────────────────────────────────────────────────
async def analyze_profile(github_data: dict) -> dict:
    """Use Gemini to infer developer vibe, skills, fun fact, and card theme."""
    fallback = {
        "developer_vibe": "A passionate developer who ships code",
        "top_skills":     (github_data.get("most_used_languages") or ["Code"])[:3],
        "fun_fact":       "Loves open source and building cool stuff!",
        "card_theme":     "builder",
    }

    if not gemini_client:
        return fallback

    prompt = f"""Analyze this GitHub profile and return ONLY a valid JSON object (no markdown, no code fences).

Profile data:
{json.dumps(github_data, indent=2)}

Return exactly this JSON structure:
{{
  "developer_vibe": "one sentence personality description",
  "top_skills": ["skill1", "skill2", "skill3"],
  "fun_fact": "something clever inferred from the repos",
  "card_theme": "builder"
}}

Rules:
- card_theme must be one of: hacker, builder, researcher, designer, open-source-hero
- top_skills should reflect languages and project types, not just language names
- Return ONLY the JSON object, nothing else
"""
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        # Strip markdown code blocks if present
        if "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        return json.loads(text)
    except Exception as e:
        print(f"[WARN] Gemini analysis failed: {e}")
        return fallback

# ── Card HTML generator ───────────────────────────────────────────────────────
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a self-contained HTML dev card."""
    themes = {
        "hacker":           {"bg": "#0f0f0f", "text": "#00ff00", "accent": "#008f11"},
        "builder":          {"bg": "#0d1117", "text": "#f0f6fc", "accent": "#238636"},
        "researcher":       {"bg": "#1a1a2e", "text": "#e0e0e0", "accent": "#7c4dff"},
        "designer":         {"bg": "#1a0a2e", "text": "#f8bbd9", "accent": "#e91e8c"},
        "open-source-hero": {"bg": "#0a1628", "text": "#90caf9", "accent": "#1976d2"},
    }
    t = themes.get(analysis.get("card_theme", "builder"), themes["builder"])

    repos_html = "".join([
        f'<div style="margin-bottom:10px;border-left:3px solid {t["accent"]};padding-left:10px;">'
        f'<strong>{r["name"]}</strong> ⭐ {r["stars"]}<br>'
        f'<small style="opacity:0.7">{r["description"] or ""}</small></div>'
        for r in github_data.get("top_repos", [])[:3]
    ])

    skills_html = "".join([
        f'<span style="background:{t["accent"]};color:#fff;padding:3px 10px;'
        f'border-radius:12px;margin:3px;font-size:0.78em;display:inline-block">{s}</span>'
        for s in analysis.get("top_skills", [])
    ])

    avatar = github_data.get("avatar_url", "")
    name   = github_data.get("name", username)
    vibe   = analysis.get("developer_vibe", "")
    repos  = github_data.get("public_repos", 0)
    followers = github_data.get("followers", 0)
    fun_fact  = analysis.get("fun_fact", "")

    return f"""
<div style="font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
            max-width:420px;padding:24px;border-radius:16px;
            background:{t['bg']};color:{t['text']};
            border:1px solid {t['accent']}33;
            box-shadow:0 8px 32px rgba(0,0,0,0.4);">
  <div style="display:flex;align-items:center;margin-bottom:20px;">
    <img src="{avatar}" style="width:80px;height:80px;border-radius:50%;
         margin-right:18px;border:3px solid {t['accent']};" alt="{name}">
    <div>
      <h2 style="margin:0;font-size:1.3em">{name}</h2>
      <p style="margin:5px 0 0;font-size:0.85em;opacity:0.75;font-style:italic">{vibe}</p>
    </div>
  </div>
  <div style="margin-bottom:16px;display:flex;flex-wrap:wrap;gap:4px">{skills_html}</div>
  <div style="display:flex;gap:24px;margin-bottom:20px;font-size:0.9em;">
    <span>📦 <strong>{repos}</strong> Repos</span>
    <span>👥 <strong>{followers}</strong> Followers</span>
  </div>
  <div style="margin-bottom:16px;">
    <h4 style="border-bottom:1px solid {t['accent']}55;padding-bottom:6px;margin-bottom:10px;">
      🚀 Top Projects
    </h4>
    {repos_html}
  </div>
  <p style="font-size:0.78em;opacity:0.65;margin-top:16px;border-top:1px solid {t['accent']}33;padding-top:12px;">
    💡 {fun_fact}
  </p>
</div>
"""

# ── Card file saver ───────────────────────────────────────────────────────────
async def save_card(username: str, html: str) -> str:
    """Save HTML card to the static directory and return its URL path."""
    path = Path("static/cards")
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{username}.html"
    file_path.write_text(html, encoding="utf-8")
    return f"/static/cards/{username}.html"

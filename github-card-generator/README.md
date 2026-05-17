# 🌟 GitHub Dev Card Generator

An elegant, premium, single-container web application that scrapes public GitHub statistics and uses **Google Gemini AI** to analyze a developer's profile, determine their developer vibe, identify top skills, and render a beautifully customized developer card!

---

## ✨ Features

- **Profile Scraper:** Fetches real-time profile statistics and top repositories directly from the public GitHub API.
- **Gemini AI Analysis:** Utilizes the cutting-edge `google-genai` SDK and the `gemini-2.5-flash` (or `gemini-2.0-flash`) model to analyze repository content and language distributions to generate a smart developer vibe, fun facts, and custom skill badges.
- **Adaptive Card Themes:** Dynamic visual styles (`hacker`, `builder`, `researcher`, `designer`, and `open-source-hero`) selected by AI and matched to the developer's personality.
- **Seamless Sharing:** Generates self-contained static HTML pages of the cards and provides one-click URL sharing.
- **Single-Container Architecture:** FastAPI serves both the REST API and the frontend (`index.html`) under one single port, making cloud deployments extremely easy.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python, `google-genai` SDK, Uvicorn, HTTPX
- **Frontend:** React, HTML5, Vanilla CSS (Premium Glassmorphic/Dark Theme)
- **Deployment:** Google Cloud Run, Cloud Shell, Docker

---

## ⚙️ Configuration & Secrets

Before running the project, create a `.env` file in the `github-card-generator` directory using the `.env.example` template:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_personal_access_token_here (optional, to avoid API rate limits)
GEMINI_MODEL=gemini-2.0-flash
```

---

## 🚀 Quick Start (Local Run)

Follow these steps to run the application on your local machine:

### 1. Set Up Virtual Environment

Navigate to the `backend` directory and activate the Python virtual environment:

```powershell
# Navigate to backend
cd backend

# Create virtual environment (if not already done)
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate
```

### 2. Install Dependencies

Install the required packages using `pip`:

```bash
pip install -r requirements.txt
```

### 3. Run the Development Server

Start the FastAPI application. The server dynamically checks the environment and binds to your configured port (defaults to `8080`, or uses `8000` to avoid conflicts on Windows systems running services like Oracle DB):

```bash
python main.py
```

Open `http://localhost:8000` (or `8080`) in your browser to view the application!

---

## ☁️ Google Cloud Run Deployment

This project is fully containerized and optimized to run on **Google Cloud Run**.

### 1. Prepare Frontend Build
The deployment scripts bundle the frontend `index.html` file into the backend's server directory so they are packaged together.

### 2. Deploy via Cloud Shell
Open the Google Cloud Console for your project and launch the Cloud Shell. Paste the following commands:

```bash
# Clone the repository
git clone https://github.com/shivanisharma16092002-bot/akd-google-session.git
cd akd-google-session/github-card-generator/backend

# Deploy directly to Cloud Run
gcloud run deploy github-card-generator \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=YOUR_GEMINI_KEY,GITHUB_TOKEN=YOUR_GITHUB_TOKEN,GEMINI_MODEL=gemini-2.0-flash" \
  --project cardgenerator-496610
```

---

## 📄 License

This project is licensed under the MIT License.

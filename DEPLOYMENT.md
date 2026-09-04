# 🚀 Deployment Guide — Hyperlocal Weather Downscaling & Agro-Advisory

This project consists of:
1. **Frontend UI**: Streamlit Dashboard (dashboard/app.py + 6 subpages) with live animated wallpaper themes (Rain, Day, Thunder).
2. **Backend API**: FastAPI Service (src/main.py) powering downscaling & advisories.
3. **Data Layer**: Bundled offline snapshots (demo_phanda.json, demo_berasia.json) + Open-Meteo live sync.

---

## 🌟 Option 1: Streamlit Community Cloud (Recommended — 100% Free & Fastest)

Streamlit Community Cloud is the best option for hosting the interactive dashboard with a public HTTPS link in 2 minutes.

### Step-by-Step:
1. **Push your code to your GitHub account**:
   `ash
   git add .
   git commit -m Complete SIH Hyperlocal Weather Forecast & Live Themes
   # If creating a new repository on your GitHub (e.g. tanmay6269):
   git remote set-url origin https://github.com/YOUR_USERNAME/weatherforcastds.git
   git branch -M main
   git push -u origin main
   `
2. **Sign in to Streamlit Cloud**:
   - Go to https://share.streamlit.io and click **Continue with GitHub**.
3. **Deploy the App**:
   - Click **New app**.
   - **Repository**: YOUR_USERNAME/weatherforcastds
   - **Branch**: main
   - **Main file path**: dashboard/app.py
4. **Environment Variables (Optional)**:
   - Click **Advanced Settings** -> **Secrets**.
   - Add your Gemini API Key if you want AI-generated advisories:
     `	oml
     GEMINI_API_KEY = your_api_key_here
     `
5. Click **Deploy!**.
   - Streamlit will install dependencies from equirements.txt and launch your app with a public URL like:
     https://weatherforcastds-YOUR_NAME.streamlit.app

---

## ⚡ Option 2: Render.com (Deploys Dashboard + FastAPI Backend)

Render supports multi-service deployments using the included ender.yaml blueprint.

### Step-by-Step:
1. Push your repository to GitHub.
2. Go to https://render.com and log in with GitHub.
3. Click **New +** -> **Blueprint**.
4. Connect your GitHub repository.
5. Render reads ender.yaml and deploys:
   - **weather-dashboard**: Web service running ash render_start.sh (Port $PORT).
   - **weather-api**: FastAPI service running uvicorn src.main:app (Port $PORT).
6. Both services will be provisioned with free SSL and public .onrender.com domains!

---

## 🐳 Option 3: Docker & Docker Compose (Self-Hosted / VPS / Local)

Deploy using Docker on any cloud server (AWS EC2, DigitalOcean, Azure, or local machine):

`ash
# Build and run both backend and dashboard in detached mode
docker compose up -d --build
`

- **Dashboard**: http://localhost:8501
- **FastAPI Backend & Swagger Docs**: http://localhost:8000/docs

To stop:
`ash
docker compose down
`

---

## 💻 Option 4: Local Demo Run

For local presentations, offline evaluations, or SIH judging:

`powershell
# In PowerShell:
python -m streamlit run dashboard/app.py
`
Or double-click:
`powershell
.\start_demo.bat
`

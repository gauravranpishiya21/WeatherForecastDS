# 🌦️ Hyperlocal Weather Downscaling & Agro-Advisory System

**Smart India Hackathon 2026 — Problem ID: SIH26074**

> Downscale block-level weather forecasts to panchayat/farm-level resolution and generate crop-specific agricultural advisories for Indian farmers.

---

## 🎯 Problem Statement

Current weather forecasts are available at Block level (~25 km resolution). Farmers need **hyperlocal, farm-level intelligence** to make decisions about irrigation, sowing, harvesting, and pest management. This system:

1. **Downscales** coarse NWP model outputs to ~1 km resolution using ML
2. **Generates** crop-specific, actionable agro-advisories
3. **Delivers** multilingual alerts via web dashboard, API, and SMS

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA INGESTION LAYER                        │
│  Open-Meteo API │ IMD Forecasts │ SRTM DEM │ Satellite Data    │
└────────┬────────────────┬───────────────┬───────────────────────┘
         │                │               │
         ▼                ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOWNSCALING ENGINE                            │
│  Feature Engineering → Statistical Baseline → ML Residual       │
│  (Elevation, Lat/Lon)  (Interpolation+Lapse)  (RF/XGBoost)     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ADVISORY ENGINE                               │
│  Crop Knowledge Base → Risk Assessment → LLM Advisory Generator │
│  (12 Indian crops)     (6 risk types)    (Gemini API)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DELIVERY LAYER                                │
│  Streamlit Dashboard │ FastAPI REST API │ SMS/WhatsApp Alerts   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd WeatherForecastDS

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment config
copy .env.example .env
# Edit .env to add your GEMINI_API_KEY (optional)
```

### Train the Downscaling Model

```bash
python -m src.downscaling.train
```

### Run the API Server

```bash
python -m src.main
# or
uvicorn src.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Dashboard available at: http://localhost:8501

### Docker

```bash
docker-compose up --build
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/forecast?lat=X&lon=Y&days=7` | Downscaled 7-day forecast |
| POST | `/api/advisory` | Crop-specific advisory |
| GET | `/api/locations/search?q=query` | Search locations |
| GET | `/api/locations/reverse?lat=X&lon=Y` | Reverse geocode |
| GET | `/api/crops` | List available crops |
| GET | `/api/panchayats?block_id=phanda` | Block overview: all panchayats with downscaled weather + risk (Phanda 28, Berasia 14) |
| GET | `/api/panchayats/blocks` | List available demo blocks |
| GET | `/api/panchayats/{village_id}?block_id=phanda` | 7-day downscaled forecast + risks for one panchayat |
| GET | `/api/search/villages?q=name` | Search MP villages (dataset + live geocoding) |
| GET | `/api/languages` | List supported advisory languages |

## 🌾 Supported Crops

Rice, Wheat, Maize, Cotton, Sugarcane, Soybean, Mustard, Chickpea, Groundnut, Tomato, Potato, Onion

## 🧠 Downscaling Approach

1. **Statistical Baseline**: Bilinear interpolation + elevation lapse rate correction (-6.5°C/km)
2. **ML Residual Learning**: Random Forest/XGBoost trained to predict the residual between interpolated and actual values
3. **Feature Set**: Latitude, longitude, elevation, slope, aspect, distance-to-coast, season, coarse forecast values

## 🛡️ Risk Assessment

The system monitors 6 weather risk categories:
- 🔥 **Heat Stress** (temp > 40°C)
- 🥶 **Cold/Frost** (temp < 5°C)
- 🌊 **Waterlogging** (rainfall > 50mm/day)
- 🏜️ **Drought** (no rain 7+ days)
- 💨 **Strong Wind** (> 40 km/h)
- 🦠 **Disease Risk** (humidity > 85% for 3+ days)

## 📂 Project Structure

```
WeatherForecastDS/
├── src/
│   ├── main.py                    # FastAPI entry point
│   ├── data/                      # Data ingestion layer
│   │   ├── weather_api.py         # Open-Meteo client
│   │   ├── terrain.py             # Elevation & terrain features
│   │   ├── geocoding.py           # Location resolution
│   │   ├── panchayats.py          # Multi-block village datasets
│   │   └── blocks/*.json          # Phanda (28) + Berasia (14) village lists
│   ├── downscaling/               # ML downscaling engine
│   │   ├── features.py            # Feature engineering
│   │   ├── interpolation.py       # Statistical baseline
│   │   ├── ml_model.py            # RF/XGBoost model
│   │   └── train.py               # Training script
│   ├── advisory/                  # Agro-advisory engine
│   │   ├── crop_rules.py          # Rule-based advisor
│   │   ├── risk_assessment.py     # Risk scoring
│   │   ├── llm_advisory.py        # Gemini-powered NL generation
│   │   ├── sms_gateway.py         # SMS alert delivery (dry-run default)
│   │   └── crop_data/crops.json   # Crop knowledge base
│   ├── api/routes/                # REST API endpoints
│   └── utils/                     # Config & translation
├── dashboard/                     # Streamlit web app
│   ├── app.py
│   ├── pages/                     # Multi-page dashboard
│   └── components/                # Reusable UI components
├── scripts/                       # Demo + data tooling
│   ├── make_demo_snapshot.py      # Offline snapshot builder (per block)
│   ├── make_real_training_data.py # ERA5 reanalysis training-set builder
│   └── geocode_villages.py        # Gazetteer coordinate updater
├── models/                        # Saved ML models (XGBoost, real-data trained)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🔑 Data Sources

| Source | Data | Cost |
|--------|------|------|
| [Open-Meteo](https://open-meteo.com/) | Global NWP forecasts + elevation | Free |
| [IMD API](https://api.imd.gov.in/) | India weather forecasts | Free |
| [OSM Nominatim](https://nominatim.openstreetmap.org/) | Geocoding | Free |

## 🏆 SIH Judging Criteria

- **Innovation**: Hybrid ML downscaling + LLM-powered advisories
- **Technical Complexity**: Multi-source data fusion, geospatial ML
- **Feasibility**: Uses only free/open data sources
- **Impact**: Farm-level intelligence for 10M+ smallholder farmers
- **User Experience**: Multilingual, mobile-friendly, visual risk indicators

## 📄 License

Built for Smart India Hackathon 2026. MIT License.

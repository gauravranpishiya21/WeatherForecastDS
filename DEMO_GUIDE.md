# 🎤 SIH 2026 — Live Demo Script (5 minutes)

**Problem Statement 74:** Hyperlocal Weather Intelligence — downscaling
block-level weather forecasts to the Panchayat level for smarter
agro-meteorological advisories.

> Safety rule for stage: every page has a **📦 Demo snapshot (offline)** mode.
> If stage WiFi dies, switch to it — the demo continues with bundled real data.

---

## 0:00–0:30 — The Problem (main page)
- "IMD/Open-Meteo forecasts come at **Block level, ~25 km resolution**."
- "A farmer in Samasgarh (575 m) and one in Parwaliya (515 m) get the **same**
  forecast — but their weather is different. Wrong forecast → wrong irrigation
  → crop loss."
- "We downscale to **~1 km, panchayat level**, and generate advisories per village."

## 0:30–2:00 — The Map (Block page)
- Open **Block** → "Phanda Block, Bhopal (MP): **28 panchayats**, one map —
  switch to **Berasia** for 14 more. 42 villages, same pipeline: scale proven."
- Point at markers: "Color = risk level. Click any village — temperature,
  rainfall, humidity, elevation, all hyperlocal." Toggle **Google Maps /
  OpenStreetMap** at the top to show the Google Maps integration.
- Compare two villages: "Samasgarh on the higher plateau edge vs Parwaliya on the
  lower plain — different temperature, different rain. That difference IS our product."
- Scroll the table: "Every panchayat, today's downscaled weather, sortable."

## 2:00–2:30 — Search any village (Forecast page)
- "Any village in MP — type the name, pick the match, graphs retarget to it."
- Point at the **Rainfall Focus** row: "7-day total, rainy days, heaviest day —
  and the irrigation verdict. THIS is what optimizes the advisory."
- Click **"Optimize advisory for this village"** → lands on the Advisory page
  with that village loaded.

## 2:30–3:30 — The Advisory (Advisory page)
- Pick a panchayat + crop (e.g. Wheat) → "Growth-stage aware:
  the same weather means different advice for germination vs maturity."
- Read one risk + one action aloud. Show the **weekly action plan**.
- Show the **SMS preview**: "This is what the farmer actually receives —
  under 160 characters, in Hindi."

## 3:30–4:30 — The Tech (Comparison page + /docs)
- Comparison page: "Coarse vs downscaled curves — the gap between them is the
  elevation lapse-rate + ML residual correction."
- Quote model metrics: "Temperature R² 0.63, RMSE 0.89 °C — trained on 17,544
  REAL ERA5 observations (2023–24, 24 MP stations, 215–1054 m), not toy data."
- Optional: open `http://localhost:8000/docs` — "Clean REST API:
  `/api/panchayats` serves the whole block in 2 upstream calls."

## 4:30–5:00 — Close (+ Kisan page kicker)
- Open the **Kisan page**: "And THIS is what the farmer sees — Hindi-first,
  big text, traffic-light risk, max 3 actions, SMS box. No graphs, no jargon."
- "Only free data sources: Open-Meteo, SRTM elevation, OSM geocoding."
- "Scales to every block in India — same pipeline, new coordinates."
- "Theme fit — MoES Disaster Management: lead with heatwave, hailstorm and
  waterlogging alerts; advisories ride on top."
- "SMS gateway module is integration-ready (dry-run in demo; add provider
  credentials to send live)."
- "Impact: panchayat-level intelligence for smallholder farmers, in their language."

---

### If something breaks on stage
| Failure | Recovery (10 seconds) |
|---|---|
| No internet | Switch every page to **📦 Demo snapshot** |
| API terminal died | Demo snapshot mode needs no server at all |
| Streamlit error | `CTRL+C`, `python -m streamlit run dashboard/app.py`, refresh browser |

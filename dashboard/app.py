"""Hyperlocal Weather Intelligence — SIH 2026 Problem Statement 74.

Block-level weather forecasts downscaled to Panchayat level
for smarter agro-meteorological advisories.
"""

import streamlit as st
import httpx

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="SIH74 — Hyperlocal Weather Intelligence",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌤️ Hyperlocal Weather Intelligence")
st.subheader("SIH 2026 • Problem Statement 74 — Block-level forecasts → Panchayat-level agro-advisories")

with st.expander("📜 Problem Statement", expanded=False):
    st.markdown("""
**Problem:** Weather forecasts are issued at Block level (~25 km resolution) — too coarse
for farm decisions on irrigation, sowing, spraying and harvest.

**Our solution:**
1. **Downscale** coarse NWP forecasts to ~1 km (panchayat) using elevation lapse rates + ML residuals
2. **Assess risk** per panchayat (heat, frost, waterlogging, drought, wind, disease)
3. **Advise** farmers with crop- and stage-specific alerts in their own language (10 languages, SMS-ready)

**Live demo area:** Phanda Block, Bhopal (Madhya Pradesh) — 28 panchayat villages. Open the **Block** page.
    """)

# API status indicator
try:
    resp = httpx.get(f"{API_BASE}/", timeout=4)
    if resp.status_code == 200:
        st.success("🔴 Live API connected (port 8000). Prefer offline safety? Use 📦 Demo snapshot mode on each page.")
except Exception:
    st.warning("📦 API not detected — every page has a 📦 Demo snapshot (offline) mode that works without the server.")


# --- Sidebar: Location & Crop Settings ---
with st.sidebar:
    st.header("📍 Location Settings")

    search_query = st.text_input("Search location", placeholder="e.g., Bhopal, MP")
    if search_query and len(search_query) >= 3:
        try:
            resp = httpx.get(f"{API_BASE}/api/locations/search", params={"q": search_query}, timeout=10)
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    options = [f"{r.get('panchayat', '')} {r.get('district', '')} ({r['lat']:.2f}, {r['lon']:.2f})" for r in results]
                    selected = st.selectbox("Select location", options, key="loc_select")
                    idx = options.index(selected)
                    st.session_state["lat"] = results[idx]["lat"]
                    st.session_state["lon"] = results[idx]["lon"]
        except Exception:
            st.warning("Location search needs the API server.")

    lat = st.number_input("Latitude", value=st.session_state.get("lat", 23.275), format="%.4f", step=0.01)
    lon = st.number_input("Longitude", value=st.session_state.get("lon", 77.335), format="%.4f", step=0.01)

    st.divider()
    st.header("🌾 Crop Settings")

    crops_list = ["Soybean", "Wheat", "Chickpea", "Mustard", "Maize", "Cotton",
                  "Sugarcane", "Tomato", "Potato", "Onion", "Groundnut", "Rice"]
    try:
        resp = httpx.get(f"{API_BASE}/api/crops", timeout=5)
        if resp.status_code == 200:
            api_crops = resp.json()
            if api_crops:
                crops_list = [c["name"] for c in api_crops]
    except Exception:
        pass

    crop = st.selectbox("Select Crop", crops_list)
    sowing_date = st.date_input("Sowing Date")

    st.divider()
    language = st.selectbox(
        "🗣️ Advisory Language",
        ["English", "Hindi", "Tamil", "Telugu", "Marathi", "Kannada",
         "Bengali", "Gujarati", "Malayalam", "Punjabi"],
    )
    lang_code = {
        "English": "en", "Hindi": "hi", "Tamil": "ta", "Telugu": "te",
        "Marathi": "mr", "Kannada": "kn", "Bengali": "bn", "Gujarati": "gu",
        "Malayalam": "ml", "Punjabi": "pa",
    }[language]

    st.session_state["lat"] = lat
    st.session_state["lon"] = lon
    st.session_state["crop"] = crop
    st.session_state["sowing_date"] = str(sowing_date)
    st.session_state["language"] = lang_code

st.info("👈 Set location + crop in the sidebar, then open the **Block** page: 28 panchayats of Phanda Block (Bhopal, MP) on one map.")

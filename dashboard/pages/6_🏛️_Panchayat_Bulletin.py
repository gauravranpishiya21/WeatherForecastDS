"""Gram Panchayat Agro-Weather Bulletin & Official Notice Generator."""

import json
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
DATA_DIR = ROOT / "src" / "data"

from dashboard.components.theme import inject_weather_theme, render_voice_button, navigate_if_needed
from src.advisory.crop_rules import CropAdvisoryEngine
from src.advisory.risk_assessment import WeatherRiskAssessor

st.set_page_config(page_title="Panchayat Bulletin", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")
inject_weather_theme(hide_sidebar=True)
navigate_if_needed("Panchayat Bulletin")

st.title("🏛️ Gram Panchayat Agro-Weather Bulletin")
st.caption("SIH 2026 • Problem 74 — Official Panchayat Village Notice & Farmer Advisory System")

BLOCKS = {"Phanda": "phanda", "Berasia": "berasia"}
col_b1, col_b2 = st.columns([1, 2])
with col_b1:
    block_name = st.selectbox("Block / विकासखण्ड", list(BLOCKS.keys()))
bid = BLOCKS[block_name]

snap_file = DATA_DIR / f"demo_{bid}.json"
if not snap_file.exists():
    st.error(f"Data file not found: {snap_file}")
    st.stop()

snap = json.loads(snap_file.read_text(encoding="utf-8"))
villages = snap["villages"]

with col_b2:
    v_options = [f"{v['name']} ({v['hindi_name']})" for v in villages]
    sel_idx = st.selectbox("Gram Panchayat / ग्राम पंचायत", range(len(v_options)), format_func=lambda i: v_options[i])
v = villages[sel_idx]

tab_bulletin, tab_micro, tab_broadcast = st.tabs([
    "📋 Official Notice (सूचना पत्र)",
    "⛰️ Micro-Elevation Simulator (सूक्ष्म जलवायु)",
    "📲 WhatsApp/SMS Broadcast (प्रसारण)",
])

with tab_bulletin:
    bulletin_lang = st.radio("Language", ["हिन्दी (Hindi)", "English"], horizontal=True)
    is_hindi = "हिन्दी" in bulletin_lang
    today_dt = datetime.now().strftime("%d %B %Y")

    daily = v["daily"]
    t0 = daily[0]
    total_rain_wk = sum(d["rainfall_mm"] for d in daily[:7])

    assessor = WeatherRiskAssessor()
    risks = assessor.assess_risks([{
        "temperature": d["temp_max"], "rainfall": d["rainfall_mm"],
        "humidity": d["humidity"], "wind_speed": d["wind_kmh"],
    } for d in daily[:7]])
    score = assessor.aggregate_risk_score(risks)

    if is_hindi:
        voice_text = (
            f"ग्राम पंचायत {v['hindi_name']}, विकासखंड {block_name} के किसान भाइयों के लिए आज का मौसम संदेश। "
            f"आज का अधिकतम तापमान {t0['temp_max']} डिग्री सेल्सियस और वर्षा {t0['rainfall_mm']} मिलीमीटर रहने का अनुमान है। "
            f"सप्ताह भर में कुल वर्षा लगभग {total_rain_wk:.1f} मिलीमीटर संभावित है।"
        )
    else:
        voice_text = (
            f"Gram Panchayat {v['name']}, Block {block_name} Agro-Weather Advisory. "
            f"Today's maximum temperature is {t0['temp_max']}°C with {t0['rainfall_mm']}mm rainfall. "
            f"Total weekly rainfall forecast is {total_rain_wk:.1f}mm."
        )

    st.markdown("### 🎙️ किसान वाणी (Voice Advisory)")
    render_voice_button(voice_text)

    header_title = f"कार्यालय ग्राम पंचायत — {v['hindi_name']}" if is_hindi else f"GRAM PANCHAYAT — {v['name'].upper()}"
    sub_title = (f"विकासखण्ड: {block_name}, जिला: भोपाल (म.प्र.) | साप्ताहिक कृषि मौसम बुलेटिन"
                 if is_hindi else f"Block: {block_name}, District: Bhopal (M.P.) | Weekly Agro-Meteorological Advisory")
    risk_color = '#34d399' if score < 30 else '#fbbf24' if score < 60 else '#f87171'
    risk_text = ('🟢 सामान्य' if score < 30 else '🟡 मध्यम' if score < 60 else '🔴 उच्च सतर्कता') if is_hindi else ('🟢 Normal' if score < 30 else '🟡 Moderate' if score < 60 else '🔴 Alert')

    bulletin_html = f"""
    <div style="background: rgba(15, 23, 42, 0.9); border: 2px solid #38bdf8; border-radius: 16px; padding: 25px; margin: 20px 0; color: #f8fafc; font-family: sans-serif; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        <div style="text-align: center; border-bottom: 2px dashed rgba(56, 189, 248, 0.4); padding-bottom: 14px; margin-bottom: 18px;">
            <div style="font-size: 22px; font-weight: 800; color: #38bdf8;">{header_title}</div>
            <div style="font-size: 14px; color: #cbd5e1; margin-top: 4px;">{sub_title}</div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 12px; color: #94a3b8;">
                <span><b>{'क्रमांक' if is_hindi else 'Ref'}:</b> GP/{bid[:3].upper()}/{v['id']}/2026/09</span>
                <span><b>{'दिनांक' if is_hindi else 'Date'}:</b> {today_dt}</span>
                <span><b>{'ऊंचाई' if is_hindi else 'Elev'}:</b> {v['elevation_m']}m</span>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
            <div style="background: rgba(30, 41, 59, 0.7); padding: 12px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.08);">
                <div style="font-size: 12px; color: #94a3b8;">{'आज का तापमान' if is_hindi else 'Today Temp'}</div>
                <div style="font-size: 18px; font-weight: 700; color: #f8fafc; margin-top: 4px;">{t0['temp_max']}°C / {t0['temp_min']}°C</div>
            </div>
            <div style="background: rgba(30, 41, 59, 0.7); padding: 12px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.08);">
                <div style="font-size: 12px; color: #94a3b8;">{'आज वर्षा' if is_hindi else 'Today Rain'}</div>
                <div style="font-size: 18px; font-weight: 700; color: #38bdf8; margin-top: 4px;">{t0['rainfall_mm']} mm</div>
            </div>
            <div style="background: rgba(30, 41, 59, 0.7); padding: 12px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.08);">
                <div style="font-size: 12px; color: #94a3b8;">{'साप्ताहिक वर्षा' if is_hindi else '7-Day Rain'}</div>
                <div style="font-size: 18px; font-weight: 700; color: #a78bfa; margin-top: 4px;">{total_rain_wk:.1f} mm</div>
            </div>
            <div style="background: rgba(30, 41, 59, 0.7); padding: 12px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.08);">
                <div style="font-size: 12px; color: #94a3b8;">{'जोखिम स्तर' if is_hindi else 'Risk Level'}</div>
                <div style="font-size: 18px; font-weight: 700; color: {risk_color}; margin-top: 4px;">{risk_text}</div>
            </div>
        </div>
        <div style="background: rgba(30, 41, 59, 0.5); padding: 16px; border-radius: 12px; margin-bottom: 16px; border-left: 4px solid #38bdf8;">
            <div style="font-weight: 700; font-size: 15px; color: #38bdf8; margin-bottom: 8px;">
                🌾 {'प्रमुख फसलों हेतु कार्ययोजना' if is_hindi else 'Crop Action Recommendations'}
            </div>
            <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6; color: #e2e8f0;">
                <li><b>{'सोयाबीन / दलहन' if is_hindi else 'Soybean & Pulses'}:</b> {'खेत में जलभराव न होने दें; मेड़ों की जल निकासी खुली रखें।' if is_hindi else 'Ensure proper field drainage; clear bund outlets.'}</li>
                <li><b>{'सिंचाई सलाह' if is_hindi else 'Irrigation Plan'}:</b> {f'{total_rain_wk:.1f}mm वर्षा अपेक्षित। अनावश्यक सिंचाई स्थगित रखें।' if total_rain_wk > 15 else 'वर्षा कम। आवश्यकतानुसार शाम को हल्की सिंचाई करें।'}</li>
                <li><b>{'कीट नियंत्रण' if is_hindi else 'Pest Control'}:</b> {'हवा 15 km/h से अधिक हो तो छिड़काव न करें।' if is_hindi else 'Avoid spraying if wind exceeds 15 km/h.'}</li>
            </ul>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 25px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 13px; color: #94a3b8;">
            <div><b>{'प्रसार माध्यम' if is_hindi else 'Issued via'}:</b> {'पंचायत सूचना पटल / व्हाट्सएप' if is_hindi else 'Notice Board & WhatsApp'}</div>
            <div style="text-align: right;"><div style="color: #f8fafc; font-weight: 700;">{'सचिव / कृषि मित्र' if is_hindi else 'Sachiv / Agri Mitra'}</div></div>
        </div>
    </div>
    """
    st.markdown(bulletin_html, unsafe_allow_html=True)

with tab_micro:
    st.subheader("⛰️ Farm Micro-Climate Simulator")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f"**Panchayat Center:** `{v['elevation_m']}m`")
        farm_offset = st.slider("Farm Elevation Offset (m)", -60, 80, 0, 5)
        aspect = st.selectbox("Slope Aspect", ["Flat", "North (cool)", "South (warm)", "East (morning sun)"])

    LAPSE_RATE = 0.0065
    temp_delta = -1.0 * (farm_offset * LAPSE_RATE)
    if "North" in aspect:
        temp_delta -= 0.8
    elif "South" in aspect:
        temp_delta += 0.8

    farm_max_temp = t0["temp_max"] + temp_delta
    farm_min_temp = t0["temp_min"] + temp_delta

    with col_m2:
        st.markdown("#### 🔬 Farm Micro-Climate")
        mc1, mc2 = st.columns(2)
        with mc1:
            st.metric("Farm Elevation", f"{v['elevation_m'] + farm_offset}m", delta=f"{farm_offset:+d}m")
        with mc2:
            st.metric("Farm Max Temp", f"{farm_max_temp:.1f}°C", delta=f"{temp_delta:+.2f}°C")
        mc3, mc4 = st.columns(2)
        with mc3:
            st.metric("Farm Min Temp", f"{farm_min_temp:.1f}°C")
        with mc4:
            frost_risk = "High" if farm_min_temp < 6.0 else "Moderate" if farm_min_temp < 10.0 else "Low"
            st.metric("Frost Risk", frost_risk)

    if farm_offset < -20:
        st.warning(f"⚠️ **Lowland Alert:** Farm is {abs(farm_offset)}m lower — cold air pooling, frost & waterlogging risk.")
    elif farm_offset > 25:
        st.info(f"💨 **Ridge Alert:** Farm is {farm_offset}m higher — 15-20% more wind, faster soil drying.")

with tab_broadcast:
    st.subheader("📲 WhatsApp & SMS Dispatcher")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        channel = st.selectbox("Channel", ["WhatsApp Group", "Kisan SMS Gateway", "Loudspeaker Notice"])
        pop = v.get("population", 1200)
        target = int(pop * 0.45)
        st.write(f"👥 Target farmers in **{v['name']}**: `{target}`")
        sample_sms = (f"[GP {v['hindi_name']}] आज: {t0['temp_max']}°C, वर्षा {t0['rainfall_mm']}mm। "
                      f"{'सिंचाई न करें।' if t0['rainfall_mm'] > 5 else 'सामान्य कार्य जारी।'}")
        sms_text = st.text_area("Alert Message", sample_sms, height=100)
        if st.button("🚀 Dispatch Alert", key="disp_btn"):
            st.success(f"✅ Queued alert to {target} farmers via {channel}!")
            st.balloons()
    with col_s2:
        st.markdown("#### 📱 Phone Preview")
        st.markdown(f"""
        <div style="background: #075e54; border-radius: 18px; padding: 18px; color: #fff; max-width: 320px; margin: 0 auto; box-shadow: 0 8px 25px rgba(0,0,0,0.5);">
            <div style="font-size: 13px; font-weight: 700; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 8px; margin-bottom: 12px;">🟢 GP Alert System</div>
            <div style="background: #128c7e; padding: 12px; border-radius: 12px; font-size: 13px; line-height: 1.5;">{sms_text}</div>
            <div style="text-align: right; font-size: 10px; color: #dcf8c6; margin-top: 6px;">Just now • Delivered ✓✓</div>
        </div>
        """, unsafe_allow_html=True)

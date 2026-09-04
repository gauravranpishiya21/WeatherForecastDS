"""Ultra-Premium Weather Live Wallpaper UI Engine with 3 Interactive Themes:
1. 🌧️ Rain (Natural slow teardrop raindrops, dark rolling clouds, ground mist)
2. ☀️ Day (Azure sky, right-mid radiant golden Sun, drifting fluffy white cumulus clouds)
3. ⚡ Thunder (Live electric Bijli lightning strikes, sky flashes, storm rain, heavy clouds)

Includes inline Top Option Menu with a compact Theme dropdown at the right corner.
"""

import random

import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu


def inject_weather_theme(hide_sidebar: bool = True):
    """Inject 100% visible 60FPS Live Wallpaper for Day, Rain, or Thunder."""
    mode = st.session_state.get("theme_mode", "rain")

    sidebar_css = """
[data-testid="stSidebar"], section[data-testid="stSidebar"] {
    display: none !important;
}
""" if hide_sidebar else ""

    shared_rain_css = """
.raindrop {
    position: fixed;
    top: -60px;
    width: 2px;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, rgba(186, 230, 253, 0.45) 45%, rgba(255, 255, 255, 0.9) 90%, #ffffff 100%);
    border-radius: 0 0 2px 2px;
    pointer-events: none;
    z-index: 9999;
    box-shadow: 0 0 4px rgba(255, 255, 255, 0.5);
    animation-name: fallDrop;
    animation-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94);
    animation-iteration-count: infinite;
}

@keyframes fallDrop {
    0% {
        transform: translateY(0) rotate(8deg);
        opacity: 0;
    }
    12% {
        opacity: 0.9;
    }
    85% {
        opacity: 0.85;
    }
    100% {
        transform: translateY(calc(100vh + 100px)) rotate(8deg);
        opacity: 0;
    }
}

__DROPS_CSS__
"""

    if mode == "day":
        bg_css = """
.stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 85% 10%, #38bdf8 0%, #0284c7 35%, #0369a1 70%, #075985 100%) !important;
    background-attachment: fixed !important;
}
"""
        elements_html = """
<div class="sun-live"></div>
<div class="sun-glow-ring"></div>
<div class="cloud-drift-1"></div>
<div class="cloud-drift-2"></div>
<div class="cloud-drift-3"></div>
<div class="sun-particles-live"></div>
"""
        anim_css = """
.sun-live {
    position: fixed;
    top: 28%;
    right: 45px;
    width: 120px;
    height: 120px;
    background: radial-gradient(circle, #ffffff 0%, #fef08a 35%, #facc15 70%, #f59e0b 100%);
    border-radius: 50%;
    box-shadow: 0 0 55px #fde047, 0 0 110px #f59e0b, 0 0 180px rgba(251, 191, 36, 0.7);
    pointer-events: none;
    z-index: 9998;
    animation: sunPulse 4s ease-in-out infinite alternate;
}

.sun-glow-ring {
    position: fixed;
    top: calc(28% - 50px);
    right: -10px;
    width: 240px;
    height: 240px;
    background: radial-gradient(circle, rgba(254, 240, 138, 0.35) 0%, rgba(251, 191, 36, 0.15) 50%, transparent 75%);
    border-radius: 50%;
    filter: blur(28px);
    pointer-events: none;
    z-index: 9997;
}

@keyframes sunPulse {
    0% { transform: scale(0.95); box-shadow: 0 0 45px #fde047, 0 0 95px #f59e0b; }
    100% { transform: scale(1.06); box-shadow: 0 0 75px #fef08a, 0 0 135px #f59e0b; }
}

.cloud-drift-1 {
    position: fixed;
    top: 40px;
    left: -450px;
    width: 520px;
    height: 140px;
    background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.75) 0%, rgba(255, 255, 255, 0.4) 50%, transparent 75%);
    filter: blur(14px);
    border-radius: 100px;
    pointer-events: none;
    z-index: 9997;
    animation: cloudMove 42s linear infinite;
}

.cloud-drift-2 {
    position: fixed;
    top: 130px;
    left: -550px;
    width: 620px;
    height: 160px;
    background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.65) 0%, rgba(224, 242, 254, 0.35) 50%, transparent 75%);
    filter: blur(16px);
    border-radius: 120px;
    pointer-events: none;
    z-index: 9997;
    animation: cloudMove 58s linear infinite;
    animation-delay: -18s;
}

.cloud-drift-3 {
    position: fixed;
    top: 250px;
    left: -400px;
    width: 480px;
    height: 120px;
    background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.55) 0%, rgba(224, 242, 254, 0.25) 50%, transparent 75%);
    filter: blur(14px);
    border-radius: 90px;
    pointer-events: none;
    z-index: 9997;
    animation: cloudMove 35s linear infinite;
    animation-delay: -8s;
}

@keyframes cloudMove {
    0% { transform: translateX(-500px); }
    100% { transform: translateX(calc(100vw + 600px)); }
}

.sun-particles-live {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    pointer-events: none;
    z-index: 9997;
    background-image: 
        radial-gradient(2px 2px at 20% 30%, rgba(254, 240, 138, 0.8), transparent),
        radial-gradient(1.5px 1.5px at 45% 55%, rgba(255, 255, 255, 0.7), transparent),
        radial-gradient(2.5px 2.5px at 70% 25%, rgba(253, 224, 71, 0.85), transparent);
    background-size: 400px 400px;
    animation: sunMotes 8s ease-in-out infinite alternate;
}

@keyframes sunMotes {
    0% { transform: translateY(0px); }
    100% { transform: translateY(-20px); }
}
"""

    elif mode == "thunder":
        bg_css = """
.stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 50% 0%, #0a0518 0%, #05020f 30%, #02010a 60%, #000000 100%) !important;
    background-attachment: fixed !important;
}
"""
        elements_html = """
<!-- Electric Bijli Lightning Bolt 1 (main left) -->
<svg class="bijli-bolt bijli-1" viewBox="0 0 200 650" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <filter id="bijliGlow1" x="-80%" y="-80%" width="260%" height="260%">
            <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#ffffff"/>
            <feDropShadow dx="0" dy="0" stdDeviation="18" flood-color="#60a5fa"/>
            <feDropShadow dx="0" dy="0" stdDeviation="40" flood-color="#a855f7"/>
            <feDropShadow dx="0" dy="0" stdDeviation="60" flood-color="#7c3aed"/>
        </filter>
    </defs>
    <polyline points="110,0 90,110 130,110 60,260 100,260 45,400 80,400 30,540 65,540 20,650"
              stroke="#ffffff" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"
              filter="url(#bijliGlow1)"/>
    <polyline points="100,260 145,320 130,380" stroke="#bae6fd" stroke-width="3" fill="none" filter="url(#bijliGlow1)"/>
    <polyline points="65,540 100,590 85,620" stroke="#c4b5fd" stroke-width="2" fill="none" filter="url(#bijliGlow1)"/>
</svg>

<!-- Electric Bijli Lightning Bolt 2 (main right) -->
<svg class="bijli-bolt bijli-2" viewBox="0 0 220 700" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <filter id="bijliGlow2" x="-80%" y="-80%" width="260%" height="260%">
            <feDropShadow dx="0" dy="0" stdDeviation="7" flood-color="#ffffff"/>
            <feDropShadow dx="0" dy="0" stdDeviation="20" flood-color="#38bdf8"/>
            <feDropShadow dx="0" dy="0" stdDeviation="45" flood-color="#c084fc"/>
            <feDropShadow dx="0" dy="0" stdDeviation="65" flood-color="#9333ea"/>
        </filter>
    </defs>
    <polyline points="120,0 95,140 140,140 65,310 110,310 50,470 90,470 35,620 70,620 25,700"
              stroke="#ffffff" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"
              filter="url(#bijliGlow2)"/>
    <polyline points="65,310 25,380 40,430" stroke="#e0f2fe" stroke-width="3" fill="none" filter="url(#bijliGlow2)"/>
    <polyline points="90,470 120,530 108,570" stroke="#ddd6fe" stroke-width="2.2" fill="none" filter="url(#bijliGlow2)"/>
</svg>

<!-- Electric Bijli Lightning Bolt 3 (center fork) -->
<svg class="bijli-bolt bijli-3" viewBox="0 0 160 500" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <filter id="bijliGlow3" x="-80%" y="-80%" width="260%" height="260%">
            <feDropShadow dx="0" dy="0" stdDeviation="5" flood-color="#ffffff"/>
            <feDropShadow dx="0" dy="0" stdDeviation="15" flood-color="#818cf8"/>
            <feDropShadow dx="0" dy="0" stdDeviation="35" flood-color="#a855f7"/>
        </filter>
    </defs>
    <polyline points="80,0 65,90 100,90 45,210 78,210 30,340 60,340 20,430 50,430 10,500"
              stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"
              filter="url(#bijliGlow3)"/>
    <polyline points="45,210 15,265 30,295" stroke="#c7d2fe" stroke-width="2" fill="none" filter="url(#bijliGlow3)"/>
</svg>

<!-- Electric Bijli Lightning Bolt 4 (small far-right) -->
<svg class="bijli-bolt bijli-4" viewBox="0 0 120 350" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <filter id="bijliGlow4" x="-80%" y="-80%" width="260%" height="260%">
            <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#ffffff"/>
            <feDropShadow dx="0" dy="0" stdDeviation="12" flood-color="#c084fc"/>
            <feDropShadow dx="0" dy="0" stdDeviation="28" flood-color="#7c3aed"/>
        </filter>
    </defs>
    <polyline points="60,0 48,80 78,80 35,180 60,180 22,280 48,280 15,350"
              stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"
              filter="url(#bijliGlow4)"/>
    <polyline points="35,180 12,215 22,240" stroke="#e0e7ff" stroke-width="1.8" fill="none" filter="url(#bijliGlow4)"/>
</svg>

<div class="sky-flash-live"></div>
<div class="ground-flash-live"></div>
<div class="storm-cloud-1"></div>
<div class="storm-cloud-2"></div>
<div class="storm-cloud-3"></div>
"""
        anim_css = """
.bijli-1 {
    position: fixed;
    top: 0;
    left: 22%;
    width: 180px;
    height: 600px;
    pointer-events: none;
    z-index: 9999;
    opacity: 0;
    filter: drop-shadow(0 0 10px #ffffff) drop-shadow(0 0 25px #60a5fa) drop-shadow(0 0 45px #a855f7);
    animation: strikeBijli1 3.5s ease-out infinite;
}

@keyframes strikeBijli1 {
    0%, 82%, 90%, 100% { opacity: 0; transform: scaleY(0.92) scaleX(0.98); }
    83% { opacity: 1; transform: scaleY(1) scaleX(1); }
    85% { opacity: 0.15; }
    86% { opacity: 0.95; }
    88% { opacity: 0.08; }
    89% { opacity: 0.7; }
}

.bijli-2 {
    position: fixed;
    top: 0;
    right: 18%;
    width: 200px;
    height: 650px;
    pointer-events: none;
    z-index: 9999;
    opacity: 0;
    filter: drop-shadow(0 0 10px #ffffff) drop-shadow(0 0 25px #38bdf8) drop-shadow(0 0 50px #9333ea);
    animation: strikeBijli2 4.2s ease-out infinite;
    animation-delay: 1.2s;
}

@keyframes strikeBijli2 {
    0%, 80%, 88%, 100% { opacity: 0; transform: scaleY(0.92) scaleX(0.98); }
    81% { opacity: 1; transform: scaleY(1) scaleX(1); }
    83% { opacity: 0.1; }
    84% { opacity: 0.9; }
    86% { opacity: 0.05; }
    87% { opacity: 0.65; }
}

.bijli-3 {
    position: fixed;
    top: 0;
    left: 48%;
    width: 140px;
    height: 460px;
    pointer-events: none;
    z-index: 9999;
    opacity: 0;
    filter: drop-shadow(0 0 8px #ffffff) drop-shadow(0 0 20px #818cf8) drop-shadow(0 0 38px #a855f7);
    animation: strikeBijli3 5.5s ease-out infinite;
    animation-delay: 2.5s;
}

@keyframes strikeBijli3 {
    0%, 85%, 92%, 100% { opacity: 0; transform: scaleY(0.9) scaleX(0.97); }
    86% { opacity: 1; transform: scaleY(1) scaleX(1); }
    88% { opacity: 0.2; }
    89% { opacity: 0.85; }
    91% { opacity: 0.1; }
}

.bijli-4 {
    position: fixed;
    top: 0;
    right: 8%;
    width: 110px;
    height: 320px;
    pointer-events: none;
    z-index: 9999;
    opacity: 0;
    filter: drop-shadow(0 0 8px #ffffff) drop-shadow(0 0 18px #c084fc) drop-shadow(0 0 30px #7c3aed);
    animation: strikeBijli4 7s ease-out infinite;
    animation-delay: 0.8s;
}

@keyframes strikeBijli4 {
    0%, 88%, 94%, 100% { opacity: 0; transform: scaleY(0.88); }
    89% { opacity: 1; transform: scaleY(1); }
    91% { opacity: 0.15; }
    92% { opacity: 0.9; }
    93% { opacity: 0.05; }
}

.sky-flash-live {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: radial-gradient(circle at 35% 8%, rgba(255, 255, 255, 0.6) 0%, rgba(168, 85, 247, 0.35) 30%, rgba(56, 189, 248, 0.15) 55%, transparent 80%);
    opacity: 0;
    pointer-events: none;
    z-index: 9998;
    animation: skyFlashPulse 3.5s ease-out infinite;
}

@keyframes skyFlashPulse {
    0%, 82%, 90%, 100% { opacity: 0; }
    83% { opacity: 1; }
    85% { opacity: 0.15; }
    86% { opacity: 0.95; }
    88% { opacity: 0.05; }
    89% { opacity: 0.6; }
}

.ground-flash-live {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100vw;
    height: 220px;
    background: radial-gradient(ellipse at 40% 100%, rgba(168, 85, 247, 0.4) 0%, rgba(99, 102, 241, 0.2) 40%, transparent 75%);
    opacity: 0;
    pointer-events: none;
    z-index: 9997;
    animation: groundFlash 4.2s ease-out infinite;
    animation-delay: 1.2s;
}

@keyframes groundFlash {
    0%, 80%, 88%, 100% { opacity: 0; }
    81% { opacity: 0.8; }
    83% { opacity: 0.1; }
    84% { opacity: 0.7; }
    86% { opacity: 0; }
}

.storm-cloud-1 {
    position: fixed;
    top: -60px;
    left: -550px;
    width: 900px;
    height: 260px;
    background: radial-gradient(ellipse at center, rgba(10, 5, 24, 0.98) 0%, rgba(30, 20, 60, 0.85) 40%, rgba(88, 28, 135, 0.2) 70%, transparent 85%);
    filter: blur(30px);
    border-radius: 140px;
    pointer-events: none;
    z-index: 9997;
    animation: cloudMove 35s linear infinite;
}

.storm-cloud-2 {
    position: fixed;
    top: 50px;
    left: -650px;
    width: 1000px;
    height: 280px;
    background: radial-gradient(ellipse at center, rgba(15, 10, 35, 0.95) 0%, rgba(49, 10, 100, 0.5) 50%, transparent 80%);
    filter: blur(32px);
    border-radius: 160px;
    pointer-events: none;
    z-index: 9997;
    animation: cloudMove 48s linear infinite;
    animation-delay: -15s;
}

.storm-cloud-3 {
    position: fixed;
    top: 160px;
    left: -480px;
    width: 700px;
    height: 200px;
    background: radial-gradient(ellipse at center, rgba(20, 10, 50, 0.9) 0%, rgba(88, 28, 135, 0.3) 55%, transparent 80%);
    filter: blur(28px);
    border-radius: 130px;
    pointer-events: none;
    z-index: 9996;
    animation: cloudMove 55s linear infinite;
    animation-delay: -30s;
}

.rain-mist-live {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100vw;
    height: 160px;
    background: linear-gradient(to top, rgba(168, 85, 247, 0.2) 0%, rgba(56, 189, 248, 0.15) 50%, transparent 100%);
    filter: blur(22px);
    pointer-events: none;
    z-index: 9997;
}
"""

    else:
        bg_css = """
.stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 50% 0%, #0c1c38 0%, #060e22 45%, #02050e 100%) !important;
    background-attachment: fixed !important;
}
"""
        elements_html = """
__DROPS_HTML__
<div class="storm-cloud-1"></div>
<div class="storm-cloud-2"></div>
<div class="rain-mist-live"></div>
"""
        anim_css = """
__SHARED_RAIN_CSS__

.storm-cloud-1 {
    position: fixed;
    top: -30px;
    left: -500px;
    width: 700px;
    height: 180px;
    background: radial-gradient(ellipse at center, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.65) 50%, transparent 75%);
    filter: blur(25px);
    border-radius: 120px;
    pointer-events: none;
    z-index: 9997;
    animation: cloudMove 50s linear infinite;
}

.storm-cloud-2 {
    position: fixed;
    top: 80px;
    left: -600px;
    width: 800px;
    height: 200px;
    background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.25) 0%, rgba(30, 58, 138, 0.4) 55%, transparent 75%);
    filter: blur(28px);
    border-radius: 140px;
    pointer-events: none;
    z-index: 9997;
    animation: cloudMove 65s linear infinite;
    animation-delay: -20s;
}

.rain-mist-live {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100vw;
    height: 140px;
    background: linear-gradient(to top, rgba(56, 189, 248, 0.25) 0%, rgba(30, 41, 59, 0.1) 50%, transparent 100%);
    filter: blur(20px);
    pointer-events: none;
    z-index: 9997;
}

@keyframes cloudMove {
    0% { transform: translateX(-500px); }
    100% { transform: translateX(calc(100vw + 600px)); }
}
"""

    if mode == "rain":
        drops_count = 120
        drops_html_parts = []
        drops_css_parts = []
        for i in range(drops_count):
            left = random.uniform(0, 100)
            height = random.uniform(18, 42)
            dur = random.uniform(0.7, 1.6)
            delay = random.uniform(0, 4)
            opacity = random.uniform(0.3, 0.9)
            w = random.choice([1.5, 2, 2.5])
            drops_html_parts.append(
                f'<div class="raindrop" style="left:{left:.1f}vw;width:{w}px;height:{height:.0f}px;'
                f'animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s;opacity:{opacity:.2f};"></div>'
            )
            drops_css_parts.append(
                f'.raindrop:nth-child({i + 1}) {{ left: {left:.1f}vw; width: {w}px; height: {height:.0f}px; }}'
            )
        drops_html = "\n".join(drops_html_parts)
        drops_css = "\n".join(drops_css_parts)
    else:
        drops_html = ""
        drops_css = ""

    elements_html = elements_html.replace("__DROPS_HTML__", drops_html)
    shared_rain_filled = shared_rain_css.replace("__DROPS_CSS__", drops_css)
    anim_css = anim_css.replace("__SHARED_RAIN_CSS__", shared_rain_filled)

    full_css = f"""
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #f8fafc;
}}

{sidebar_css}
{bg_css}

[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section[data-testid="stMain"],
section.main,
.main,
div[data-testid="stAppViewContainer"] > section:first-child,
div[data-testid="stAppViewBlockContainer"] {{
    background: transparent !important;
    background-color: transparent !important;
}}

.block-container {{
    position: relative;
    z-index: 10;
    padding-top: 0.6rem !important;
    padding-bottom: 3rem !important;
    max-width: 1280px !important;
    background: transparent !important;
}}

{anim_css}

/* Glassmorphism Cards */
.glass-card {{
    background: linear-gradient(135deg, rgba(22, 33, 56, 0.78) 0%, rgba(11, 20, 38, 0.88) 100%) !important;
    backdrop-filter: blur(24px) saturate(190%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(190%) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 20px !important;
    padding: 22px 26px !important;
    box-shadow: 0 12px 35px -5px rgba(0, 0, 0, 0.55), 0 0 1px 1px rgba(255, 255, 255, 0.08) inset !important;
    margin-bottom: 22px !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}}

.glass-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 18px 40px -4px rgba(0, 0, 0, 0.7), 0 0 24px rgba(56, 189, 248, 0.25) !important;
    border-color: rgba(56, 189, 248, 0.45) !important;
}}

div[data-testid="stMetric"] {{
    background: linear-gradient(145deg, rgba(22, 33, 56, 0.75) 0%, rgba(11, 20, 38, 0.88) 100%) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 18px !important;
    padding: 16px 22px !important;
    box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.45) !important;
    transition: all 0.25s ease;
}}

div[data-testid="stMetric"]:hover {{
    border-color: rgba(56, 189, 248, 0.45) !important;
    transform: translateY(-2px);
    box-shadow: 0 14px 30px -4px rgba(0, 0, 0, 0.6), 0 0 16px rgba(56, 189, 248, 0.22) !important;
}}

div[data-testid="stMetricLabel"] {{
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}}

div[data-testid="stMetricValue"] {{
    color: #f8fafc !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}}

.stButton > button {{
    background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 14px !important;
    padding: 10px 24px !important;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4) !important;
    transition: all 0.25s ease !important;
}}

.stButton > button:hover {{
    background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%) !important;
    box-shadow: 0 8px 24px rgba(56, 189, 248, 0.5) !important;
    transform: translateY(-2px) !important;
}}

.weather-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 16px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}}
.badge-blue {{ background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); }}
.badge-green {{ background: rgba(52, 211, 153, 0.18); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.35); }}
.badge-amber {{ background: rgba(251, 191, 36, 0.18); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.35); }}
.badge-rose {{ background: rgba(244, 63, 94, 0.18); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.35); }}

header[data-testid="stHeader"] {{
    background: transparent !important;
}}

/* ============ MOBILE / RESPONSIVE ============ */
@media (max-width: 768px) {{
    .block-container {{
        padding-top: 0.3rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }}
    h1 {{
        font-size: 1.6rem !important;
        line-height: 1.25 !important;
    }}
    h2 {{
        font-size: 1.2rem !important;
    }}
    h3 {{
        font-size: 1.05rem !important;
    }}
    .glass-card {{
        padding: 14px 16px !important;
        border-radius: 16px !important;
    }}
    .sun-live {{
        width: 70px !important;
        height: 70px !important;
        top: 20% !important;
        right: 20px !important;
    }}
    .sun-glow-ring {{
        width: 150px !important;
        height: 150px !important;
        top: calc(20% - 40px) !important;
        right: -15px !important;
    }}
    .storm-cloud-1 {{
        width: 600px !important;
        height: 180px !important;
    }}
    .storm-cloud-2 {{
        width: 700px !important;
        height: 200px !important;
    }}
    .bijli-1 {{ width: 110px !important; left: 15% !important; }}
    .bijli-2 {{ width: 130px !important; right: 12% !important; }}
    .bijli-3 {{ width: 90px !important; }}
    .bijli-4 {{ width: 75px !important; }}

    /* Make metric cards stack nicely */
    div[data-testid="stMetric"] {{
        padding: 12px 14px !important;
    }}
    div[data-testid="stMetricValue"] {{
        font-size: 1.4rem !important;
    }}

    /* Collapsible horizontal menu on small screens -> allow wrap */
    .stHorizontalBlock {{
        flex-wrap: wrap !important;
        gap: 0.35rem !important;
    }}

    /* Full-width buttons */
    .stButton > button {{
        width: 100% !important;
    }}
}}

/* Extra small phones */
@media (max-width: 480px) {{
    h1 {{ font-size: 1.35rem !important; }}
    .block-container {{ padding-left: 0.4rem !important; padding-right: 0.4rem !important; }}
}}
"""
    # 1. Inject styling via st.markdown with unsafe_allow_html=True.
    # st.markdown with unsafe_allow_html=True guarantees that <style> tags and keyframe
    # animations are NEVER stripped by DOMPurify on Streamlit Community Cloud.
    st.markdown(f"<style>\n{full_css}\n</style>", unsafe_allow_html=True)

    # 2. Inject live animation elements via st.markdown
    if elements_html.strip():
        st.markdown(elements_html, unsafe_allow_html=True)


def render_top_navbar_with_theme(current_title: str = "Overview") -> str:
    """Render horizontal Option Menu on the left, with compact Themes dropdown at the right corner."""
    col_menu, col_theme = st.columns([6.0, 1.4])

    options = [
        "Overview",
        "7-Day Forecast",
        "Agro-Advisory",
        "Model Comparison",
        "Block Map",
        "Kisan View",
        "Panchayat Bulletin",
    ]
    icons = [
        "house-door-fill",
        "cloud-rain-heavy-fill",
        "flower1",
        "bar-chart-line-fill",
        "geo-alt-fill",
        "person-badge-fill",
        "bank2",
    ]
    default_idx = options.index(current_title) if current_title in options else 0

    with col_menu:
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            default_index=default_idx,
            orientation="horizontal",
            styles={
                "container": {
                    "padding": "4px 8px",
                    "background": "linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(10, 18, 36, 0.92) 100%)",
                    "backdrop-filter": "blur(20px)",
                    "border": "1px solid rgba(255, 255, 255, 0.12)",
                    "border-radius": "16px",
                    "box-shadow": "0 6px 24px rgba(0, 0, 0, 0.45)",
                    "margin-bottom": "10px",
                    "display": "flex",
                    "flex-wrap": "wrap",
                    "justify-content": "flex-start",
                },
                "nav": {
                    "display": "flex",
                    "flex-wrap": "wrap",
                    "gap": "2px",
                },
                "icon": {"color": "#38bdf8", "font-size": "14px"},
                "nav-link": {
                    "font-size": "12.5px",
                    "font-weight": "600",
                    "color": "#cbd5e1",
                    "border-radius": "10px",
                    "padding": "7px 10px",
                    "margin": "0 2px",
                    "--hover-color": "rgba(56, 189, 248, 0.15)",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #0284c7 0%, #2563eb 100%)",
                    "color": "#ffffff",
                    "font-weight": "700",
                    "box-shadow": "0 4px 12px rgba(37, 99, 235, 0.4)",
                },
            },
        )

    with col_theme:
        theme_options = ["🌧️ Rain", "☀️ Day", "⚡ Thunder"]
        theme_map = {"🌧️ Rain": "rain", "☀️ Day": "day", "⚡ Thunder": "thunder"}
        rev_map = {"rain": "🌧️ Rain", "day": "☀️ Day", "thunder": "⚡ Thunder"}
        curr_theme = rev_map.get(st.session_state.get("theme_mode", "rain"), "🌧️ Rain")
        def_idx = theme_options.index(curr_theme) if curr_theme in theme_options else 0

        # Sleek dropdown with explicit Themes label
        st.markdown('<div style="font-size: 11px; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px;">Themes</div>', unsafe_allow_html=True)
        selected_theme = st.selectbox(
            "Themes",
            theme_options,
            index=def_idx,
            key=f"theme_picker_v3_{current_title.replace(' ', '_').replace('-', '_')}",
            label_visibility="collapsed",
            help="Select live animated wallpaper theme",
        )
        new_mode = theme_map[selected_theme]
        if new_mode != st.session_state.get("theme_mode", "rain"):
            st.session_state["theme_mode"] = new_mode
            st.rerun()

    return selected


_PAGE_MAP = {
    "Overview": "app.py",
    "7-Day Forecast": "pages/1_🌤_Forecast.py",
    "Agro-Advisory": "pages/2_🌾_Advisory.py",
    "Model Comparison": "pages/3_📊_Comparison.py",
    "Block Map": "pages/4_🏘️_Block.py",
    "Kisan View": "pages/5_🧑‍🌾_Kisan.py",
    "Panchayat Bulletin": "pages/6_🏛️_Panchayat_Bulletin.py",
}


def navigate_if_needed(current_title: str):
    """Call after render_top_navbar_with_theme. Handles page switching in one line."""
    nav_choice = render_top_navbar_with_theme(current_title)
    if nav_choice != current_title:
        target = _PAGE_MAP.get(nav_choice)
        if target:
            st.switch_page(target)
        return None
    return nav_choice


def render_voice_button(text_hi: str, text_en: str = ""):
    """Embed browser voice audio player for rural farmers."""
    hi_escaped = text_hi.replace('"', '\"').replace('\n', ' ')
    html = f"""
    <div style="margin: 14px 0;">
        <button id="speechBtn" onclick="toggleSpeech()" style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: #ffffff;
            border: none;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 700;
            border-radius: 12px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
            transition: all 0.2s ease;
        ">
            <span id="btnIcon">🔊</span>
            <span id="btnText">किसान वाणी सुनें (Listen Voice Advisory)</span>
        </button>
        <span id="speechStatus" style="color: #94a3b8; font-size: 13px; margin-left: 12px;"></span>
    </div>

    <script>
    let isSpeaking = false;
    function toggleSpeech() {{
        if (!('speechSynthesis' in window)) {{
            alert('Your browser does not support voice synthesis.');
            return;
        }}
        if (isSpeaking) {{
            window.speechSynthesis.cancel();
            isSpeaking = false;
            document.getElementById('btnIcon').innerText = '🔊';
            document.getElementById('btnText').innerText = 'किसान वाणी सुनें (Listen Voice Advisory)';
            document.getElementById('speechStatus').innerText = 'रुका हुआ (Stopped)';
            return;
        }}
        window.speechSynthesis.cancel();
        const text = "{hi_escaped}";
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'hi-IN';
        utterance.rate = 0.92;
        utterance.pitch = 1.0;
        
        const voices = window.speechSynthesis.getVoices();
        const hiVoice = voices.find(v => v.lang.includes('hi') || v.name.includes('Hindi'));
        if (hiVoice) utterance.voice = hiVoice;

        utterance.onstart = () => {{
            isSpeaking = true;
            document.getElementById('btnIcon').innerText = '⏹️';
            document.getElementById('btnText').innerText = 'आवाज रोकें (Stop Voice)';
            document.getElementById('speechStatus').innerText = '▶️ बोल रहा है (Speaking)...';
        }};
        utterance.onend = () => {{
            isSpeaking = false;
            document.getElementById('btnIcon').innerText = '🔊';
            document.getElementById('btnText').innerText = 'किसान वाणी सुनें (Listen Voice Advisory)';
            document.getElementById('speechStatus').innerText = '✅ संपन्न (Finished)';
        }};
        utterance.onerror = (e) => {{
            isSpeaking = false;
            document.getElementById('btnIcon').innerText = '🔊';
            document.getElementById('btnText').innerText = 'किसान वाणी सुनें (Listen Voice Advisory)';
            document.getElementById('speechStatus').innerText = '';
        }};
        window.speechSynthesis.speak(utterance);
    }}
    </script>
    """
    components.html(html, height=65)

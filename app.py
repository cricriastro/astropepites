import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval
import math

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro v4.4", layout="wide")

# --- STYLE VISION NOCTURNE ---
st.markdown("""
<style>
.stApp { background-color: #000000; color: #FFFFFF !important; }
h1, h2, h3 { color: #FF3333 !important; }
.stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1rem !important; }
.stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; }
[data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
.stTabs [data-baseweb="tab-list"] { background-color: #111; border-radius: 10px; }
.stTabs [data-baseweb="tab"] { color: #FF3333 !important; font-weight: bold !important; }
.mosaic-alert { background-color: #331a00; border: 1px dashed #FF8800; padding: 10px; border-radius: 10px; color: #FF8800 !important; font-weight: bold; }
.boost-box { background-color: #001a33; border: 1px solid #0088FF; padding: 10px; border-radius: 10px; color: #0088FF !important; }
.safety-box { background-color: #440000; border: 2px solid #FF0000; padding: 15px; border-radius: 10px; color: white; font-weight: bold; text-align: center; }
hr { border: 1px solid #333; }
.stSelectbox div[data-baseweb="select"] { background-color: #222 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR : GPS ---
st.sidebar.title("🔭 AstroPépites Pro")
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)

if loc:
    st.session_state.lat = loc['coords']['latitude']
    st.session_state.lon = loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")

# --- MASQUE D’HORIZON ---
st.sidebar.header("🌲 Masque d'Horizon")
with st.sidebar.expander("Réglage Obstacles", expanded=False):
    mN = st.slider("Nord", 0, 90, 15)
    mNE = st.slider("NE", 0, 90, 15)
    mE = st.slider("Est", 0, 90, 20)
    mSE = st.slider("SE", 0, 90, 30)
    mS = st.slider("Sud", 0, 90, 15)
    mSW = st.slider("SW", 0, 90, 15)
    mO = st.slider("Ouest", 0, 90, 20)
    mNO = st.slider("NO", 0, 90, 15)

mask_values = [mN, mNE, mE, mSE, mS, mSW, mO, mNO]

angles = np.linspace(0, 2*np.pi, 8, endpoint=False).tolist()
fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.fill(angles + [angles[0]], mask_values + [mask_values[0]], color='red', alpha=0.4)
ax.fill_between(angles + [angles[0]], mask_values + [mask_values[0]], 90, color='green', alpha=0.2)
ax.set_yticklabels([])
ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'O', 'NO'], color='white', fontsize=8)
ax.patch.set_facecolor('black')
fig.patch.set_facecolor('black')
st.sidebar.pyplot(fig)

def get_horizon_limit(az):
    idx = int(((az + 22.5) % 360) // 45)
    return mask_values[idx]

# --- MATÉRIEL ---
st.sidebar.header("📸 Matériel")
TELS = {
    "Evolux 62ED": (400, 62),
    "Esprit 100": (550, 100),
    "RedCat 51": (250, 51),
    "Newton 200/800": (800, 200),
    "C8": (1280, 203)
}

CAMS = {
    "ASI 183MC": (13.2, 8.8, 2.4, 84),
    "ASI 2600MC": (23.5, 15.7, 3.76, 80)
}

tube = st.sidebar.selectbox("Télescope", list(TELS.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMS.keys()))

focale, diam = TELS[tube]
sw, sh, px, qe = CAMS[cam]

f_ratio = focale / diam
fov_w = (sw * 3438) / focale
fov_h = (sh * 3438) / focale

# --- BASE DE DONNÉES ---
db = [
    {"name": "M31 (Andromède)", "ra": "00:42:44", "dec": "+41:16:09", "type": "Galaxy", "size_w": 180, "size_h": 60, "cat": "Messier"},
    {"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size_w": 65, "size_h": 60, "cat": "Messier"},
    {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size_w": 60, "size_h": 50, "cat": "Pépites Rares"},
    {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size_w": 15, "size_h": 15, "cat": "Pépites Rares"},
    {"name": "24P/Schaumasse", "ra": "12:58:05", "dec": "+14:01:06", "type": "Comet", "size_w": 10, "size_h": 10, "cat": "Comètes"},
]

# --- APP ---
st.title("🔭 AstroPépites Pro v4.4")
t_radar, t_meteo, t_batt = st.tabs(["💎 Radar & Catalogues", "☁️ Météo Live", "🔋 Énergie"])

now = Time.now()
obs_loc = EarthLocation(lat=u_lat * u.deg, lon=u_lon * u.deg)

try:
    moon_pos = get_body("moon", now)
except Exception:
    moon_pos = None

with t_radar:
    col_cat, col_obj = st.columns(2)

    with col_cat:
        selected_cat = st.selectbox(
            "📂 1. Choisir un catalogue",
            ["Pépites Rares", "Messier", "Planètes", "Comètes", "Événements 2026"]
        )

    if selected_cat == "Planètes":
        filtered_objs = ["Jupiter", "Saturn", "Mars"]
    elif selected_cat == "Événements 2026":
        filtered_objs = ["Éclipse Solaire (12 Août)", "Éclipse Lunaire (28 Août)"]
    else:
        filtered_objs = [t["name"] for t in db if t["cat"] == selected_cat]

    with col_obj:
        active_target_name = st.selectbox(
            "🎯 2. Choisir l'objet",
            ["--- Sélectionner ---"] + filtered_objs
        )

    if active_target_name != "--- Sélectionner ---":
        st.markdown("---")

        if selected_cat == "Événements 2026":
            if "Solaire" in active_target_name:
                st.subheader("🌞 Éclipse Solaire - 12 Août 2026")
                st.markdown(
                    '<div class="safety-box">⚠️ FILTRE SOLAIRE ND5.0 OBLIGATOIRE ! Ne pointez jamais le soleil sans protection.</div>',
                    unsafe_allow_html=True
                )
            else:
                st.subheader("🌕 Éclipse Lunaire - 28 Août 2026")

        else:
            if selected_cat == "Planètes":
                coord = get_body(active_target_name.lower(), now)
                t_type = "Planet"
                t_size_w = t_size_h = 1
            else:
                t = next(obj for obj in db if obj["name"] == active_target_name)
                coord = SkyCoord(t["ra"], t["dec"], unit=(u.hourangle, u.deg))
                t_type = t["type"]
                t_size_w = t["size_w"]
                t_size_h = t["size_h"]

            altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
            limit = get_horizon_limit(altaz.az.deg)
            visible = altaz.alt.deg > limit

            col1, col2, col3 = st.columns([1.5, 2, 1.2])

            with col1:
                fov_img = 0.1 if t_type == "Planet" else 1.5
                img_url = (
                    "https://alasky.u-strasbg.fr/hips-image-services/hips2fits"
                    f"?hips=CDS/P/DSS2/color&ra={coord.ra.deg}&dec={coord.dec.deg}"
                    f"&width=450&height=450&fov={fov_img}&format=jpg"
                )
                st.image(img_url, use_container_width=True)

            with col2:
                status = "✅ DÉGAGÉ" if visible else f"❌ MASQUÉ (<{limit}°)"
                st.subheader(f"{active_target_name} {status}")

                st.markdown(
                    f"📍 Altitude : **{round(altaz.alt.deg)}°**  \n"
                    f"✨ Type : **{t_type}**"
                )

                times = now + np.linspace(0, 12, 24) * u.hour
                hours = [
                    (datetime.now() + timedelta(minutes=30 * i)).strftime("%H:%M")
                    for i in range(24)
                ]
                alts = [
                    max(0, coord.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg)
                    for ts in times
                ]

                st.line_chart(pd.DataFrame({"Altitude": alts}, index=hours))

            with col3:
                if t_type != "Planet":
                    expo = round(4 * (f_ratio / 4) ** 2 * (80 / qe), 1)
                    st.metric("Temps suggéré", f"{expo} h")
                    st.write(f"🖼️ Cadrage : {round((t_size_w / fov_w) * 100)} %")
                else:
                    st.metric("Mode", "Vidéo")

                if moon_pos:
                    st.write(f"🌙 Lune à {round(coord.separation(moon_pos).deg)}°")

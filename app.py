import streamlit as st
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval
import math

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro v4.5", layout="wide")

# --- STYLE VISION NOCTURNE (Le style qui fait planter les anciennes versions !) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF3333 !important; font-weight: bold !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; }
    [data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; font-weight: bold !important; }
    .mosaic-alert { background-color: #331a00; border: 1px dashed #FF8800; padding: 10px; border-radius: 10px; color: #FF8800 !important; font-weight: bold; }
    .boost-box { background-color: #001a33; border: 1px solid #0088FF; padding: 10px; border-radius: 10px; color: #0088FF !important; }
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True) # <-- CECI EST LA CORRECTION POUR LE STYLE!

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat, st.session_state.lon = loc['coords']['latitude'], loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")
h_mask = st.sidebar.slider("Masque d'Horizon (°)", 0, 60, 25)

# BOUSSOLE ASIAIR
st.sidebar.header("🌲 Masque d'Horizon")
with st.sidebar.expander("Réglage Obstacles", expanded=False):
    mN = st.slider("Nord", 0, 90, 20); mNE = st.slider("NE", 0, 90, 15); mE = st.slider("Est", 0, 90, 20)
    mSE = st.slider("SE", 0, 90, 30); mS = st.slider("Sud", 0, 90, 15); mSW = st.slider("SW", 0, 90, 15)
    mO = st.slider("Ouest", 0, 90, 20); mNO = st.slider("NO", 0, 90, 15)
    mask_values = [mN, mNE, mE, mSE, mS, mSW, mO, mNO]
    angles = np.linspace(0, 2*np.pi, 8, endpoint=False).tolist()
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'}); ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.fill(angles + [angles[0]], mask_values + [mask_values[0]], color='red', alpha=0.4)
    ax.fill_between(angles + [angles[0]], mask_values + [mask_values[0]], 90, color='green', alpha=0.2)
    ax.set_yticklabels([]); ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'O', 'NO'], color='white', fontsize=8)
    ax.patch.set_facecolor('black'); fig.patch.set_facecolor('black')
    st.sidebar.pyplot(fig)

def get_horizon_limit(az):
    idx = int(((az + 22.5) % 360) // 45)
    return mask_values[idx]

# --- MATÉRIEL ---
st.sidebar.header("📸 Matériel")
TELS = {"Evolux 62ED":(400,62), "Esprit 100":(550,100), "RedCat 51":(250,51), "Newton 200/800":(800,200), "C8":(1280,203)}
CAMS = {"ASI 183MC":(13.2, 8.8, 2.4, 84), "ASI 2600MC":(23.5, 15.7, 3.76, 80)}
tube = st.sidebar.selectbox("Télescope", list(TELS.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMS.keys()))
focale, diam = TELS[tube]; sw, sh, px, qe = CAMS[cam]
f_ratio = focale / diam
fov_w = (sw * 3438) / focale
fov_h = (sh * 3438) / focale

# --- BASE DE DONNÉES CIBLES ---
db = []
if st.sidebar.checkbox("💎 Pépites Rares", value=True):
    db += [{"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size_w": 60, "size_h": 50},
           {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size_w": 15, "size_h": 15}]
if st.sidebar.checkbox("⭐ Messier", value=True):
    db += [{"name": "M31 (Andromède)", "ra": "00:42:44", "dec": "+41:16:09", "type": "Galaxy", "size_w": 180, "size_h": 60},
           {"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size_w": 65, "size_h": 60}]
if st.sidebar.checkbox("🌌 NGC / IC", value=False):
    db += [{"name": "NGC 2237 (Rosette)", "ra": "06:32:19", "dec": "+05:03:12", "type": "Emission", "size_w": 80, "size_h": 80}]

# --- APP ---
st.title("🔭 AstroPépites Pro v4.5")
t_radar, t_meteo, t_batterie = st.tabs(["💎 Radar & Planning", "☁️ Météo Live", "🔋 Énergie"])

now = Time.now(); obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
try: moon_pos = get_body("moon", now)
except: moon_pos = None

with t_radar:
    st.write("### 🎯 Analyse et Planning")
    target_names = [t['name'] for t in db]
    active_target = st.selectbox("Cible active (pour voir le planning) :", ["--- Sélectionner ---"] + target_names)

    for t in db:
        if t['name'] != active_target: continue
        
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        limit = get_horizon_limit(altaz.az.deg)
        visible = altaz.alt.deg > limit
        
        col1, col2, col3 = st.columns([1.5, 2, 1.2])
        with col1:
            img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={coord.ra.deg}&dec={coord.dec.deg}&width=450&height=450&fov=1.5&format=jpg"
            st.image(img, use_container_width=True)
        with col2:
            status = "✅ DÉGAGÉ" if visible else f"❌ MASQUÉ (<{limit}°)"
            st.subheader(f"{t['name']} {status}")
            st.write(f"📍 Alt : **{round(altaz.alt.deg)}°** | ✨ Filtre : **{'Dual-Band' if t['type']=='Emission' else 'RGB'}**")
            
            if t['type'] == "Galaxy":
                st.markdown('<div class="boost-box">🚀 Expert Boost : Ajoutez du H-Alpha pour les nébuleuses internes !</div>', unsafe_allow_html=True)
            
            with st.expander("📈 Planning Visibilité & Mosaïque", expanded=True):
                if (t['size_w'] / fov_w) * 100 > 90:
                    pw, ph = math.ceil(t['size_w']/(fov_w*0.8)), math.ceil(t['size_h']/(fov_h*0.8))
                    st.markdown(f'<div class="mosaic-alert">⚠️ MOSAÏQUE : {pw} x {ph} panneaux</div>', unsafe_allow_html=True)
                
                times = now + np.linspace(0, 12, 24) * u.hour
                hours = [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]
                alts = [max(0, coord.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg) for ts in times]
                st.line_chart(pd.DataFrame({"Altitude": alts}, index=hours), color="#FF3333")

        with col3:
            expo = round(4 * (f_ratio/4)**2 * (80/qe), 1)
            st.metric("Temps suggéré", f"{expo}h")
            if moon_pos: st.write(f"🌙 Lune à {round(coord.separation(moon_pos).deg)}°")
            st.write(f"📐 Ton Champ : {round(fov_w)}' x {round(fov_h)}'")
        st.markdown("---")

# Météo et Batterie restent identiques...
with t_meteo:
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={u_lat}&longitude={u_lon}&current_weather=true&hourly=cloudcover&timezone=auto"
        w = requests.get(w_url).json()
        df_w = pd.DataFrame({"Heure": [d[11:16] for d in w['hourly']['time'][:24]], "Nuages (%)": w['hourly']['cloudcover'][:24]}).set_index("Heure")
        st.subheader("☁️ Prévisions Nuages (%)")
        st.area_chart(df_w, color="#FF3333")
    except: st.error("Météo indisponible")

with t_batterie:
    st.subheader("🔋 Énergie")
    wh = st.number_input("Wh batterie", value=240)
    c1, c2 = st.columns(2)
    p_m = c1.slider("Monture", 5, 25, 10); p_t = c1.slider("TEC", 0, 40, 20)
    p_p = c2.slider("ASIAIR/PC", 5, 25, 10); p_d = c2.slider("Chauffage", 0, 40, 15)
    st.metric("Autonomie", f"{round((wh*0.9)/(p_m+p_t+p_p+p_d), 1)} h")

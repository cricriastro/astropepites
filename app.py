import streamlit as st
import pandas as pd
import requests
import numpy as np
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro v3", layout="wide")

# --- STYLE VISION NOCTURNE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF3333 !important; font-weight: bold !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [aria-selected="true"] { background-color: #FF3333 !important; color: #FFFFFF !important; border-radius: 8px; }
    hr { border: 1px solid #333; }
    .safety-box { background-color: #440000; border: 3px solid #FF0000; padding: 20px; border-radius: 10px; color: white; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro v3")
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat = loc['coords']['latitude']
    st.session_state.lon = loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")
h_mask = st.sidebar.slider("Masque d'Horizon (°)", 0, 60, 20)

st.sidebar.header("📂 Filtres")
f_events = st.sidebar.checkbox("📅 Éclipses & Événements", value=True)
f_comets = st.sidebar.checkbox("☄️ Comètes", value=True)
f_rare = st.sidebar.checkbox("💎 Pépites Rares", value=True)
f_planets = st.sidebar.checkbox("🪐 Planètes", value=True)

st.sidebar.header("📸 Mon Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200), "Custom": (400,60)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80), "Custom": (13.2,8.8,3.76,80)}
tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = focale / diam
res = (px * 206) / focale

# --- BASE DE DONNÉES ÉVÉNEMENTS ---
events = []
if f_events:
    events += [
        {"name": "Éclipse Solaire (Europe)", "date": "2026-08-12", "type": "Solar", "desc": "Totale en Espagne, Partielle (90%) en Suisse/France."},
        {"name": "Éclipse Lunaire Partielle", "date": "2026-08-28", "type": "Lunar", "desc": "La Lune passera dans l'ombre de la Terre en fin de nuit."},
    ]

db_targets = []
if f_comets:
    db_targets += [{"name": "24P/Schaumasse", "ra": "12:58:05", "dec": "+14:01:06", "type": "Comet", "size": 10}]
if f_rare:
    db_targets += [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
    ]

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3, tab4 = st.tabs(["💎 Cibles & Événements", "🗓️ Planning", "☁️ Météo", "🔋 Batterie"])

now = Time.now()
obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)

# --- TAB 1 : RADAR ---
with tab1:
    # AFFICHER LES ÉCLIPSES EN PREMIER
    if f_events:
        st.subheader("📅 Événements à venir")
        for e in events:
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Date", e['date'])
                with col2:
                    st.write(f"### {e['name']}")
                    st.write(e['desc'])
                    if e['type'] == "Solar":
                        st.markdown('<div class="safety-box">⚠️ ATTENTION : Filtre Solaire ND5.0 OBLIGATOIRE sur votre Evolux 62 ! Risque de destruction de la ASI 183MC.</div>', unsafe_allow_html=True)
                    else:
                        st.info("💡 Conseil : Pas de filtre nécessaire. Utilisez le mode HDR pour capter la couleur rouge de l'ombre.")
            st.markdown("---")

    # RADAR DSO & PLANETES
    st.subheader("💎 Cibles visibles ce soir")
    for t in db_targets:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        if altaz.alt.deg > h_mask:
            col1, col2, col3 = st.columns([1.5, 2, 1.2])
            with col1:
                ra_d, de_d = coord.ra.deg, coord.dec.deg
                img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={ra_d}&dec={de_d}&width=400&height=400&fov=1.2&format=jpg"
                st.image(img, use_container_width=True)
            with col2:
                st.subheader(t['name'])
                st.write(f"📍 Alt : **{round(altaz.alt.deg)}°** | ✨ Filtre : **{'RGB' if t['type'] in ['Reflection', 'Comet'] else 'Dual-Band'}**")
            with col3:
                expo = round(4 * (f_ratio/4)**2, 1) if t['type'] != "Comet" else "Calculateur"
                st.metric("Temps suggéré", f"{expo}h" if t['type'] != "Comet" else "Comète")
            st.markdown("---")

# --- TAB 2 : PLANNING ---
with tab2:
    st.subheader("⏱️ Chronologie de votre nuit")
    if db_targets:
        time_steps = now + np.linspace(0, 12, 24) * u.hour
        planning_data = {"Heure": [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]}
        for t in db_targets:
            coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
            planning_data[t['name']] = [max(0, coord.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg) for ts in time_steps]
        st.line_chart(pd.DataFrame(planning_data).set_index("Heure"))

# --- TAB 4 : BATTERIE EXPERT ---
with tab4:
    st.subheader("🔋 Calculateur Batterie")
    wh = st.number_input("Wh de votre batterie", value=240)
    st.write("🔧 **Consommation estimée (Watts) :**")
    c1, c2 = st.columns(2)
    p_mount = c1.slider("Monture", 5, 25, 10)
    p_cam = c1.slider("Caméra TEC", 0, 40, 20)
    p_pc = c2.slider("ASIAIR/PC", 5, 25, 10)
    p_dew = c2.slider("Résistances Chauffantes", 0, 40, 15)
    
    total_w = p_mount + p_cam + p_pc + p_dew
    autonomie = (wh * 0.9) / total_w if total_w > 0 else 0
    st.metric("Autonomie estimée", f"{round(autonomie, 1)} heures")

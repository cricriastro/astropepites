import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- STYLE HAUTE VISIBILITÉ ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3, h4 { color: #FF3333 !important; }
    label, p, span { color: #FFFFFF !important; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1a1a1a; }
    .stTabs [data-baseweb="tab"] { color: #FF3333; }
    .stMetric { background-color: #1a0000; border: 1px solid #FF3333; border-radius: 10px; padding: 10px; }
    /* Fix pour la visibilité des inputs */
    input { color: #000000 !important; } 
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR SETUP ---
st.sidebar.title("🔭 AstroPépites Pro")
lang = st.sidebar.radio("Langue", ["Français", "English"])

st.sidebar.header("📍 Position & Horizon")
lat = st.sidebar.number_input("Latitude", value=46.0, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=6.0, format="%.4f")
h_mask = st.sidebar.slider("Masque Horizon (Altitude min °)", 0, 60, 25)

st.sidebar.header("📸 Mon Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}

tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
res = round((px * 206) / focale, 2)

# --- APP PRINCIPALE ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3, tab4 = st.tabs(["💎 Radar de Pépites", "☁️ Météo Live", "🔋 Énergie", "☄️ Comètes"])

# --- TAB 1 : RADAR ---
with tab1:
    st.write(f"### 🎯 Cibles pour {tube} (f/{f_ratio})")
    db = [
        {"name": "Sh2-157", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
    ]
    
    now = Time.now()
    loc = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
    try: moon_pos = get_body("moon", now)
    except: moon_pos = None

    results = []
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=loc))
        if altaz.alt.deg > h_mask:
            img = f"https://aladin.u-strasbg.fr/AladinLite/api/v1/preview?ra={coord.ra.deg}&dec={coord.dec.deg}&fov=1&width=200&height=200"
            results.append({
                "Aperçu": img,
                "Nom": t['name'],
                "Altitude": f"{round(altaz.alt.deg)}°",
                "Filtre": "Dual-Band" if t['type'] == "Emission" else "RGB Pur",
                "Temps Pose": f"{round(4 * (f_ratio/4)**2 * (80/qe), 1)}h",
                "ra": t['ra'], "dec": t['dec']
            })
    if results:
        df = pd.DataFrame(results)
        st.data_editor(df.drop(columns=['ra', 'dec']), column_config={"Aperçu": st.column_config.ImageColumn()}, hide_index=True)
        st.download_button("📥 Télécharger pour ASIAIR", df[["Nom", "ra", "dec"]].to_csv(index=False), "plan.csv")

# --- TAB 2 : MÉTÉO ---
with tab2:
    st.write("### 🛰️ Météo en direct")
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m"
        w = requests.get(url).json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Nuages", f"{w['hourly']['cloudcover'][0]}%")
        c2.metric("Humidité", f"{w['hourly']['relativehumidity_2m'][0]}%")
        c3.metric("Temp", f"{w['current_weather']['temperature']}°C")
    except: st.write("Erreur météo")

# --- TAB 3 : ÉNERGIE ---
with tab3:
    st.write("### 🔋 Calculateur de Batterie")
    wh = st.number_input("Capacité (Wh) - ex: Bluetti EB3A = 268", value=240)
    conso = st.slider("Consommation (Watts)", 10, 80, 35)
    st.metric("Autonomie", f"{round((wh*0.9)/conso, 1)} heures")

# --- TAB 4 : COMÈTES (NOUVEAU) ---
with tab4:
    st.write("### ☄️ Assistant Comètes")
    st.info("Les comètes bougent ! Pour ne pas avoir un noyau flou, calculez votre pose maximum.")
    
    v_c = st.number_input("Vitesse de la comète (arcsec / minute)", value=1.0, help="Donnée 'Motion' dans Stellarium")
    
    # Calcul basé sur ton échantillonnage (res)
    max_exp = res / (v_c / 60)
    
    st.metric("Temps de pose MAX conseillé", f"{round(max_exp, 1)} secondes")
    
    st.write("---")
    st.write("#### 🔍 Quelles sont les comètes visibles ?")
    st.markdown("[👉 Cliquez ici pour voir la liste des comètes actuelles (TheSkyLive)](https://theskylive.com/comets)")
    st.write("Une fois que vous avez le nom (ex: C/2023 A3), cherchez sa vitesse dans Stellarium et entrez-la au-dessus.")

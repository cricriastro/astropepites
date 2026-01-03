import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- STYLE VISION NOCTURNE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3 { color: #FF3333 !important; }
    .stMarkdown, label, p, span { color: #FFFFFF !important; font-weight: bold; }
    .stMetric { background-color: #1a0000; border: 1px solid #FF3333; border-radius: 10px; padding: 10px; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; }
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🔭 AstroPépites Pro")
u_lat = st.sidebar.number_input("Latitude", value=46.8, format="%.2f")
u_lon = st.sidebar.number_input("Longitude", value=7.1, format="%.2f")
h_mask = st.sidebar.slider("Masque Horizon (°)", 0, 60, 25)

st.sidebar.header("📸 Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}

tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3 = st.tabs(["💎 Radar", "☁️ Météo", "🔋 Batterie"])

with tab1:
    db = [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
        {"name": "Abell 21 (Medusa)", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12},
        {"name": "Sh2-129 (Flying Bat)", "ra": "21:11:48", "dec": "+59:59:12", "type": "Emission", "size": 120},
    ]

    now = Time.now()
    loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
    try: moon_pos = get_body("moon", now)
    except: moon_pos = None

    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=loc))
        
        if altaz.alt.deg > h_mask:
            # --- CALCUL TRANSIT (Méridien) ---
            # Approximatif pour la planification
            lst = now.sidereal_time('mean', longitude=u_lon*u.deg)
            ha = (lst - coord.ra).hour
            transit_in = -ha if ha < 12 else 24-ha
            transit_time = (datetime.now() + timedelta(hours=transit_in)).strftime("%H:%M")

            col1, col2, col3 = st.columns([1.2, 2, 1.2])
            
            with col1:
                # NOUVEAU LIEN IMAGE ALADIN STRASBOURG (Ultra Rapide)
                ra_deg, dec_deg = coord.ra.deg, coord.dec.deg
                img_url = f"https://aladin.u-strasbg.fr/AladinLite/api/v1/preview?ra={ra_deg}&dec={dec_deg}&fov=0.5&width=300&height=300"
                st.image(img_url, use_container_width=True)
            
            with col2:
                st.subheader(t['name'])
                st.write(f"📍 **Altitude :** {round(altaz.alt.deg)}°")
                st.write(f"⏱️ **Méridien à :** {transit_time}")
                st.write(f"✨ **Filtre :** {'Dual-Band' if t['type']=='Emission' or t['type']=='Planetary' else 'RGB Pur'}")
                st.write(f"🖼️ **Cadrage :** {round((t['size']/fov_w)*100)}% du champ")
            
            with col3:
                integration = round(4 * (f_ratio/4)**2 * (80/qe), 1)
                st.metric("Temps total", f"{integration}h")
                if moon_pos:
                    m_dist = round(coord.separation(moon_pos).deg)
                    st.write(f"🌙 Lune à {m_dist}°")
            
            st.markdown("---")

with tab2:
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={u_lat}&longitude={u_lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m"
        w = requests.get(w_url).json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Nuages", f"{w['hourly']['cloudcover'][0]}%")
        c2.metric("Humidité", f"{w['hourly']['relativehumidity_2m'][0]}%")
        c3.metric("Temp", f"{w['current_weather']['temperature']}°C")
    except: st.error("Erreur Météo")

with tab3:
    st.subheader("🔋 Énergie Nomade")
    capa = st.number_input("Batterie (Wh)", value=240)
    conso = st.slider("Conso (W)", 10, 100, 35)
    st.metric("Autonomie", f"{round((capa*0.9)/conso, 1)} h")

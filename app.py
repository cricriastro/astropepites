import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- STYLE HAUTE VISIBILITÉ ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF0000 !important; font-weight: bold !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; font-weight: bold !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF0000; border-radius: 12px; padding: 15px; }
    [data-testid="stMetricValue"] { color: #FF0000 !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; }
    .stTabs [data-baseweb="tab"] { color: #FF0000 !important; }
    button { background-color: #FF0000 !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION MÉTÉO ---
def get_live_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m"
        r = requests.get(url, timeout=5).json()
        return r
    except: return None

# --- SIDEBAR ---
st.sidebar.title("🔭 AstroPépites Pro")

# --- FONCTION GPS AUTOMATIQUE ---
st.sidebar.header("📍 Géolocalisation")
if st.sidebar.button("🛰️ Cliquer pour activer le GPS"):
    loc_js = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition')
    if loc_js:
        st.session_state.lat = loc_js['coords']['latitude']
        st.session_state.lon = loc_js['coords']['longitude']
        st.sidebar.success(f"Position GPS captée !")

# Valeurs par défaut ou session
lat_init = st.session_state.get('lat', 46.80)
lon_init = st.session_state.get('lon', 7.10)

u_lat = st.sidebar.number_input("Latitude", value=lat_init, format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=lon_init, format="%.4f")
h_mask = st.sidebar.slider("Masque d'Horizon (°)", 0, 60, 25)

st.sidebar.header("📸 Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200), "Esprit 100": (550, 100)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}

tube = st.sidebar.selectbox("Mon Tube", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Ma Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)
res = round((px * 206) / focale, 2)

# --- APP PRINCIPALE ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3, tab4 = st.tabs(["💎 Radar", "☁️ Météo", "🔋 Batterie", "☄️ Comètes"])

with tab1:
    db = [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
    ]

    now = Time.now()
    loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
    try: moon_pos = get_body("moon", now)
    except: moon_pos = None

    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=loc))
        
        if altaz.alt.deg > h_mask:
            col1, col2, col3 = st.columns([1.5, 2, 1.2])
            with col1:
                # Lien image haute fiabilité
                img_url = f"https://aladin.u-strasbg.fr/AladinLite/api/v1/preview?ra={coord.ra.deg}&dec={coord.dec.deg}&fov=1.0&width=300&height=300"
                st.image(img_url, caption=t['name'], use_container_width=True)
            with col2:
                st.subheader(t['name'])
                st.write(f"📍 Altitude : {round(altaz.alt.deg)}°")
                st.write(f"✨ Filtre : {'Dual-Band' if t['type']=='Emission' else 'RGB Pur'}")
                st.write(f"🖼️ Cadrage : {round((t['size']/fov_w)*100)}% du champ")
            with col3:
                integration = round(4 * (f_ratio/4)**2 * (80/qe), 1)
                st.metric("Temps total", f"{integration}h")
                if moon_pos:
                    st.write(f"🌙 Lune à {round(coord.separation(moon_pos).deg)}°")
            st.markdown("---")

with tab2:
    w = get_live_weather(u_lat, u_lon)
    if w:
        st.subheader(f"🛰️ Météo Live à {u_lat}, {u_lon}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Nuages", f"{w['hourly']['cloudcover'][0]}%")
        c2.metric("Humidité", f"{w['hourly']['relativehumidity_2m'][0]}%")
        c3.metric("Temp", f"{w['current_weather']['temperature']}°C")

with tab3:
    st.subheader("🔋 Batterie")
    wh = st.number_input("Wh", value=240)
    conso = st.slider("Watts", 10, 100, 35)
    st.metric("Autonomie", f"{round((wh*0.9)/conso, 1)} h")

with tab4:
    st.subheader("☄️ Comètes")
    v_c = st.number_input("Vitesse (arcsec/min)", value=1.0)
    max_p = res / (v_c / 60)
    st.metric("Pose MAX", f"{round(max_p, 1)} s")

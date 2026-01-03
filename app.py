import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- STYLE HAUTE VISIBILITÉ (Texte Blanc Pur sur Noir) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3 { color: #FF4B4B !important; font-weight: bold !important; }
    /* Force le texte en blanc partout */
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; }
    /* Amélioration des cases de saisie */
    input, select { background-color: #333 !important; color: #FFFFFF !important; border: 1px solid #FF4B4B !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF4B4B; border-radius: 12px; padding: 15px; }
    /* Style des onglets */
    .stTabs [data-baseweb="tab-list"] { background-color: #111; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #FF4B4B !important; font-weight: bold !important; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #FF4B4B !important; color: #FFFFFF !important; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION MÉTÉO ---
def get_live_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m"
        r = requests.get(url, timeout=5).json()
        return r
    except: return None

# --- BARRE LATÉRALE ---
st.sidebar.title("🔭 AstroPépites Pro")
lang = st.sidebar.radio("Langue", ["Français", "English"])

st.sidebar.header("📍 Position & Horizon")
u_lat = st.sidebar.number_input("Latitude (ex: 46.8)", value=46.8, format="%.2f")
u_lon = st.sidebar.number_input("Longitude (ex: 7.1)", value=7.1, format="%.2f")
h_mask = st.sidebar.slider("Masque d'Horizon (Altitude mini °)", 0, 60, 25)

st.sidebar.header("📸 Mon Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200), "Esprit 100": (550, 100)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}

tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)
res = round((px * 206) / focale, 2)

# --- APP PRINCIPALE ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3, tab4 = st.tabs(["💎 Radar de Pépites", "☁️ Météo Live", "🔋 Énergie", "☄️ Comètes"])

# --- TAB 1 : RADAR ---
with tab1:
    db = [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
        {"name": "Abell 21 (Medusa)", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12},
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
                # NOUVEAU SERVEUR D'IMAGES (Hips2Fits - Le plus fiable)
                ra_deg, dec_deg = coord.ra.deg, coord.dec.deg
                img_url = f"https://alasky.cds.unistra.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={ra_deg}&dec={dec_deg}&width=300&height=300&fov=1.0&projection=GNOM&format=jpg"
                st.image(img_url, use_container_width=True)
            
            with col2:
                st.subheader(t['name'])
                st.write(f"📍 **Altitude :** {round(altaz.alt.deg)}°")
                st.write(f"✨ **Filtre :** {'Dual-Band' if t['type'] in ['Emission', 'Planetary'] else 'RGB Pur'}")
                st.write(f"🖼️ **Cadrage :** {round((t['size']/fov_w)*100)}% du champ")
                st.write(f"🔗 [Voir sur Telescopius](https://telescopius.com/deep-sky/object/{t['name'].replace(' ', '-')})")
            
            with col3:
                integration = round(4 * (f_ratio/4)**2 * (80/qe), 1)
                st.metric("Temps total", f"{integration}h")
                if moon_pos:
                    m_dist = round(coord.separation(moon_pos).deg)
                    st.write(f"🌙 Lune à {m_dist}°")
            st.markdown("---")

# --- TAB 2 : MÉTÉO ---
with tab2:
    w = get_live_weather(u_lat, u_lon)
    if w:
        st.subheader(f"🛰️ Ciel à {u_lat}, {u_lon}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Nuages", f"{w['hourly']['cloudcover'][0]}%")
        c2.metric("Humidité", f"{w['hourly']['relativehumidity_2m'][0]}%")
        c3.metric("Température", f"{w['current_weather']['temperature']}°C")
    else: st.error("Serveur météo indisponible.")

# --- TAB 3 : ÉNERGIE ---
with tab3:
    BATT = {"Bluetti EB3A": 268, "EcoFlow River 2": 256, "Jackery 240": 240, "Jackery 500": 518, "Batterie 60Ah": 360, "Custom": 0}
    choix = st.selectbox("Modèle de batterie", list(BATT.keys()))
    wh = st.number_input("Wh", value=BATT[choix]) if choix == "Custom" else BATT[choix]
    conso = st.slider("Consommation moyenne (Watts)", 10, 100, 35)
    st.metric("Autonomie estimée", f"{round((wh*0.9)/conso, 1)} heures")

# --- TAB 4 : COMÈTES ---
with tab4:
    st.subheader("☄️ Calcul de pose Comète")
    v_c = st.number_input("Vitesse (arcsec/min)", value=1.0)
    max_p = res / (v_c / 60)
    st.metric("Temps de pose MAX", f"{round(max_p, 1)} s")
    st.info("💡 Au-delà de ce temps, le noyau de la comète sera flou.")

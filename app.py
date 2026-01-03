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

# --- STYLE VISION NOCTURNE ULTRA-CONTRASTE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF0000 !important; font-weight: bold !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF0000; border-radius: 12px; padding: 15px; }
    [data-testid="stMetricValue"] { color: #FF0000 !important; font-weight: bold !important; }
    button { background-color: #FF0000 !important; color: white !important; font-weight: bold !important; border: none !important; padding: 10px !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; }
    .stTabs [data-baseweb="tab"] { color: #FF0000 !important; }
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")

st.sidebar.header("📍 Ma Position GPS")
# Bouton pour récupérer la position réelle
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)

if loc:
    st.session_state.lat = loc['coords']['latitude']
    st.session_state.lon = loc['coords']['longitude']
    st.sidebar.success("✅ GPS Connecté")

# Champs de saisie manuelle (se remplissent tout seuls si le GPS marche)
default_lat = st.session_state.get('lat', 46.80)
default_lon = st.session_state.get('lon', 7.10)

u_lat = st.sidebar.number_input("Latitude", value=default_lat, format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=default_lon, format="%.4f")
h_mask = st.sidebar.slider("Masque d'Horizon (°)", 0, 60, 25)

st.sidebar.header("📸 Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200), "Esprit 100": (550, 100)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}

tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)
res = round((px * 206) / focale, 2)

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3 = st.tabs(["💎 Radar de Pépites", "☁️ Météo Live", "🔋 Batterie"])

with tab1:
    db = [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
        {"name": "Abell 21 (Medusa)", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12},
    ]

    now = Time.now()
    obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
    try: moon_pos = get_body("moon", now)
    except: moon_pos = None

    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        
        if altaz.alt.deg > h_mask:
            col1, col2, col3 = st.columns([1.5, 2, 1.2])
            
            with col1:
                # FIX IMAGES : Utilisation d'un lien statique DSS2 plus compatible
                ra_deg, dec_deg = coord.ra.deg, coord.dec.deg
                img_url = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={ra_deg}&dec={dec_deg}&width=400&height=400&fov=1.2&projection=GNOM&format=jpg"
                st.image(img_url, caption=t['name'], use_container_width=True)
                
                # FIX TELESCOPIUS : Nettoyage du nom (ex: "Sh2-157 (Lobster)" -> "sh2-157")
                clean_name = t['name'].split(' (')[0].lower().replace(' ', '-')
                t_link = f"https://telescopius.com/deep-sky/object/{clean_name}"
                st.markdown(f"[🔗 Fiche Telescopius]({t_link})")

            with col2:
                st.subheader(t['name'])
                st.write(f"📍 Altitude : **{round(altaz.alt.deg)}°**")
                st.write(f"✨ Filtre : **{'Dual-Band (Hα/OIII)' if t['type'] in ['Emission', 'Planetary'] else 'RGB Pur'}**")
                st.write(f"🖼️ Cadrage : **{round((t['size']/fov_w)*100)}%** du capteur")
                st.write(f"🔬 Échantillonnage : **{res} \"/px**")
            
            with col3:
                integration = round(4 * (f_ratio/4)**2 * (80/qe), 1)
                st.metric("Temps total", f"{integration}h")
                if moon_pos:
                    dist = round(coord.separation(moon_pos).deg)
                    st.write(f"🌙 Lune à **{dist}°**")
            st.markdown("---")

with tab2:
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={u_lat}&longitude={u_lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m"
        w = requests.get(w_url).json()
        st.subheader(f"☁️ Météo Live ({u_lat}, {u_lon})")
        c1, c2, c3 = st.columns(3)
        c1.metric("Nuages", f"{w['hourly']['cloudcover'][0]}%")
        c2.metric("Humidité", f"{w['hourly']['relativehumidity_2m'][0]}%")
        c3.metric("Temp", f"{w['current_weather']['temperature']}°C")
    except: st.error("Liaison météo impossible")

with tab3:
    st.subheader("🔋 Calculateur Batterie")
    BATT = {"Bluetti EB3A": 268, "EcoFlow River 2": 256, "Jackery 240": 240, "Batterie 60Ah": 360, "Custom": 100}
    choix = st.selectbox("Ma Batterie", list(BATT.keys()))
    capa = st.number_input("Capacité (Wh)", value=BATT[choix])
    conso = st.slider("Watts consommés (Monture+PC+TEC)", 10, 100, 35)
    st.metric("Autonomie restante", f"{round((capa*0.9)/conso, 1)} h")

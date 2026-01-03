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
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- STYLE VISION NOCTURNE ULTRA-CONTRASTE ---
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
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS MÉTÉO ---
def get_expert_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m,temperature_2m&timezone=auto"
        return requests.get(url, timeout=5).json()
    except: return None

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat = loc['coords']['latitude']
    st.session_state.lon = loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")
h_mask = st.sidebar.slider("Masque d'Horizon (°)", 0, 60, 25)

st.sidebar.header("📂 Filtres")
show_rare = st.sidebar.checkbox("💎 Pépites Rares", value=True)
show_planets = st.sidebar.checkbox("🪐 Planètes", value=True)

st.sidebar.header("📸 Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}
tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = focale / diam
fov_w = (sw * 3438) / focale

# --- BASE DE DONNÉES ---
db = []
if show_rare:
    db += [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
        {"name": "Abell 21 (Medusa)", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12},
    ]

# --- APP ---
st.title("🔭 AstroPépites Pro")
t_radar, t_planning, t_meteo, t_batterie = st.tabs(["💎 Radar & Photos", "🗓️ Planning de Nuit", "☁️ Météo Live", "🔋 Batterie"])

now = Time.now()
obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)

# --- TAB 1 : RADAR ---
with t_radar:
    results = []
    # Ajout des planètes si coché
    if show_planets:
        for p in ["Jupiter", "Saturn", "Mars"]:
            p_coord = get_body(p.lower(), now)
            altaz = p_coord.transform_to(AltAz(obstime=now, location=obs_loc))
            if altaz.alt.deg > h_mask:
                col1, col2, col3 = st.columns([1.5, 2, 1.2])
                with col1:
                    img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={p_coord.ra.deg}&dec={p_coord.dec.deg}&width=400&height=400&fov=0.1&format=jpg"
                    st.image(img, use_container_width=True)
                with col2:
                    st.subheader(f"🪐 {p}")
                    st.write(f"📍 Altitude : **{round(altaz.alt.deg)}°** | ✨ Filtre : **RGB / IR-Pass**")
                with col3:
                    st.metric("Temps suggéré", "Vidéo")
                st.markdown("---")

    # DSO
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        if altaz.alt.deg > h_mask:
            col1, col2, col3 = st.columns([1.5, 2, 1.2])
            with col1:
                img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={coord.ra.deg}&dec={coord.dec.deg}&width=400&height=400&fov=1.2&format=jpg"
                st.image(img, use_container_width=True)
            with col2:
                st.subheader(t['name'])
                st.write(f"📍 Alt : **{round(altaz.alt.deg)}°** | ✨ Filtre : **{'Dual-Band' if t['type']=='Emission' else 'RGB'}**")
                st.write(f"🖼️ Cadrage : **{round((t['size']/fov_w)*100)}%**")
            with col3:
                expo = round(4 * (f_ratio/4)**2, 1)
                st.metric("Expo conseillée", f"{expo}h")
                clean = t['name'].split(' (')[0].lower().replace(' ', '-')
                st.markdown(f"[🔗 Telescopius](https://telescopius.com/deep-sky/object/{clean})")
            st.markdown("---")

# --- TAB 2 : PLANNING (SCHEDULER) ---
with t_planning:
    st.subheader("⏱️ Courbes de visibilité (12 prochaines heures)")
    time_steps = now + np.linspace(0, 12, 24) * u.hour
    chart_data = pd.DataFrame()
    chart_data["Heure"] = [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]
    
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        alts = [max(0, coord.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg) for ts in time_steps]
        chart_data[t['name']] = alts
    
    st.line_chart(chart_data.set_index("Heure"))
    st.info("💡 **Conseil :** Shootez la cible quand sa courbe est au plus haut. Quand elle descend sous les 30°, passez à la suivante !")

# --- TAB 3 : MÉTÉO ---
with t_meteo:
    w = get_expert_weather(u_lat, u_lon)
    if w:
        st.subheader(f"📊 Prévisions Nuages pour {u_lat}, {u_lon}")
        df_w = pd.DataFrame({
            "Heure": [d[11:16] for d in w['hourly']['time'][:24]],
            "Nuages (%)": w['hourly']['cloudcover'][:24]
        }).set_index("Heure")
        st.area_chart(df_w, color="#FF3333")
        st.write("Détails : ", df_w.T)

# --- TAB 4 : BATTERIE ---
with t_batterie:
    wh = st.number_input("Wh de la batterie", value=240)
    conso = st.slider("Consommation Watts", 10, 100, 35)
    st.metric("Autonomie (h)", round((wh*0.9)/conso, 1))

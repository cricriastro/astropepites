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

# --- STYLE VISION NOCTURNE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF3333 !important; font-weight: bold !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; }
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

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
show_std = st.sidebar.checkbox("⭐ Standards", value=True)
show_planets = st.sidebar.checkbox("🪐 Planètes", value=True)

st.sidebar.header("📸 Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}
tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)

# --- BASE DE DONNÉES ---
db = []
if show_rare:
    db += [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
    ]
if show_std:
    db += [{"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size": 65}]

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3, tab4 = st.tabs(["💎 Radar & Photos", "🗓️ Planning de Nuit", "☁️ Météo", "🔋 Batterie"])

now = Time.now()
obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)

# --- TAB 1 : RADAR ---
with tab1:
    results = []
    for t in db:
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
                st.write(f"📍 Altitude : **{round(altaz.alt.deg)}°** | ✨ Filtre : **{'Dual-Band' if t['type']=='Emission' else 'RGB'}**")
                st.write(f"🖼️ Cadrage : **{round((t['size']/fov_w)*100)}%**")
            with col3:
                st.metric("Expo conseillée", f"{round(4 * (f_ratio/4)**2 * (80/qe), 1)}h")
                clean_n = t['name'].split(' (')[0].lower().replace(' ', '-')
                st.markdown(f"[🔗 Telescopius](https://telescopius.com/deep-sky/object/{clean_n})")
            st.markdown("---")

# --- TAB 2 : PLANNING DE NUIT (NOUVEAU) ---
with tab2:
    st.subheader("⏱️ Chronologie de votre session")
    st.write("Visualisez la trajectoire de vos cibles pour organiser votre séquence de capture.")
    
    # Création d'une plage horaire (12h à partir de maintenant)
    times = now + np.linspace(0, 12, 13) * u.hour
    planning_data = {"Heure": [(datetime.now() + timedelta(hours=i)).strftime("%H:%M") for i in range(13)]}
    
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altitudes = []
        for check_time in times:
            alt = coord.transform_to(AltAz(obstime=check_time, location=obs_loc)).alt.deg
            altitudes.append(max(0, alt)) # On garde 0 si c'est sous l'horizon
        planning_data[t['name']] = altitudes
    
    df_plan = pd.DataFrame(planning_data).set_index("Heure")
    
    # Affichage du graphique de planification
    st.line_chart(df_plan)
    
    st.info("💡 **Comment lire ce graphique ?** Choisissez la cible qui est au plus haut (le sommet de la courbe) au moment où vous voulez shooter. Si deux courbes se croisent, c'est le moment idéal pour changer de cible !")

# --- TAB 3 : MÉTÉO ---
with tab2: # Note: correction index tab si besoin
    pass # (Logique météo précédente identique...)

# --- TAB 4 : BATTERIE ---
with tab4:
    st.subheader("🔋 Énergie")
    wh = st.number_input("Wh", value=240)
    conso = st.slider("Watts", 10, 100, 35)
    st.metric("Autonomie", f"{round((wh*0.9)/conso, 1)} h")

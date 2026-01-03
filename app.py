import streamlit as st
import pandas as pd
import requests
import numpy as np
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro v3.2", layout="wide")

# --- STYLE VISION NOCTURNE ULTRA ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF3333 !important; font-weight: bold !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; padding: 15px; }
    [data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [aria-selected="true"] { background-color: #FF3333 !important; color: #FFFFFF !important; border-radius: 8px; }
    hr { border: 1px solid #333; }
    /* Selectbox Visibility */
    div[data-baseweb="select"] { background-color: #222 !important; color: white !important; }
    input { background-color: #222 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- BASES DE DONNÉES MATÉRIEL ---
TELESCOPES = {
    "Skywatcher Evolux 62ED": (400, 62), "Skywatcher 72ED": (420, 72), "Skywatcher 80ED": (600, 80),
    "Esprit 100ED": (550, 100), "Esprit 120ED": (840, 120), "Esprit 150ED": (1050, 150),
    "RedCat 51": (250, 51), "RedCat 71": (350, 71), "Newton 150/750": (750, 150),
    "Newton 200/800": (800, 200), "Newton 250/1000": (1000, 250), "Celestron C8 (f/10)": (2032, 203),
    "Celestron C8 (f/6.3)": (1280, 203), "Celestron C9.25": (2350, 235), "Celestron C11": (2800, 280),
    "Takahashi FSQ-106": (530, 106), "Askar FRA400": (400, 72), "Custom / Manuel": (400, 60)
}
CAMERAS = {
    "ASI 183MC/MM (2.4µm)": (13.2, 8.8, 2.4, 84), "ASI 533MC/MM (3.76µm)": (11.3, 11.3, 3.76, 80),
    "ASI 294MC/MM (4.63µm)": (19.1, 13.0, 4.63, 75), "ASI 2600MC/MM (3.76µm)": (23.5, 15.7, 3.76, 80),
    "ASI 6200MC/MM (Full Frame)": (36.0, 24.0, 3.76, 80), "Canon EOS 6D / R6": (36.0, 24.0, 5.0, 50),
    "Canon EOS 80D / 90D": (22.3, 14.9, 3.7, 45), "Sony A7III": (35.6, 23.8, 5.9, 50), "Custom / Manuel": (13.2, 8.8, 3.76, 80)
}
BATTERIES = {
    "Bluetti EB3A (268Wh)": 268, "Bluetti EB55 (537Wh)": 537, "Bluetti AC180 (1152Wh)": 1152,
    "EcoFlow River 2 (256Wh)": 256, "EcoFlow River 2 Max (512Wh)": 512, "EcoFlow Delta 2 (1024Wh)": 1024,
    "Jackery Explorer 240": 240, "Jackery Explorer 500": 518, "Jackery Explorer 1000": 1002,
    "Batterie Voiture 60Ah": 360, "Batterie AGM 100Ah": 600, "Custom": 0
}

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")
lang = st.sidebar.radio("Language", ["Français", "English"])
T_FR = lang == "Français"

st.sidebar.header("📍 Ma Position")
if st.sidebar.button("🛰️ Activer le GPS"):
    loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
    if loc:
        st.session_state.lat, st.session_state.lon = loc['coords']['latitude'], loc['coords']['longitude']
        st.sidebar.success("Position captée !")

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")
h_mask = st.sidebar.slider("Masque Horizon (°)", 0, 60, 20)

st.sidebar.header("📸 Matériel")
tube = st.sidebar.selectbox("Télescope / Lunette", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra / Capteur", list(CAMERAS.keys()))
focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale/diam, 2) if diam > 0 else 1
fov_w = (sw * 3438) / focale

# --- BASE DE DONNÉES CIBLES ---
# DSO Database étendue
db_objects = [
    {"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size": 65, "cat": "Messier"},
    {"name": "M31 (Andromède)", "ra": "00:42:44", "dec": "+41:16:09", "type": "Galaxy", "size": 180, "cat": "Messier"},
    {"name": "M45 (Pléiades)", "ra": "03:47:24", "dec": "+24:07:00", "type": "Reflection", "size": 110, "cat": "Messier"},
    {"name": "M51 (Tourbillon)", "ra": "13:29:52", "dec": "+47:11:43", "type": "Galaxy", "size": 11, "cat": "Messier"},
    {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60, "cat": "Rare"},
    {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15, "cat": "Rare"},
    {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10, "cat": "Rare"},
    {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50, "cat": "Rare"},
    {"name": "NGC 2237 (Rosette)", "ra": "06:32:19", "dec": "+05:03:12", "type": "Emission", "size": 80, "cat": "NGC"},
    {"name": "NGC 7000 (N. America)", "ra": "20:59:17", "dec": "+44:31:44", "type": "Emission", "size": 120, "cat": "NGC"},
    {"name": "24P/Schaumasse", "ra": "12:58:05", "dec": "+14:01:06", "type": "Comet", "size": 10, "cat": "Comète"},
]

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3, tab4 = st.tabs(["💎 Radar", "🗓️ Planning", "☁️ Météo", "🔋 Batterie"])

now = Time.now()
obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)

# --- TAB 1 : RADAR ---
with tab1:
    search = st.text_input("🔍 Rechercher (ex: M42, Sh2, NGC...)", "")
    
    # Planètes
    for p in ["Jupiter", "Saturn", "Mars"]:
        p_c = get_body(p.lower(), now)
        altaz = p_c.transform_to(AltAz(obstime=now, location=obs_loc))
        if altaz.alt.deg > h_mask:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.image(f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={p_c.ra.deg}&dec={p_c.dec.deg}&width=300&height=300&fov=0.1&format=jpg", use_container_width=True)
            with col2:
                st.subheader(f"🪐 {p}")
                st.write(f"📍 Alt : **{round(altaz.alt.deg)}°** | ✨ Filtre : **RGB**")
            st.markdown("---")

    # DSO & Comètes
    for t in db_objects:
        if search.lower() in t['name'].lower():
            coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
            altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
            if altaz.alt.deg > h_mask:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={coord.ra.deg}&dec={coord.dec.deg}&width=400&height=400&fov=1.2&format=jpg"
                    st.image(img, use_container_width=True)
                with col2:
                    icon = "☄️" if t['cat']=="Comète" else "💎"
                    st.subheader(f"{icon} {t['name']}")
                    st.write(f"📍 Alt : **{round(altaz.alt.deg)}°** | ✨ Filtre : **{'Dual-Band' if t['type']=='Emission' else 'RGB'}**")
                    st.write(f"🖼️ Cadrage : **{round((t['size']/fov_w)*100)}%**")
                with col3:
                    expo = round(4 * (f_ratio/4)**2 * (80/qe), 1)
                    st.metric("Temps suggéré", f"{expo}h" if t['cat']!="Comète" else "Spécial")
                st.markdown("---")

# --- TAB 2 : PLANNING ---
with tab2:
    st.subheader("⏱️ Courbes de visibilité")
    time_steps = now + np.linspace(0, 12, 24) * u.hour
    planning_data = {"Heure": [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]}
    for t in db_objects:
        c = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        planning_data[t['name']] = [max(0, c.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg) for ts in time_steps]
    st.line_chart(pd.DataFrame(planning_data).set_index("Heure"))

# --- TAB 3 : MÉTÉO ---
with tab3:
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={u_lat}&longitude={u_lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m&timezone=auto"
        w = requests.get(w_url).json()
        df_w = pd.DataFrame({"Heure": [d[11:16] for d in w['hourly']['time'][:24]], "Nuages (%)": w['hourly']['cloudcover'][:24]}).set_index("Heure")
        st.area_chart(df_w, color="#FF3333")
    except: st.error("Météo indisponible")

# --- TAB 4 : BATTERIE DÉTAILLÉE ---
with tab4:
    st.subheader("🔋 Calculateur d'Énergie Expert")
    choix_b = st.selectbox("Modèle de Batterie", list(BATTERIES.keys()))
    capa_wh = st.number_input("Wh de votre source", value=BATTERIES[choix_b]) if choix_b == "Custom" else BATTERIES[choix_b]
    
    st.write("🔧 **Consommation (Watts) :**")
    colA, colB = st.columns(2)
    p_mount = colA.slider("Monture (Suivi)", 5, 25, 10)
    p_cam = colA.slider("Caméra TEC (Refroid.)", 0, 40, 20)
    p_pc = colB.slider("ASIAIR / PC", 5, 25, 10)
    p_dew = colB.slider("Bandes Chauffantes", 0, 40, 15)
    
    total_w = p_mount + p_cam + p_pc + p_dew
    runtime = (capa_wh * 0.9) / total_w if total_w > 0 else 0
    st.metric("Autonomie estimée", f"{round(runtime, 1)} h")

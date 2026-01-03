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
    h1, h2, h3 { color: #FF3333 !important; font-weight: bold !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; }
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS TECHNIQUES ---
def get_live_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m,temperature_2m&timezone=auto"
        return requests.get(url, timeout=5).json()
    except: return None

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")

# GPS automatique
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat = loc['coords']['latitude']
    st.session_state.lon = loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")
h_mask = st.sidebar.slider("Masque d'Horizon (°)", 0, 60, 25)

st.sidebar.header("📂 Filtres de Cibles")
show_rare = st.sidebar.checkbox("💎 Pépites Rares (Sh2, vdB, Arp)", value=True)
show_std = st.sidebar.checkbox("⭐ Standards (Messier, NGC)", value=True)
show_planets = st.sidebar.checkbox("🪐 Planètes", value=True)

st.sidebar.header("📸 Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200), "C8": (2032, 203)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}

tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)

# --- BASE DE DONNÉES ---
db_dso = []
if show_rare:
    db_dso += [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60, "cat": "Rare"},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15, "cat": "Rare"},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10, "cat": "Rare"},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50, "cat": "Rare"},
    ]
if show_std:
    db_dso += [
        {"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size": 65, "cat": "Standard"},
        {"name": "M31 (Andromède)", "ra": "00:42:44", "dec": "+41:16:09", "type": "Galaxy", "size": 180, "cat": "Standard"},
        {"name": "M51 (Tourbillon)", "ra": "13:29:52", "dec": "+47:11:43", "type": "Galaxy", "size": 11, "cat": "Standard"},
        {"name": "NGC 2237 (Rosette)", "ra": "06:32:19", "dec": "+05:03:12", "type": "Emission", "size": 80, "cat": "Standard"},
    ]

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3 = st.tabs(["💎 Radar de Cibles", "☁️ Prévisions Ciel", "🔋 Énergie"])

with tab1:
    now = Time.now()
    obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
    
    results = []
    
    # 1. Traitement des Planètes
    if show_planets:
        for p_name in ["Mars", "Jupiter", "Saturn", "Venus"]:
            p_coord = get_body(p_name.lower(), now)
            altaz = p_coord.transform_to(AltAz(obstime=now, location=obs_loc))
            if altaz.alt.deg > h_mask:
                results.append({
                    "Aperçu": f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={p_coord.ra.deg}&dec={p_coord.dec.deg}&width=300&height=300&fov=0.1&format=jpg",
                    "Nom": f"🪐 {p_name}",
                    "Altitude": f"{round(altaz.alt.deg)}°",
                    "Filtre": "RGB / IR-Pass (Lucky Imaging)",
                    "Expo": "Vidéo Haute Vitesse",
                    "Cat": "Planète",
                    "ra": p_coord.ra.to_string(unit=u.hourangle, sep=':'), 
                    "dec": p_coord.dec.to_string(unit=u.deg, sep=':')
                })

    # 2. Traitement des DSO
    for t in db_dso:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        if altaz.alt.deg > h_mask:
            integration = round(4 * (f_ratio/4)**2 * (80/80), 1) # Simplifié pour l'exemple
            results.append({
                "Aperçu": f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={coord.ra.deg}&dec={coord.dec.deg}&width=300&height=300&fov=1.2&format=jpg",
                "Nom": t['name'],
                "Altitude": f"{round(altaz.alt.deg)}°",
                "Filtre": "Dual-Band" if t['type']=="Emission" else "RGB Pur",
                "Expo": f"{integration}h",
                "Cat": t['cat'],
                "ra": t['ra'], "dec": t['dec']
            })

    if results:
        for r in results:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1: st.image(r["Aperçu"], use_container_width=True)
            with col2:
                st.subheader(r["Nom"])
                st.write(f"📂 **Catégorie :** {r['Cat']} | 📍 **Alt :** {r['Altitude']}")
                st.write(f"✨ **Filtre conseillé :** {r['Filtre']}")
            with col3:
                st.metric("Temps suggéré", r["Expo"])
                clean_name = r['Nom'].replace('🪐 ', '').split(' (')[0].lower().replace(' ', '-')
                st.markdown(f"[🔗 Telescopius](https://telescopius.com/deep-sky/object/{clean_name})")
            st.markdown("---")
    else:
        st.warning("Aucune cible dans vos filtres au-dessus de l'horizon.")

with tab2:
    w = get_live_weather(u_lat, u_lon)
    if w:
        df_w = pd.DataFrame({
            "Heure": [d[11:16] for d in w['hourly']['time'][:24]],
            "Nuages (%)": w['hourly']['cloudcover'][:24],
            "Temp (°C)": w['hourly']['temperature_2m'][:24]
        }).set_index("Heure")
        st.area_chart(df_w["Nuages (%)"], color="#FF3333")
        st.dataframe(df_w.T)

with tab3:
    wh = st.number_input("Capacité Batterie (Wh)", value=240)
    conso = st.slider("Watts", 10, 100, 35)
    st.metric("Autonomie", f"{round((wh*0.9)/conso, 1)} h")

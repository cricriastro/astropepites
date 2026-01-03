import streamlit as st
import pandas as pd
import numpy as np
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro v3.4", layout="wide")

# --- STYLE VISION NOCTURNE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF3333 !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; padding: 10px; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; font-weight: bold !important; }
    hr { border: 1px solid #333; }
    .stButton>button { background-color: #330000 !important; color: white !important; border: 1px solid #FF3333 !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION DIRECTION CARDINALE ---
def get_cardinal(az):
    if 315 <= az or az < 45: return "Nord (N)"
    if 45 <= az < 135: return "Est (E)"
    if 135 <= az < 225: return "Sud (S)"
    if 225 <= az < 315: return "Ouest (O)"
    return "N/A"

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat, st.session_state.lon = loc['coords']['latitude'], loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")

# --- NOUVEAU : MASQUE D'HORIZON EXPERT ---
with st.sidebar.expander("🌲 Mon Masque d'Horizon"):
    st.write("Réglez la hauteur de vos obstacles (arbres, murs...) :")
    mask_n = st.slider("Nord (315°-45°)", 0, 90, 20)
    mask_e = st.slider("Est (45°-135°)", 0, 90, 20)
    mask_s = st.slider("Sud (135°-225°)", 0, 90, 20)
    mask_w = st.slider("Ouest (225°-315°)", 0, 90, 20)

def get_horizon_limit(az):
    if 315 <= az or az < 45: return mask_n
    if 45 <= az < 135: return mask_e
    if 135 <= az < 225: return mask_s
    if 225 <= az < 315: return mask_w
    return 0

st.sidebar.header("📸 Matériel")
tube = st.sidebar.selectbox("Télescope", ["Evolux 62ED", "RedCat 51", "Newton 200/800", "Custom"])
cam = st.sidebar.selectbox("Caméra", ["ASI 183MC", "ASI 2600MC", "ASI 533MC"])
focale, diam = {"Evolux 62ED":(400,62), "RedCat 51":(250,51), "Newton 200/800":(800,200), "Custom":(400,60)}[tube]
sw, sh, px, qe = {"ASI 183MC":(13.2, 8.8, 2.4, 84), "ASI 2600MC":(23.5, 15.7, 3.76, 80), "ASI 533MC":(11.3, 11.3, 3.76, 80)}[cam]

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3 = st.tabs(["💎 Radar & Visibilité", "☁️ Météo", "🔋 Énergie"])

now = Time.now()
obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
try: moon_pos = get_body("moon", now)
except: moon_pos = None

db = [
    {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
    {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
    {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
    {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
]

with tab1:
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz_now = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        
        limit = get_horizon_limit(altaz_now.az.deg)
        is_visible = "✅" if altaz_now.alt.deg > limit else "❌ CACHÉ"
        
        col1, col2, col3 = st.columns([1.5, 2, 1.2])
        
        with col1:
            img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={coord.ra.deg}&dec={coord.dec.deg}&width=400&height=400&fov=1.2&format=jpg"
            st.image(img, use_container_width=True)
        
        with col2:
            st.subheader(f"{t['name']} {is_visible}")
            st.write(f"📍 Actuellement : **{round(altaz_now.alt.deg)}°** au **{get_cardinal(altaz_now.az.deg)}**")
            
            with st.expander("📊 COURBE DE VISIBILITÉ & DIRECTIONS"):
                times = now + np.linspace(0, 12, 24) * u.hour
                hours = [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]
                
                alts, dirs = [], []
                for ts in times:
                    aa = coord.transform_to(AltAz(obstime=ts, location=obs_loc))
                    alts.append(max(0, aa.alt.deg))
                    dirs.append(get_cardinal(aa.az.deg))
                
                st.line_chart(pd.DataFrame({"Altitude (°)": alts}, index=hours), color="#FF3333")
                
                # Tableau des directions pour le planning
                st.write("**Planning des directions :**")
                df_dir = pd.DataFrame({"Heure": hours[::2], "Direction": dirs[::2], "Hauteur": [f"{round(a)}°" for a in alts[::2]]})
                st.table(df_dir)

        with col3:
            integration = round(4 * ((focale/diam)/4)**2 * (80/qe), 1)
            st.metric("Temps suggéré", f"{integration}h")
            st.write(f"🖼️ Cadrage : {round((t['size']/((sw*3438)/focale))*100)}%")
            clean_n = t['name'].split(' (')[0].lower().replace(' ', '-')
            st.markdown(f"[🔗 Fiche Telescopius](https://telescopius.com/deep-sky/object/{clean_n})")
        st.markdown("---")

# Les autres onglets Météo/Batterie restent identiques

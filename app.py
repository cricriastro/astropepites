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
st.set_page_config(page_title="AstroPépites Pro v3.3", layout="wide")

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
    /* Style pour les boutons de visibilité */
    .stButton>button { background-color: #330000 !important; color: white !important; border: 1px solid #FF3333 !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat, st.session_state.lon = loc['coords']['latitude'], loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")
h_mask = st.sidebar.slider("Mon Horizon (Altitude min °)", 0, 60, 25)

st.sidebar.header("📸 Matériel")
tube = st.sidebar.selectbox("Télescope", ["Evolux 62ED", "RedCat 51", "Newton 200/800", "Esprit 100", "C8", "Custom"])
cam = st.sidebar.selectbox("Caméra", ["ASI 183MC", "ASI 2600MC", "ASI 533MC", "Canon EOS R"])

# Dictionnaires techniques
TELS = {"Evolux 62ED":(400,62), "RedCat 51":(250,51), "Newton 200/800":(800,200), "Esprit 100":(550,100), "C8":(1280,203), "Custom":(400,60)}
CAMS = {"ASI 183MC":(13.2, 8.8, 2.4, 84), "ASI 2600MC":(23.5, 15.7, 3.76, 80), "ASI 533MC":(11.3, 11.3, 3.76, 80), "Canon EOS R":(36.0, 24.0, 5.3, 50)}

focale, diam = TELS[tube]
sw, sh, px, qe = CAMS[cam]
f_ratio = focale / diam
fov_w = (sw * 3438) / focale

# --- BASE DE DONNÉES ---
db = [
    {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
    {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
    {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
    {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
    {"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size": 65},
    {"name": "24P/Schaumasse", "ra": "12:58:05", "dec": "+14:01:06", "type": "Comet", "size": 10},
]

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3 = st.tabs(["💎 Radar de Cibles", "☁️ Météo Expert", "🔋 Énergie"])

now = Time.now()
obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)

with tab1:
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        
        if altaz.alt.deg > -10: # On affiche même si c'est un peu bas pour prévoir
            col1, col2, col3 = st.columns([1.5, 2, 1.2])
            
            with col1:
                img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={coord.ra.deg}&dec={coord.dec.deg}&width=400&height=400&fov=1.2&format=jpg"
                st.image(img, use_container_width=True)
            
            with col2:
                st.subheader(t['name'])
                st.write(f"📍 Altitude actuelle : **{round(altaz.alt.deg)}°**")
                st.write(f"✨ Filtre : **{'Dual-Band' if t['type']=='Emission' else 'RGB'}**")
                
                # LA NOUVELLE FONCTION : Graphique de visibilité individuel
                with st.expander("📊 VOIR LA COURBE DE VISIBILITÉ"):
                    # Calcul sur 12 heures
                    times = now + np.linspace(0, 12, 24) * u.hour
                    hours = [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]
                    alts = [max(0, coord.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg) for ts in times]
                    
                    df_v = pd.DataFrame({"Heure": hours, "Altitude (°)": alts}).set_index("Heure")
                    st.line_chart(df_v, color="#FF3333")
                    st.caption(f"Le point le plus haut est le passage au Méridien pour votre position.")

            with col3:
                expo = round(4 * (f_ratio/4)**2 * (80/qe), 1)
                st.metric("Temps total estimé", f"{expo}h")
                st.write(f"🖼️ Cadrage : {round((t['size']/fov_w)*100)}%")
                clean = t['name'].split(' (')[0].lower().replace(' ', '-')
                st.markdown(f"[🔗 Voir sur Telescopius](https://telescopius.com/deep-sky/object/{clean})")
            
            st.markdown("---")

with tab2:
    st.subheader("☁️ Prévisions Ciel")
    url = f"https://api.open-meteo.com/v1/forecast?latitude={u_lat}&longitude={u_lon}&hourly=cloudcover,relativehumidity_2m&current_weather=true&timezone=auto"
    try:
        w = requests.get(url).json()
        df_w = pd.DataFrame({"Heure": [d[11:16] for d in w['hourly']['time'][:24]], "Nuages (%)": w['hourly']['cloudcover'][:24]}).set_index("Heure")
        st.area_chart(df_w, color="#FF3333")
    except: st.error("Météo indisponible")

with tab3:
    st.subheader("🔋 Énergie")
    capa = st.number_input("Batterie (Wh)", value=240)
    conso = st.slider("Watts", 10, 100, 35)
    st.metric("Autonomie", f"{round((capa*0.9)/conso, 1)} h")

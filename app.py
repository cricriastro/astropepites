import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro v3.5", layout="wide")

# --- STYLE NOCTURNE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF3333 !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; }
    [data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; font-weight: bold !important; }
    hr { border: 1px solid #333; }
    /* Style pour les boutons de sélection */
    .stButton>button { border: 1px solid #FF3333 !important; width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat, st.session_state.lon = loc['coords']['latitude'], loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")

# --- MASQUE D'HORIZON VISUEL (STYLE ASIAIR) ---
st.sidebar.header("🌲 Masque d'Horizon")
with st.sidebar.expander("Régler les obstacles", expanded=False):
    mN = st.slider("Nord", 0, 90, 20)
    mNE = st.slider("Nord-Est", 0, 90, 20)
    mE = st.slider("Est", 0, 90, 25)
    mSE = st.slider("Sud-Est", 0, 90, 30)
    mS = st.slider("Sud", 0, 90, 20)
    mSW = st.slider("Sud-Ouest", 0, 90, 20)
    mO = st.slider("Ouest", 0, 90, 25)
    mNO = st.slider("Nord-Ouest", 0, 90, 20)

# Création du graphique radar pour la boussole
mask_values = [mN, mNE, mE, mSE, mS, mSW, mO, mNO]
angles = np.linspace(0, 2*np.pi, 8, endpoint=False).tolist()
# On ferme la boucle du graphique
mask_plot = mask_values + [mask_values[0]]
angles_plot = angles + [angles[0]]

fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
# Zone rouge (obstruée)
ax.fill(angles_plot, mask_plot, color='red', alpha=0.3)
# Zone verte (ciel libre)
ax.fill_between(angles_plot, mask_plot, 90, color='green', alpha=0.2)
ax.set_ylim(0, 90)
ax.set_yticks([30, 60])
ax.set_yticklabels([])
ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'O', 'NO'], color='white', fontsize=8)
ax.patch.set_facecolor('black')
fig.patch.set_facecolor('black')
st.sidebar.pyplot(fig)

def get_horizon_limit(az):
    idx = int(((az + 22.5) % 360) // 45)
    return mask_values[idx]

# --- MATÉRIEL ---
st.sidebar.header("📸 Matériel")
tube = st.sidebar.selectbox("Télescope", ["Evolux 62ED", "Esprit 100", "RedCat 51", "Newton 200/800", "C8"])
cam = st.sidebar.selectbox("Caméra", ["ASI 183MC", "ASI 2600MC", "ASI 533MC", "Canon EOS R"])
TELS = {"Evolux 62ED":(400,62), "Esprit 100":(550,100), "RedCat 51":(250,51), "Newton 200/800":(800,200), "C8":(1280,203)}
CAMS = {"ASI 183MC":(13.2, 8.8, 2.4, 84), "ASI 2600MC":(23.5, 15.7, 3.76, 80), "ASI 533MC":(11.3, 11.3, 3.76, 80), "Canon EOS R":(36, 24, 5.3, 50)}
focale, diam = TELS[tube]
sw, sh, px, qe = CAMS[cam]

# --- BASE DE DONNÉES ÉTENDUE ---
db = [
    {"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size": 65},
    {"name": "M31 (Andromède)", "ra": "00:42:44", "dec": "+41:16:09", "type": "Galaxy", "size": 180},
    {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
    {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
    {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
    {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
    {"name": "NGC 2237 (Rosette)", "ra": "06:32:19", "dec": "+05:03:12", "type": "Emission", "size": 80},
    {"name": "IC 1805 (Heart)", "ra": "02:32:42", "dec": "+61:27:00", "type": "Emission", "size": 150},
]

# --- APP ---
st.title("🔭 AstroPépites Pro v3.5")
t_radar, t_meteo, t_batterie = st.tabs(["💎 Radar & Planning", "☁️ Météo Live", "🔋 Énergie"])

now = Time.now()
obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
try: moon_pos = get_body("moon", now)
except: moon_pos = None

with t_radar:
    # Système d'accordéon forcé : on choisit une cible pour voir les détails
    st.write("### 🎯 Analyse des cibles")
    selected_target_name = st.selectbox("🎯 Choisir une cible pour voir son planning détaillé :", [o['name'] for o in db])

    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        limit = get_horizon_limit(altaz.az.deg)
        visible = altaz.alt.deg > limit
        
        col1, col2, col3 = st.columns([1.5, 2, 1.2])
        with col1:
            img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={coord.ra.deg}&dec={coord.dec.deg}&width=400&height=400&fov=1.2&format=jpg"
            st.image(img, use_container_width=True)
        with col2:
            status = "✅ DÉGAGÉ" if visible else "❌ MASQUÉ"
            st.subheader(f"{t['name']} {status}")
            st.write(f"📍 Altitude : **{round(altaz.alt.deg)}°** | ✨ Filtre : **{'Dual-Band' if t['type']=='Emission' else 'RGB'}**")
            
            # Affichage du planning UNIQUEMENT si sélectionné (effet accordéon)
            if t['name'] == selected_target_name:
                st.write("---")
                st.write("**📈 Courbe de visibilité (12h) :**")
                times = now + np.linspace(0, 12, 24) * u.hour
                hours = [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]
                alts = [max(0, coord.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg) for ts in times]
                st.line_chart(pd.DataFrame({"Altitude": alts}, index=hours), color="#FF3333")
                
        with col3:
            expo = round(4 * ((focale/diam)/4)**2 * (80/qe), 1)
            st.metric("Temps suggéré", f"{expo}h")
            st.write(f"🖼️ Cadrage : {round((t['size']/((sw*3438)/focale))*100)}%")
            if moon_pos:
                st.write(f"🌙 Lune à {round(coord.separation(moon_pos).deg)}°")
        st.markdown("---")

# Les onglets Météo et Batterie restent identiques

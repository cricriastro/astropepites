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
import math

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro v4.1", layout="wide")

# --- STYLE VISION NOCTURNE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF3333 !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; }
    [data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; font-weight: bold !important; }
    .mosaic-alert { background-color: #331a00; border: 1px dashed #FF8800; padding: 10px; border-radius: 10px; color: #FF8800 !important; font-weight: bold; }
    .boost-box { background-color: #001a33; border: 1px solid #0088FF; padding: 5px 10px; border-radius: 5px; color: #0088FF !important; font-size: 0.9rem; margin-top: 5px; }
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- GPS ---
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat, st.session_state.lon = loc['coords']['latitude'], loc['coords']['longitude']

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")

# --- BOUSSOLE D'HORIZON ---
st.sidebar.header("🌲 Masque d'Horizon")
with st.sidebar.expander("Réglage des obstacles", expanded=False):
    mN = st.slider("Nord", 0, 90, 20); mNE = st.slider("NE", 0, 90, 20)
    mE = st.slider("Est", 0, 90, 20); mSE = st.slider("SE", 0, 90, 20)
    mS = st.slider("Sud", 0, 90, 20); mSW = st.slider("SW", 0, 90, 20)
    mO = st.slider("Ouest", 0, 90, 20); mNO = st.slider("NO", 0, 90, 20)

mask_values = [mN, mNE, mE, mSE, mS, mSW, mO, mNO]
angles = np.linspace(0, 2*np.pi, 8, endpoint=False).tolist()
fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
ax.fill(angles + [angles[0]], mask_values + [mask_values[0]], color='red', alpha=0.4)
ax.fill_between(angles + [angles[0]], mask_values + [mask_values[0]], 90, color='green', alpha=0.2)
ax.set_yticklabels([]); ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'O', 'NO'], color='white', fontsize=8)
ax.patch.set_facecolor('black'); fig.patch.set_facecolor('black')
st.sidebar.pyplot(fig)

def get_horizon_limit(az):
    idx = int(((az + 22.5) % 360) // 45)
    return mask_values[idx]

# --- MATÉRIEL ---
st.sidebar.header("📸 Matériel")
TELS = {"Evolux 62ED":(400,62), "Esprit 100":(550,100), "RedCat 51":(250,51), "Newton 200/800":(800,200), "C8":(1280,203)}
CAMS = {"ASI 183MC":(13.2, 8.8, 2.4, 84), "ASI 2600MC":(23.5, 15.7, 3.76, 80), "ASI 533MC":(11.3, 11.3, 3.76, 80)}
tube = st.sidebar.selectbox("Télescope", list(TELS.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMS.keys()))
focale, diam = TELS[tube]; sw, sh, px, qe = CAMS[cam]
f_ratio = focale / diam
fov_w = (sw * 3438) / focale
fov_h = (sh * 3438) / focale

# --- BASE DE DONNÉES CIBLES ---
db = [
    {"name": "M31 (Andromède)", "ra": "00:42:44", "dec": "+41:16:09", "type": "Galaxy", "size_w": 180, "size_h": 60},
    {"name": "M33 (Triangle)", "ra": "01:33:50", "dec": "+30:39:37", "type": "Galaxy", "size_w": 70, "size_h": 40},
    {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size_w": 60, "size_h": 50},
    {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size_w": 15, "size_h": 15},
    {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size_w": 10, "size_h": 8},
    {"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size_w": 65, "size_h": 60},
]

# --- APP ---
st.title("🔭 AstroPépites Pro v4.1")
t_radar, t_meteo, t_batt = st.tabs(["💎 Radar & Cibles", "☁️ Météo Live", "🔋 Énergie"])

now = Time.now(); obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
try: moon_pos = get_body("moon", now)
except: moon_pos = None

with t_radar:
    search = st.text_input("🔍 Rechercher une cible...", "")
    targets_to_show = [t for t in db if search.lower() in t['name'].lower()]
    selected_target = st.selectbox("🎯 Cible active (pour planning) :", ["Toutes"] + [o['name'] for o in targets_to_show])

    for t in targets_to_show:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        limit = get_horizon_limit(altaz.az.deg)
        visible = altaz.alt.deg > limit
        
        col1, col2, col3 = st.columns([1.5, 2, 1.2])
        with col1:
            img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={coord.ra.deg}&dec={coord.dec.deg}&width=400&height=400&fov=1.2&format=jpg"
            st.image(img, use_container_width=True)
        with col2:
            status = "✅ DÉGAGÉ" if visible else f"❌ MASQUÉ (<{limit}°)"
            st.subheader(f"{t['name']} {status}")
            st.write(f"📍 Alt : **{round(altaz.alt.deg)}°**")
            
            # --- LOGIQUE FILTRE EXPERT ---
            if t['type'] == "Emission":
                filter_rec = "🔴 Dual-Band (HOO)"
            elif t['type'] == "Galaxy":
                filter_rec = "⚪ RGB"
                st.markdown('<div class="boost-box">🚀 Expert Boost : Ajoutez des poses en H-Alpha pour faire ressortir les nébuleuses rouges dans les bras !</div>', unsafe_allow_html=True)
            elif t['type'] == "Reflection":
                filter_rec = "🌈 RGB Pur (Pas de filtre sélectif)"
            else:
                filter_rec = "RGB"
            
            st.write(f"✨ Filtre conseillé : **{filter_rec}**")

            if selected_target == t['name'] or selected_target == "Toutes":
                cadrage = round((t['size_w'] / fov_w) * 100)
                if cadrage > 90:
                    pw, ph = math.ceil(t['size_w']/(fov_w*0.8)), math.ceil(t['size_h']/(fov_h*0.8))
                    st.markdown(f'<div class="mosaic-alert">⚠️ MOSAÏQUE CONSEILLÉE : {pw} x {ph} panneaux</div>', unsafe_allow_html=True)
                times = now + np.linspace(0, 12, 24) * u.hour
                hours = [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]
                alts = [max(0, coord.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg) for ts in times]
                st.line_chart(pd.DataFrame({"Altitude": alts}, index=hours), color="#FF3333")
        with col3:
            st.metric("Temps suggéré", f"{round(4 * (f_ratio/4)**2 * (80/qe), 1)}h")
            if moon_pos: st.write(f"🌙 Lune à {round(coord.separation(moon_pos).deg)}°")
            st.markdown(f"[🔗 Telescopius](https://telescopius.com/deep-sky/object/{t['name'].split(' (')[0].lower().replace(' ', '-')})")
        st.markdown("---")

# Météo et Batterie identiques...

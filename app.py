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

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro v3.9", layout="wide")

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
    div[data-testid="stExpander"] { background-color: #0a0a0a; border: 1px solid #333; }
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR : GPS & BOUSSOLE ---
st.sidebar.title("🔭 AstroPépites Pro")

st.sidebar.header("📍 Ma Position")
if st.sidebar.button("🛰️ Capturer ma position GPS"):
    loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
    if loc:
        st.session_state.lat, st.session_state.lon = loc['coords']['latitude'], loc['coords']['longitude']
        st.sidebar.success("Position captée !")

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")

# BOUSSOLE ASIAIR
st.sidebar.header("🌲 Masque d'Horizon")
with st.sidebar.expander("Réglage des obstacles", expanded=False):
    mN = st.slider("Nord", 0, 90, 15); mNE = st.slider("NE", 0, 90, 15)
    mE = st.slider("Est", 0, 90, 20); mSE = st.slider("SE", 0, 90, 30)
    mS = st.slider("Sud", 0, 90, 15); mSW = st.slider("SW", 0, 90, 15)
    mO = st.slider("Ouest", 0, 90, 20); mNO = st.slider("NO", 0, 90, 15)

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

# --- FILTRES CATALOGUES ---
st.sidebar.header("📂 Catalogues")
f_rare = st.sidebar.checkbox("💎 Pépites (Sh2, vdB, Arp)", value=True)
f_messier = st.sidebar.checkbox("⭐ Messier", value=True)
f_ngc = st.sidebar.checkbox("🌌 NGC / IC", value=True)
f_planets = st.sidebar.checkbox("🪐 Planètes", value=True)

# --- MATÉRIEL ---
st.sidebar.header("📸 Mon Matériel")
TELS = {"Evolux 62ED":(400,62), "Esprit 100":(550,100), "RedCat 51":(250,51), "Newton 200/800":(800,200), "C8":(1280,203)}
CAMS = {"ASI 183MC":(13.2, 8.8, 2.4, 84), "ASI 2600MC":(23.5, 15.7, 3.76, 80), "ASI 533MC":(11.3, 11.3, 3.76, 80)}
tube = st.sidebar.selectbox("Télescope", list(TELS.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMS.keys()))
focale, diam = TELS[tube]; sw, sh, px, qe = CAMS[cam]
f_ratio = focale / diam
fov_w = (sw * 3438) / focale
fov_h = (sh * 3438) / focale

# --- BASE DE DONNÉES ---
db = []
if f_messier:
    db += [{"name": "M31 (Andromède)", "ra": "00:42:44", "dec": "+41:16:09", "type": "Galaxy", "size_w": 180, "size_h": 60, "cat": "Messier"},
           {"name": "M42 (Orion)", "ra": "05:35:17", "dec": "-05:23:28", "type": "Emission", "size_w": 65, "size_h": 60, "cat": "Messier"}]
if f_rare:
    db += [{"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size_w": 60, "size_h": 50, "cat": "Rare"},
           {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size_w": 15, "size_h": 15, "cat": "Rare"}]
if f_ngc:
    db += [{"name": "NGC 2237 (Rosette)", "ra": "06:32:19", "dec": "+05:03:12", "type": "Emission", "size_w": 80, "size_h": 80, "cat": "NGC"}]

# --- APP ---
st.title("🔭 AstroPépites Pro v3.9")
t_radar, t_meteo, t_batt = st.tabs(["💎 Radar & Cibles", "☁️ Météo Live", "🔋 Énergie"])

now = Time.now(); obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
try: moon_pos = get_body("moon", now)
except: moon_pos = None

with t_radar:
    search = st.text_input("🔍 Rechercher une cible...", "")
    
    # Affichage des planètes en haut si coché
    if f_planets:
        for p in ["Jupiter", "Saturn", "Mars"]:
            p_c = get_body(p.lower(), now)
            altaz = p_c.transform_to(AltAz(obstime=now, location=obs_loc))
            if altaz.alt.deg > h_mask:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1: st.image(f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={p_c.ra.deg}&dec={p_c.dec.deg}&width=300&height=300&fov=0.1&format=jpg", use_container_width=True)
                with col2: st.subheader(f"🪐 {p} (Planète)"); st.write(f"📍 Altitude : **{round(altaz.alt.deg)}°**")
                st.markdown("---")

    # Affichage de la liste des cibles filtrées
    for t in db:
        if search.lower() not in t['name'].lower(): continue
        
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
            st.write(f"📍 Alt : **{round(altaz.alt.deg)}°** | ✨ Filtre : **{'Dual-Band' if t['type']=='Emission' else 'RGB'}**")
            
            with st.expander("📈 VOIR LE PLANNING & MOSAÏQUE"):
                # Calcul Mosaïque
                cadrage = round((t['size_w'] / fov_w) * 100)
                if cadrage > 90:
                    pw = math.ceil(t['size_w'] / (fov_w * 0.8))
                    ph = math.ceil(t['size_h'] / (fov_h * 0.8))
                    st.markdown(f'<div class="mosaic-alert">⚠️ MOSAÏQUE CONSEILLÉE : {pw} x {ph} panneaux</div>', unsafe_allow_html=True)
                
                # Courbe de visibilité
                times = now + np.linspace(0, 12, 24) * u.hour
                hours = [(datetime.now() + timedelta(hours=i*0.5)).strftime("%H:%M") for i in range(24)]
                alts = [max(0, coord.transform_to(AltAz(obstime=ts, location=obs_loc)).alt.deg) for ts in times]
                st.line_chart(pd.DataFrame({"Altitude": alts}, index=hours), color="#FF3333")

        with col3:
            st.metric("Temps total", f"{round(4 * (f_ratio/4)**2 * (80/qe), 1)}h")
            st.write(f"🌙 Lune à {round(coord.separation(moon_pos).deg) if moon_pos else 'N/A'}°")
            clean_n = t['name'].split(' (')[0].lower().replace(' ', '-')
            st.markdown(f"[🔗 Telescopius](https://telescopius.com/deep-sky/object/{clean_n})")
        st.markdown("---")

with t_meteo:
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={u_lat}&longitude={u_lon}&current_weather=true&hourly=cloudcover&timezone=auto"
        w = requests.get(w_url).json()
        st.subheader(f"☁️ Prévisions Nuages (%)")
        df_w = pd.DataFrame({"Heure": [d[11:16] for d in w['hourly']['time'][:24]], "Nuages": w['hourly']['cloudcover'][:24]}).set_index("Heure")
        st.area_chart(df_w, color="#FF3333")
    except: st.error("Météo indisponible")

with t_batt:
    st.subheader("🔋 Consommation Batterie")
    wh = st.number_input("Wh de la batterie", value=240)
    c1, c2 = st.columns(2)
    p_mount = c1.slider("Monture", 5, 25, 10)
    p_tec = c1.slider("Refroidissement", 0, 40, 20)
    p_pc = c2.slider("ASIAIR/PC", 5, 25, 10)
    p_dew = c2.slider("Bandes chauffantes", 0, 40, 15)
    runtime = (wh * 0.9) / (p_mount + p_tec + p_pc + p_dew)
    st.metric("Autonomie estimée", f"{round(runtime, 1)} h")

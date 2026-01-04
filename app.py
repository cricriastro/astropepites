import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun
from astropy.coordinates import get_body  # Nouveau correctif pour la Lune
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Master 2026", layout="wide")

# TA CLÉ API OPENWEATHER
OW_API_KEY = "16f68f1e07fea20e39f52de079037925"

# --- DATABASE DES OBJETS ---
DB_OBJECTS = [
    {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "mag": 4.0, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg/600px-Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg"},
    {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "mag": 3.4, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/M31_09-01-2011.jpg/600px-M31_09-01-2011.jpg"},
    {"name": "NGC 6960 (Dentelles)", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse", "mag": 7.0, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/The_Witch%27s_Broom_Nebula.jpg/600px-The_Witch%27s_Broom_Nebula.jpg"},
    {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "mag": 13.0, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/600px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg"},
    {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P.", "mag": 12.2, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/600px-Abell_31_nebula.jpg"},
    {"name": "C/2023 A3 (Comète)", "ra": "18h40m00s", "dec": "+05h00m00s", "type": "Comète", "mag": 5.0, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Comet_C2023_A3_2024-10-14.jpg/600px-Comet_C2023_A3_2024-10-14.jpg"}
]

# --- FONCTION MÉTÉO ---
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OW_API_KEY}&units=metric"
        res = requests.get(url).json()
        return res['clouds']['all'], res['main']['temp'], res['main']['humidity']
    except: return None, None, None

# --- SIDEBAR ---
st.sidebar.title("🛠️ CONFIGURATION SETUP")

with st.sidebar.expander("📍 GPS & Météo", expanded=True):
    lat = st.number_input("Latitude", value=48.85)
    lon = st.number_input("Longitude", value=2.35)
    clouds, temp, hum = get_weather(lat, lon)
    if clouds is not None:
        st.write(f"☁️ Nuages : **{clouds}%** | 🌡️ {temp}°C")
        if clouds < 30: st.success("🌌 CIEL DÉGAGÉ")
        else: st.error("❌ CIEL COUVERT")

with st.sidebar.expander("🔋 Batterie Bluetti", expanded=True):
    model_batt = st.selectbox("Modèle", ["EB3A (268Wh)", "EB70 (716Wh)", "AC180 (1152Wh)"])
    wh = int(model_batt.split('(')[1].replace('Wh)', ''))
    conso = st.slider("Conso (W)", 10, 60, 25)
    st.write(f"⏳ Autonomie : **{wh/conso:.1f}h**")

with st.sidebar.expander("🧭 Horizon (Boussole)", expanded=True):
    h_n = st.slider("Nord (°)", 0, 60, 20)
    h_e = st.slider("Est (°)", 0, 60, 15)
    h_s = st.slider("Sud (°)", 0, 60, 10)
    h_o = st.slider("Ouest (°)", 0, 60, 25)

# --- CORPS DE L'APP ---
st.title("🔭 AstroPépites : Expert Planning 2026")

sel_name = st.selectbox("🎯 Choisir la cible :", [t["name"] for t in DB_OBJECTS])
t_data = next(t for t in DB_OBJECTS if t["name"] == sel_name)

col1, col2 = st.columns([1, 1.5])
with col1:
    st.image(t_data["img"], use_container_width=True)
with col2:
    st.subheader(f"📊 Analyse : {sel_name}")
    st.write(f"**Type :** {t_data['type']} | **Magnitude :** {t_data['mag']}")
    
    if "Galaxie" in t_data['type'] or "Comète" in t_data['type']:
        st.error("💎 FILTRE : L-Pro ou VIDE recommandé")
    else:
        st.success("🌀 FILTRE : Svbony SV220 recommandé")
    
    st.write(f"📸 **Pose ASIAIR :** {300 if t_data['mag'] > 8 else 120}s")

# --- GRAPHIQUE ---
st.divider()
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
times = Time.now() + np.linspace(0, 12, 100)*u.hour
target_coord = SkyCoord(t_data["ra"], t_data["dec"])
altaz = target_coord.transform_to(AltAz(obstime=times, location=location))
moon_pos = get_body('moon', times, location) # Correctif ici
moon_alt = moon_pos.transform_to(AltAz(obstime=times, location=location)).alt.deg
sun_alt = get_sun(times).transform_to(AltAz(obstime=times, location=location)).alt.deg

# Logic horizon boussole
horiz = [h_n if (az<45 or az>315) else h_e if az<135 else h_s if az<225 else h_o for az in altaz.az.deg]

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(np.linspace(0, 12, 100), altaz.alt.deg, color="#00ffcc", lw=3, label=t_data["name"])
ax.plot(np.linspace(0, 12, 100), moon_alt, color="white", ls="--", alpha=0.5, label="Lune")
ax.fill_between(np.linspace(0, 12, 100), 0, horiz, color='red', alpha=0.2, label="Obstacles")
ax.fill_between(np.linspace(0, 12, 100), 0, 90, where=sun_alt < -12, color='blue', alpha=0.05, label="Nuit Noire")
ax.set_facecolor("#0e1117")
fig.patch.set_facecolor("#0e1117")
ax.set_ylim(0, 90)
ax.legend()
st.pyplot(fig)

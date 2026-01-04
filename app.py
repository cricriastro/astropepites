import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun
from astropy import units as u
from astropy.time import Time
from datetime import datetime, timedelta

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="AstroPépites : Pro-Guide", layout="wide")

# --- DATABASE CIBLES (Coordonnées & Vignettes) ---
DB_OBJECTS = {
    "Messier": [
        {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/M31_09-01-2011.jpg/600px-M31_09-01-2011.jpg", "mag": 3.4},
        {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg/600px-Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg", "mag": 4.0}
    ],
    "Arp (Raretés)": [
        {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/600px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg", "mag": 13.0}
    ],
    "Abell (Planétaires)": [
        {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P.", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/600px-Abell_31_nebula.jpg", "mag": 12.2}
    ]
}

# --- SIDEBAR : BOUSSOLE D'HORIZON ---
st.sidebar.title("🧭 BOUSSOLE D'HORIZON")
with st.sidebar.expander("🌲 Obstacles Locaux", expanded=True):
    h_nord = st.slider("Horizon Nord (°)", 0, 70, 20)
    h_est = st.slider("Horizon Est (°)", 0, 70, 15)
    h_sud = st.slider("Horizon Sud (°)", 0, 70, 10)
    h_ouest = st.slider("Horizon Ouest (°)", 0, 70, 25)

# --- SIDEBAR : SETUP MATÉRIEL ---
st.sidebar.title("🔭 SETUP IMAGERIE")
with st.sidebar.expander("⚙️ Optique & Capteur", expanded=True):
    pixel_size = 2.4 # ASI 183MC
    focale = st.number_input("Focale effective (mm)", value=320)
    echan = (pixel_size / focale) * 206
    st.write(f"Échantillonnage : **{echan:.2f}\"/px**")

with st.sidebar.expander("🔋 Énergie Bluetti", expanded=True):
    batt_wh = st.number_input("Capacité (Wh)", value=268)
    conso = st.slider("Consommation globale (W)", 10, 60, 25)
    autonomie = batt_wh / conso

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites : Expert Planning 2026")

# Sélection
all_targets = []
for cat in DB_OBJECTS.values(): all_targets.extend(cat)
sel_name = st.selectbox("🎯 Choisir la cible du soir :", [t["name"] for t in all_targets])
t_data = next(t for t in all_targets if t["name"] == sel_name)

# --- ANALYSE DE SHOOT ---
st.divider()
c1, c2 = st.columns([1, 1.5])

with c1:
    st.image(t_data["img"], use_container_width=True)
    
with c2:
    st.subheader("👨‍🏫 Recommandations Expert")
    
    # LOGIQUE FILTRE
    if "Galaxie" in t_data['type']:
        st.error("💎 **FILTRE :** L-Pro ou VIDE recommandé (Spectre continu)")
    elif "Nébuleuse" in t_data['type']:
        st.success("🌀 **FILTRE :** Svbony SV220 / Dual-Band (Ha & OIII)")
    
    # LOGIQUE TEMPS DE POSE (Approximation selon magnitude)
    if t_data['mag'] < 6:
        temps_total = "2 à 4 heures"
        poses_unit = "120s"
    elif t_data['mag'] < 11:
        temps_total = "6 à 10 heures"
        poses_unit = "300s"
    else:
        temps_total = "15+ heures (Plusieurs nuits)"
        poses_unit = "600s"
        
    st.write(f"⏱️ **Temps total requis :** {temps_total}")
    st.write(f"📸 **Poses unitaires (ASIAIR) :** {poses_unit}")
    st.write(f"🔋 **Autonomie Batterie :** {autonomie:.1f} heures")

# --- BOUSSOLE DE VISIBILITÉ ---
st.divider()
st.subheader("📈 Fenêtre de tir & Obstacles")

# Calcul de l'horizon dynamique selon l'azimut de la cible
target_coord = SkyCoord(t_data["ra"], t_data["dec"])
times = Time.now() + np.linspace(0, 12, 100)*u.hour
altaz = target_coord.transform_to(AltAz(obstime=times, location=EarthLocation(lat=48.85*u.deg, lon=2.35*u.deg)))

# On définit un horizon simplifié par quadrant
horizon_dynamic = []
for az in altaz.az.deg:
    if 315 <= az or az < 45: h = h_nord
    elif 45 <= az < 135: h = h_est
    elif 135 <= az < 225: h = h_sud
    else: h = h_ouest
    horizon_dynamic.append(h)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(np.linspace(0, 12, 100), altaz.alt.deg, color="#00ffcc", lw=3, label=t_data["name"])
ax.fill_between(np.linspace(0, 12, 100), 0, horizon_dynamic, color='red', alpha=0.2, label="Obstacles (Maison/Arbres)")
ax.set_facecolor("#0e1117")
fig.patch.set_facecolor("#0e1117")
ax.set_ylim(0, 90)
ax.legend()
st.pyplot(fig)

# --- EXPORT ASIAIR ---
st.divider()
st.download_button("📥 Télécharger CSV pour ASIAIR", 
                  f"Name,RA,Dec\n{t_data['name']},{t_data['ra']},{t_data['dec']}", 
                  file_name=f"{sel_name}.csv")

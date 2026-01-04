import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy import units as u
from astropy.time import Time
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Ultimate Pro", layout="wide")
OW_API_KEY = "16f68f1e07fea20e39f52de079037925"

# --- BASES DE DONNÉES MATÉRIEL ---
BRANDS = {
    "Télescopes": ["Sky-Watcher", "William Optics", "Askar", "Svbony", "ZWO"],
    "Filtres": ["Svbony", "Optolong", "Antlia", "ZWO", "Baader"],
    "Batteries": ["Bluetti", "EcoFlow", "Jackery"]
}

MODELS = {
    "Sky-Watcher": ["Evolux 62ED", "Esprit 80ED", "72ED", "Evostar 100ED"],
    "Svbony": ["SV220 (Dual-Band)", "SV226 (Filter Drawer)", "UHC", "CLS"],
    "Optolong": ["L-Pro", "L-Extreme", "L-Ultimate", "L-Enhance"],
    "Antlia": ["ALP-T Dual Band", "Triband RGB", "Ha 3nm"],
    "Bluetti": ["EB3A (268Wh)", "EB70 (716Wh)", "AC180 (1152Wh)"]
}

CATALOG = [
    {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "mag": 4.0, "shoot": 3},
    {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "mag": 3.4, "shoot": 5},
    {"name": "C/2023 A3 (Comète)", "ra": "18h40m00s", "dec": "+05h00m00s", "type": "Comète", "mag": 5.0, "shoot": 1},
    {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "mag": 13.0, "shoot": 12},
    {"name": "NGC 6960 (Dentelles)", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse", "mag": 7.0, "shoot": 8}
]

# --- SIDEBAR : LE CERVEAU DU SETUP ---
st.sidebar.title("🛠️ CONFIGURATION EXPERT")

with st.sidebar.expander("🔭 Optique & Accessoires", expanded=True):
    brand_t = st.selectbox("Marque Tube", BRANDS["Télescopes"])
    model_t = st.selectbox("Modèle Tube", MODELS.get(brand_t, ["Standard"]))
    f_native = st.number_input("Focale Native (mm)", value=400 if "62ED" in model_t else 360)
    
    # LA RUBRIQUE RÉDUCTEUR / BARLOW
    ratio_optique = st.select_slider("Correcteur / Barlow", options=[0.7, 0.8, 0.9, 1.0, 1.5, 2.0], value=1.0)
    f_finale = f_native * ratio_optique
    st.success(f"🎯 Focale résultante : {f_finale:.0f} mm")
    
    pixel_size = st.number_input("Taille Pixel Caméra (µm)", value=3.76)
    echantillon = (pixel_size / f_finale) * 206
    st.info(f"📐 Échantillonnage : {echantillon:.2f}\"/px")

with st.sidebar.expander("🛡️ Filtrage & Énergie", expanded=True):
    brand_f = st.selectbox("Marque Filtre", BRANDS["Filtres"])
    model_f = st.selectbox("Modèle Filtre", MODELS.get(brand_f, ["Standard"]))
    brand_b = st.selectbox("Batterie", BRANDS["Batteries"])
    model_b = st.selectbox("Modèle Batterie", MODELS.get(brand_b, ["Standard"]))
    capa = 268 if "EB3A" in model_b else 716 if "EB70" in model_b else 500
    conso = st.slider("Conso Globale (W)", 10, 80, 25)
    st.metric("Autonomie", f"{capa/conso:.1f}h")

with st.sidebar.expander("🧭 Boussole d'Horizon", expanded=False):
    h = {d: st.slider(f"Obstacle {d}", 0, 80, 15) for d in ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]}

# --- CALCULS ASTRO ---
lat, lon = 46.65, 6.91
loc = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

def get_obs_limit(az):
    idx = int(((az + 22.5) % 360) // 45)
    return list(h.values())[idx]

def is_target_ok(ra, dec):
    altaz = SkyCoord(ra, dec).transform_to(AltAz(obstime=now, location=loc))
    return altaz.alt.deg > get_obs_limit(altaz.az.deg)

visibles = [o for o in CATALOG if is_target_ok(o["ra"], o["dec"])]

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites Master Pro 2026")

# MÉTÉO EN TEMPS RÉEL AVEC LIEN API
try:
    w = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OW_API_KEY}&units=metric").json()
    c_meteo, h_meteo = w['clouds']['all'], w['main']['humidity']
    if c_meteo > 40: st.error(f"☁️ ALERTE MÉTÉO : {c_meteo}% de nuages. Shoot déconseillé.")
    elif h_meteo > 85: st.warning(f"💧 ALERTE HUMIDITÉ : {h_meteo}%. Buée imminente !")
    else: st.success("🌌 CIEL DÉGAGÉ : Prêt pour l'acquisition.")
except: st.write("Service météo en attente...")

# Sélection de la cible
if visibles:
    sel_name = st.selectbox("🎯 Choisissez une cible VISIBLE :", [t["name"] for t in visibles])
else:
    st.warning("⚠️ Aucune cible au-dessus de vos obstacles. Vérifiez la boussole.")
    sel_name = st.selectbox("Catalogue complet :", [t["name"] for t in CATALOG])

target = next(o for o in CATALOG if o["name"] == sel_name)

# --- ZONE D'ANALYSE ---
col_img, col_info = st.columns([1, 1.5])
with col_img:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg/600px-Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg", caption=target["name"])

with col_info:
    st.subheader(f"📊 Fiche Technique : {target['name']}")
    # LOGIQUE FILTRE INTELLIGENTE
    if target["type"] in ["Galaxie", "Comète"] and "SV220" in model_f:
        st.error(f"❌ ERREUR SETUP : Le filtre {model_f} est un Dual-Band. Il va tuer le signal de cette {target['type']}. RETIREZ-LE !")
    else:
        st.success(f"✅ SETUP OPTIMAL : {model_t} + {model_f}")
    
    st.write(f"⏱️ **Temps de shoot recommandé :** {target['shoot']} heures")
    
    # EXPORT ASIAIR
    plan_text = f"Target: {target['name']}\nRA: {target['ra']}\nDec: {target['dec']}\nFocal: {f_finale}mm\nFilter: {model_f}"
    st.download_button("📥 Exporter Plan ASIAIR (TXT)", plan_text, file_name=f"plan_{target['name']}.txt")

# --- GRAPHIQUES ---
st.divider()
g1, g2 = st.columns([1, 1.5])

with g1:
    st.subheader("🌹 Rose des Vents")
    
    angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
    fig_r, ax_r = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(4,4))
    ax_r.bar(angles, list(h.values()), width=0.6, color='red', alpha=0.5, label="Obstacles")
    ax_r.bar(angles, [90-v for v in h.values()], bottom=list(h.values()), width=0.6, color='green', alpha=0.3, label="Ciel Libre")
    ax_r.set_theta_zero_location('N'); ax_r.set_theta_direction(-1)
    ax_r.set_facecolor("#0e1117"); fig_r.patch.set_facecolor("#0e1117")
    st.pyplot(fig_r)

with g2:
    st.subheader("📈 Trajectoire & Éphémérides")
    times = now + np.linspace(0, 12, 100)*u.hour
    frame = AltAz(obstime=times, location=loc)
    obj_altaz = SkyCoord(target["ra"], target["dec"]).transform_to(frame)
    moon_alt = get_body('moon', times, loc).transform_to(frame).alt.deg
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(np.linspace(0, 12, 100), obj_altaz.alt.deg, color="#00ffcc", lw=3, label=target["name"])
    ax.plot(np.linspace(0, 12, 100), moon_alt, color="white", ls="--", alpha=0.3, label="Lune")
    
    obs_curve = [get_obs_limit(az) for az in obj_altaz.az.deg]
    ax.fill_between(np.linspace(0, 12, 100), 0, obs_curve, color='red', alpha=0.2)
    
    ax.set_ylim(0, 90); ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.legend(); st.pyplot(fig)

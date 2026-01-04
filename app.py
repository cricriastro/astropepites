import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Ultimate 2026", layout="wide")

# Données Météo (Romont)
API_KEY = "16f68f1e07fea20e39f52de079037925"
LAT, LON = 46.65, 6.91

# --- BASE DE DONNÉES DU MARCHÉ ---
EQUIPMENT = {
    "Télescopes": ["Sky-Watcher Evolux 62ED", "Sky-Watcher 72ED", "Askar FRA400", "ZWO Seestar S50", "William Optics RedCat 51"],
    "Filtres": ["Svbony SV220 (Dual-Band)", "Optolong L-Pro", "Optolong L-Extreme", "Antlia ALP-T", "ZWO Duo-Band", "UV/IR Cut (Vide)"],
    "Batteries": ["Bluetti EB3A (268Wh)", "Bluetti EB70 (716Wh)", "EcoFlow River 2", "Jackery 240"]
}

CATALOG = [
    {"name": "M42 Orion", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "mag": 4.0, "img": "https://nova.astrometry.net/image/16654271"},
    {"name": "M31 Andromède", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "mag": 3.4, "img": "https://nova.astrometry.net/image/16654272"},
    {"name": "C/2023 A3 (Comète)", "ra": "18h40m00s", "dec": "+05h00m00s", "type": "Comète", "mag": 5.0, "img": "https://nova.astrometry.net/image/16654273"}
]

# --- SIDEBAR PRO ---
st.sidebar.title("👨‍🚀 Dashboard Expert")

with st.sidebar.expander("🔭 Matériel & Optique", expanded=True):
    tube = st.selectbox("Mon Tube", EQUIPMENT["Télescopes"])
    focale = st.number_input("Focale Native (mm)", value=400 if "62ED" in tube else 360)
    # AJOUT DU RÉDUCTEUR / BARLOW
    ratio = st.select_slider("Correcteur de champ", options=[0.7, 0.8, 0.9, 1.0, 1.5, 2.0], value=1.0)
    f_finale = focale * ratio
    st.caption(f"Focale calculée : {f_finale} mm")

with st.sidebar.expander("🔋 Énergie & Filtres", expanded=True):
    filtre_sel = st.selectbox("Filtre utilisé", EQUIPMENT["Filtres"])
    batterie_sel = st.selectbox("Ma Batterie", EQUIPMENT["Batteries"])
    capa_wh = 268 if "EB3A" in batterie_sel else 716
    conso = st.number_input("Consommation totale (W)", value=25)
    st.metric("Autonomie estimée", f"{capa_wh/conso:.1f} heures")

with st.sidebar.expander("🧭 Horizon (Boussole)", expanded=True):
    st.write("Réglez les obstacles par secteur :")
    h = {}
    # UTILISATION DE NUMBER_INPUT AVEC BOUTONS +/-
    c1, c2 = st.columns(2)
    h["N"] = c1.number_input("Nord (°)", 0, 80, 20)
    h["NE"] = c2.number_input("N-Est (°)", 0, 80, 15)
    h["E"] = c1.number_input("Est (°)", 0, 80, 25)
    h["SE"] = c2.number_input("S-Est (°)", 0, 80, 10)
    h["S"] = c1.number_input("Sud (°)", 0, 80, 5)
    h["SO"] = c2.number_input("S-Ouest (°)", 0, 80, 20)
    h["O"] = c1.number_input("Ouest (°)", 0, 80, 30)
    h["NO"] = c2.number_input("N-Ouest (°)", 0, 80, 15)

# --- ZONE MÉTÉO & ALERTES ---
st.markdown("### ☁️ État du Ciel & Alertes")
try:
    w = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric").json()
    met_col1, met_col2, met_col3 = st.columns(3)
    cloud = w['clouds']['all']
    hum = w['main']['humidity']
    temp = w['main']['temp']
    
    met_col1.metric("Nuages", f"{cloud}%")
    met_col2.metric("Humidité", f"{hum}%")
    met_col3.metric("Température", f"{temp}°C")

    if cloud > 40: st.error("❌ Alerte : Trop de nuages pour imager.")
    elif hum > 85: st.warning("⚠️ Alerte : Humidité critique (Buée imminente !)")
    else: st.success("✅ Conditions optimales détectées.")
except:
    st.info("Connexion météo en attente...")

# --- LOGIQUE DE VISIBILITÉ ---
loc = EarthLocation(lat=LAT*u.deg, lon=LON*u.deg)
now = Time.now()
visibles = []
for obj in CATALOG:
    altaz = SkyCoord(obj["ra"], obj["dec"]).transform_to(AltAz(obstime=now, location=loc))
    limite = list(h.values())[int(((altaz.az.deg + 22.5) % 360) // 45)]
    if altaz.alt.deg > limite: visibles.append(obj)

# --- AFFICHAGE PRINCIPAL ---
st.divider()
target = st.selectbox("🎯 Choisir la cible (Filtrée par horizon) :", visibles, format_func=lambda x: x['name'])

c_left, c_right = st.columns([1, 1.2])

with c_left:
    st.image(target["img"], use_container_width=True, caption=f"Cible : {target['name']}")

with c_right:
    st.header(f"Analyse Expert : {target['name']}")
    # LOGIQUE FILTRE
    if target["type"] in ["Galaxie", "Comète"] and "SV220" in filtre_sel:
        st.error(f"🚫 ATTENTION : Votre {filtre_sel} bloque le signal ! Retirez-le.")
    else:
        st.success(f"💎 Setup Filtre : {filtre_sel} est adapté.")
    
    st.write(f"**Type :** {target['type']} | **Magnitude :** {target['mag']}")
    st.info(f"📸 Pose ASIAIR conseillée : {'120s' if target['mag'] < 6 else '300s'}")

# Rose des vents
st.subheader("🌹 Horizon Local")
angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
fig_p, ax_p = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(4,4))
ax_p.bar(angles, list(h.values()), color='red', alpha=0.5)
ax_p.bar(angles, [90-v for v in h.values()], bottom=list(h.values()), color='green', alpha=0.3)
ax_p.set_theta_zero_location('N')
ax_p.set_theta_direction(-1)
ax_p.set_facecolor("#0e1117")
fig_p.patch.set_facecolor("#0e1117")
st.pyplot(fig_p)

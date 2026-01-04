import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION STYLE ---
st.set_page_config(page_title="AstroPépites Master", layout="wide")
st.markdown("""<style> .main { background-color: #0e1117; } .stMetric { background-color: #1a1c24; padding: 10px; border-radius: 10px; } </style>""", unsafe_allow_html=True)

# --- BASE DE DONNÉES MATÉRIEL ---
FILTERS_DB = ["Svbony SV220 (Dual-Band)", "Optolong L-Pro", "Optolong L-Extreme", "Optolong L-Ultimate", "Antlia ALP-T Dual Band", "Antlia Triband RGB", "ZWO Duo-Band", "IDAS NBZ", "UV/IR Cut"]
POWER_DB = {"Bluetti EB3A": 268, "Bluetti EB70": 716, "EcoFlow River 2": 256, "EcoFlow River Pro": 720, "Jackery 240": 240}
TUBES_DB = ["Sky-Watcher Evolux 62ED", "Sky-Watcher 72ED", "Askar FRA400", "RedCat 51", "SharpStar 61EDPH"]

# --- SIDEBAR : LE SETUP COMPLET ---
st.sidebar.title("🔭 SETUP CONFIGURATOR")

with st.sidebar.expander("🛠️ Optique & Caméra", expanded=True):
    tube = st.selectbox("Tube Optique", TUBES_DB)
    f_nat = st.number_input("Focale Native (mm)", value=400, step=10)
    reducteur = st.select_slider("Réducteur / Barlow", options=[0.7, 0.75, 0.8, 0.9, 1.0, 1.5, 2.0], value=1.0)
    f_res = f_nat * reducteur
    st.caption(f"Focale résultante : {f_res:.1f} mm")

with st.sidebar.expander("🔋 Énergie & Accessoires", expanded=True):
    bat_choice = st.selectbox("Batterie", list(POWER_DB.keys()))
    capa_wh = POWER_DB[bat_choice]
    
    st.write("**Consommation détaillée (Watts) :**")
    w_mount = st.number_input("Monture (Suivi)", 5, 20, 8)
    w_camera = st.number_input("Caméra (Refroidie)", 5, 30, 15)
    w_asiair = st.number_input("ASIAIR + EAF + Roue", 2, 10, 5)
    w_heat = st.number_input("Résistances Chauffantes", 0, 40, 12)
    
    total_w = w_mount + w_camera + w_asiair + w_heat
    # Calcul réel avec marge de sécurité de 15%
    autonomie_h = (capa_wh * 0.85) / total_w
    st.metric("Autonomie Réelle", f"{autonomie_h:.1f} h", delta=f"-{total_w}W")

with st.sidebar.expander("🧭 Horizon (Obstacles)", expanded=True):
    cols = st.columns(2)
    h_n = cols[0].number_input("N (°)", 0, 80, 15)
    h_ne = cols[1].number_input("NE (°)", 0, 80, 15)
    h_e = cols[0].number_input("E (°)", 0, 80, 25)
    h_se = cols[1].number_input("SE (°)", 0, 80, 10)
    h_s = cols[0].number_input("S (°)", 0, 80, 5)
    h_so = cols[1].number_input("SO (°)", 0, 80, 20)
    h_o = cols[0].number_input("O (°)", 0, 80, 30)
    h_no = cols[1].number_input("NO (°)", 0, 80, 15)
    h_map = {"N": h_n, "NE": h_ne, "E": h_e, "SE": h_se, "S": h_s, "SO": h_so, "O": h_o, "NO": h_no}

# --- LOGIQUE MÉTÉO ---
try:
    meteo = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat=46.65&lon=6.91&appid=16f68f1e07fea20e39f52de079037925&units=metric").json()
    cloud_cover = meteo['clouds']['all']
    humidity = meteo['main']['humidity']
except: cloud_cover, humidity = 50, 50

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites Pro Dashboard")

# Alertes Météo & Energie
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Météo (Nuages)", f"{cloud_cover}%")
    if cloud_cover > 40: st.error("⚠️ Trop de nuages")
with m2:
    st.metric("Humidité", f"{humidity}%")
    if humidity > 85: st.warning("⚠️ Buée probable")
with m3:
    st.metric("Consommation", f"{total_w} W")
    if autonomie_h < 5: st.error("⚠️ Batterie faible")

# Sélection Cible & Filtre
st.divider()
c_target, c_filter = st.columns(2)
with c_target:
    target_name = st.selectbox("🎯 Cible", ["M42 Orion", "M31 Andromède", "NGC 7000 North America", "C/2023 A3 (Comète)"])
    filter_used = st.selectbox("💎 Filtre installé", FILTERS_DB)

# ANALYSE EXPERTE
st.markdown("### 📋 Analyse du Shooting")
info_col, graph_col = st.columns([1, 1.5])

with info_col:
    # Logique Filtre
    is_galaxy = "Andromède" in target_name or "Comète" in target_name
    if is_galaxy and "Dual-Band" in filter_used:
        st.error(f"❌ FILTRE INADAPTÉ : Le {filter_used} bloque le signal continu des galaxies/comètes. Utilisez un filtre UV/IR Cut ou L-Pro.")
    else:
        st.success(f"✅ SETUP FILTRE OK : {filter_used} est cohérent.")
    
    st.info(f"📐 Échantillonnage : {(3.76 / f_res) * 206:.2f}\"/pixel")
    st.write(f"⏱️ Temps de shoot max avec {bat_choice} : **{autonomie_h:.1f} heures**.")

with graph_col:
    # Rose des vents compacte
    angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
    vals = list(h_map.values())
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(4,4))
    ax.bar(angles, vals, color='red', alpha=0.5, width=0.6)
    ax.bar(angles, [90-v for v in vals], bottom=vals, color='green', alpha=0.3, width=0.6)
    ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
    ax.set_facecolor("#1a1c24"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

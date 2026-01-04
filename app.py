import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION STYLE ---
st.set_page_config(page_title="AstroPépites Master 2026", layout="wide")

# --- BASE DE DONNÉES MATÉRIEL UNIVERSELLE ---
EQUIP_DB = {
    "Batteries": {"Bluetti EB3A": 268, "Bluetti EB70": 716, "EcoFlow River 2": 256, "Jackery 240": 240},
    "Montures": {"ZWO AM5/AM3": 10, "EQ6-R Pro": 15, "Star Adventurer GTi": 6, "Ioptron CEM26": 10},
    "Caméras": {"ZWO ASI2600 (Refroidie)": 18, "ZWO ASI533 (Refroidie)": 12, "ZWO ASI294 (Refroidie)": 14, "Canon/Nikon DSLR": 4}
}

# --- SIDEBAR : CONFIGURATION COMPLÈTE ---
st.sidebar.title("🛠️ Setup & Énergie")

with st.sidebar.expander("🔋 Choix du Matériel", expanded=True):
    bat_sel = st.selectbox("Ma Batterie", list(EQUIP_DB["Batteries"].keys()))
    mnt_sel = st.selectbox("Ma Monture", list(EQUIP_DB["Montures"].keys()))
    cam_sel = st.selectbox("Ma Caméra", list(EQUIP_DB["Caméras"].keys()))
    
    capa_wh = EQUIP_DB["Batteries"][bat_sel]
    w_mnt = EQUIP_DB["Montures"][mnt_sel]
    w_cam = EQUIP_DB["Caméras"][cam_sel]

with st.sidebar.expander("🔌 Accessoires (Boutons +/-)", expanded=True):
    w_asiair = st.number_input("ASIAIR Plus / Mini (W)", 0, 15, 6)
    w_guide = st.number_input("Caméra de Suivi / Guidage (W)", 0, 10, 2)
    w_eaf = st.number_input("EAF + Roue à filtres (W)", 0, 10, 2)
    w_heat = st.number_input("Résistances Chauffantes (W)", 0, 40, 12)
    
    # Calcul Consommation et Autonomie
    total_w = w_mnt + w_cam + w_asiair + w_guide + w_eaf + w_heat
    rendement = 0.85 # Marge de sécurité de 15%
    heures_restantes = (capa_wh * rendement) / total_w
    
    # Calcul de l'heure de fin
    heure_fin = datetime.now() + timedelta(hours=heures_restantes)
    
    st.divider()
    st.metric("Conso Totale", f"{total_w} W")
    st.metric("Heure de coupure", heure_fin.strftime("%H:%M"))

with st.sidebar.expander("🧭 Horizon (Précision brute)", expanded=False):
    h = {d: st.number_input(f"{d} (°)", 0, 90, 15) for d in ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]}

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites : Expert Planning")

# Météo Directe Romont
try:
    m = requests.get("https://api.openweathermap.org/data/2.5/weather?lat=46.65&lon=6.91&appid=16f68f1e07fea20e39f52de079037925&units=metric").json()
    met1, met2, met3 = st.columns(3)
    met1.metric("Nuages", f"{m['clouds']['all']}%")
    met2.metric("Humidité", f"{m['main']['humidity']}%")
    met3.metric("Vent", f"{m['wind']['speed']} km/h")
except: pass

st.divider()

# Cible et Filtre UNIQUE
col1, col2 = st.columns(2)
with col1:
    target = st.selectbox("🎯 Cible", ["M31 Andromède", "M42 Orion", "NGC 7000", "C/2023 A3 (Comète)"])
with col2:
    filtre = st.selectbox("💎 Filtre installé", ["Aucun / UV-IR Cut", "Svbony SV220 (Dual-Band)", "Optolong L-Pro"])

# --- GRAPHIQUE D'ÉNERGIE DYNAMIQUE ---
st.subheader("🔋 Suivi de l'autonomie")
temps = np.linspace(0, heures_restantes, 100)
charge = np.linspace(100, 15, 100) # De 100% à 15% (sécurité)

fig_p, ax_p = plt.subplots(figsize=(10, 2))
ax_p.fill_between(temps, charge, color='green', alpha=0.3)
ax_p.plot(temps, charge, color='lime', lw=2)
ax_p.set_ylabel("Batterie %")
ax_p.set_xlabel("Heures de shoot")
ax_p.set_facecolor("#0e1117"); fig_p.patch.set_facecolor("#0e1117")
ax_p.tick_params(colors='white')
st.pyplot(fig_p)

# --- ANALYSE FINALE ---
res_a, res_b = st.columns(2)

with res_a:
    st.markdown("### 📋 Rapport de session")
    st.write(f"✅ **Matériel :** {mnt_sel} + {cam_sel}")
    st.write(f"🔋 **Batterie :** {bat_sel} ({capa_wh}Wh)")
    
    if ("Andromède" in target or "Comète" in target) and "SV220" in filtre:
        st.error(f"🚫 ALERTE : Le {filtre} est incompatible avec {target} (Galaxie/Comète).")
    else:
        st.success(f"✔️ Configuration {filtre} validée.")
    
    st.warning(f"⚠️ Ta session doit s'arrêter à **{heure_fin.strftime('%H:%M')}** maximum.")

with res_b:
    # Rose des vents
    angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
    fig_h, ax_h = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3,3))
    ax_h.bar(angles, list(h.values()), color='red', alpha=0.5)
    ax_h.set_theta_zero_location('N'); ax_h.set_theta_direction(-1)
    ax_h.set_facecolor("#0e1117"); fig_h.patch.set_facecolor("#0e1117")
    ax_h.tick_params(colors='white')
    st.pyplot(fig_h)

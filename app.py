import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy import units as u
from astropy.time import Time

st.set_page_config(page_title="AstroPépites Expert", layout="wide")

# --- BASE DE DONNÉES TECHNIQUE ---
# Consommation réelle moyenne en Watts (sous 12V)
POWER_CONSUMPTION = {
    "ASIAIR Plus/Mini": 6,
    "Caméra Principale (Refroidie)": 18,
    "Caméra de Guidage (USB)": 2,
    "Monture (Suivi Sidéral)": 9,
    "EAF (Mise au point)": 1,
    "Roue à filtres (EFW)": 1,
    "Résistance Chauffante (Moyenne)": 12
}

BATTERIES = {
    "Bluetti EB3A": 268,
    "Bluetti EB70": 716,
    "EcoFlow River 2": 256
}

# --- SIDEBAR TECHNIQUE ---
st.sidebar.title("🛠️ Configuration Réelle")

with st.sidebar.expander("🔌 Gestion de l'Énergie", expanded=True):
    bat_sel = st.selectbox("Batterie utilisée", list(BATTERIES.keys()))
    capa_wh = BATTERIES[bat_sel]
    
    st.write("**Éléments actifs :**")
    # Utilisation de checkbox pour des chiffres binaires (On/Off) et précis
    use_guide = st.checkbox("Caméra de Guidage", value=True)
    use_cool = st.checkbox("Refroidissement Caméra (-10°C)", value=True)
    use_heat = st.checkbox("Résistance Chauffante", value=True)
    
    # Calcul de la puissance totale consommée
    p_total = POWER_CONSUMPTION["ASIAIR Plus/Mini"] + POWER_CONSUMPTION["Monture (Suivi Sidéral)"]
    if use_guide: p_total += POWER_CONSUMPTION["Caméra de Guidage (USB)"]
    if use_cool: p_total += POWER_CONSUMPTION["Caméra Principale (Refroidie)"]
    if use_heat: p_total += POWER_CONSUMPTION["Résistance Chauffante (Moyenne)"]
    
    # Formule : Heures = Capacité (Wh) / Puissance (W) * Rendement (0.85)
    autonomie_reelle = (capa_wh * 0.85) / p_total
    
    st.metric("Consommation Totale", f"{p_total} Watts")
    st.metric("Autonomie Réelle (85%)", f"{autonomie_reelle:.2f} h")

with st.sidebar.expander("🔭 Optique & Guidage", expanded=True):
    f_nat = st.number_input("Focale Evolux (mm)", value=400)
    reducteur = st.selectbox("Réducteur de focale", [0.8, 0.9, 1.0], index=1)
    f_finale = f_nat * reducteur
    
    st.write(f"🎯 Focale Imageur : **{f_finale:.0f} mm**")
    if use_guide:
        st.write("🛰️ Guidage : **Actif via ASIAIR**")

with st.sidebar.expander("🧭 Horizon (Degrés Précis)", expanded=True):
    # Utilisation de number_input sans "pas" de 5 pour une précision au degré près
    h = {d: st.number_input(f"Obstacle {d} (°)", 0, 90, 15) for d in ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]}

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites Pro Dashboard")

# Affichage Météo (Romont)
try:
    w = requests.get("https://api.openweathermap.org/data/2.5/weather?lat=46.65&lon=6.91&appid=16f68f1e07fea20e39f52de079037925&units=metric").json()
    c1, c2, c3 = st.columns(3)
    c1.metric("Ciel", f"{w['clouds']['all']}% Nuages")
    c2.metric("Humidité", f"{w['main']['humidity']}%")
    c3.metric("Vent", f"{w['wind']['speed']} km/h")
except:
    st.warning("Données météo indisponibles.")

# Cibles
target = st.selectbox("🎯 Cible sélectionnée", ["M31 Andromède", "M42 Orion", "C/2023 A3 (Comète)"])

st.divider()

col_txt, col_vis = st.columns([1, 1])

with col_txt:
    st.subheader(f"Analyse Expert : {target}")
    if "Andromède" in target or "Comète" in target:
        st.error("⚠️ FILTRE : Ne pas utiliser le SV220 (Dual-Band) sur cette cible !")
    else:
        st.success("✅ FILTRE : SV220 Dual-Band recommandé.")
    
    st.write(f"📊 **Setup :** {f_finale}mm avec guidage USB.")
    st.write(f"🔋 **Énergie :** Ta {bat_sel} tiendra précisément **{int(autonomie_reelle)}h {int((autonomie_reelle%1)*60)}min**.")

with col_vis:
    # Rose des vents scientifique
    angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(4,4))
    ax.bar(angles, list(h.values()), color='red', alpha=0.6, width=0.6)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_facecolor("#111")
    fig.patch.set_facecolor("#0e1117")
    st.pyplot(fig)

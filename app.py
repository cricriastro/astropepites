import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Expert Romont", layout="wide")

# --- BASE DE DONNÉES CIBLES (Correction Expert) ---
TARGETS_INTEL = {
    "M31 Andromède": {"type": "Galaxie", "desc": "Continu + Régions HII (Ha)."},
    "M42 Orion": {"type": "Nébuleuse", "desc": "Émission intense (Ha, OIII)."},
    "C/2023 A3 (Comète)": {"type": "Comète", "desc": "Gaz (Cyan) + Poussières."},
    "NGC 7000 (North America)": {"type": "Nébuleuse", "desc": "Émission Hydrogène (Ha)."},
    "M45 Les Pléiades": {"type": "Amas", "desc": "Réflexion bleue (Spectre continu)."}
}

# --- SIDEBAR : RÉGLAGES PRÉCIS ---
st.sidebar.title("🛠️ Mon Setup ASIAIR")

with st.sidebar.expander("🎥 Caméra Personnalisée", expanded=True):
    cam_name = st.text_input("Modèle", "ZWO ASI294MC Pro")
    w_cam = st.number_input("Conso Caméra (W)", 1, 30, 15)
    px_size = st.number_input("Taille pixels (µm)", 1.0, 10.0, 4.63)

with st.sidebar.expander("🔋 Énergie (Bluetti EB3A)", expanded=True):
    bat_wh = 268  # Capacité fixe de ta EB3A
    w_mount = st.number_input("Monture (W)", 1, 25, 8)
    w_asiair_guide = st.number_input("ASIAIR + Guidage (W)", 1, 20, 8)
    w_heat = st.number_input("Chauffage (W)", 0, 40, 12)
    
    total_w = w_cam + w_mount + w_asiair_guide + w_heat
    # Calcul d'autonomie (85% utilisable pour protéger la batterie)
    autonomie_h = (bat_wh * 0.85) / total_w
    heure_fin = datetime.now() + timedelta(hours=autonomie_h)

with st.sidebar.expander("🧭 Horizon (Degrés exacts)", expanded=False):
    h = {d: st.number_input(f"{d} (°)", 0, 90, 15) for d in ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]}

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites Pro Dashboard")

# MÉTÉO RÉELLE AVEC TA CLÉ (Romont)
try:
    # Utilisation de ta clé API OpenWeather
    api_key = "16f68f1e07fea20e39f52de079037925"
    url = f"https://api.openweathermap.org/data/2.5/weather?lat=46.65&lon=6.91&appid={api_key}&units=metric"
    m = requests.get(url).json()
    
    met1, met2, met3 = st.columns(3)
    met1.metric("Nuages", f"{m['clouds']['all']}%")
    met2.metric("Humidité", f"{m['main']['humidity']}%")
    met3.metric("Coupure Énergie", heure_fin.strftime("%H:%M"))
    
    if m['clouds']['all'] > 60:
        st.error("⚠️ Couverture nuageuse importante à Romont.")
except Exception:
    st.warning("⚠️ Erreur de connexion météo (Vérifie ta connexion internet).")

st.divider()

# SÉLECTION CIBLE ET FILTRE
c1, c2 = st.columns(2)
t_name = c1.selectbox("🎯 Cible du soir", list(TARGETS_INTEL.keys()))
f_name = c2.selectbox("💎 Filtre installé", ["Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])

# --- ANALYSE FILTRAGE ---
st.subheader("📋 Analyse Technique")

t_type = TARGETS_INTEL[t_name]["type"]
if f_name == "Svbony SV220 (Dual-Band)":
    if "Galaxie" in t_type:
        st.warning(f"💡 **Note Expert :** Sur {t_name}, le SV220 capture spécifiquement les nébuleuses rouges (H-alpha). C'est parfait pour les détails, mais pense à mixer avec du signal sans filtre pour les bras de la galaxie.")
    elif "Comète" in t_type or "Amas" in t_type:
        st.error(f"❌ **Erreur Signal :** Le SV220 bloque le spectre bleu/vert de {t_name}. Utilise un filtre clair !")
    else:
        st.success(f"✅ **Optimal :** Le contraste sera parfait sur les gaz de {t_name}.")
else:
    st.success(f"✅ Filtre {f_name} validé pour {t_name}.")

# --- GRAPHIQUES ---
st.write(f"🔋 **Autonomie :** {int(autonomie_h)}h {int((autonomie_h%1)*60)}min restants.")
col_g, col_r = st.columns([1.5, 1])

with col_g:
    # Graphique de décharge
    tx = np.linspace(0, autonomie_h, 100)
    ty = np.linspace(100, 15, 100)
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.plot(tx, ty, color='#00FF00', lw=2)
    ax.fill_between(tx, ty, color='#00FF00', alpha=0.1)
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.set_ylabel("%", color="white"); ax.tick_params(colors='white')
    st.pyplot(fig)

with col_r:
    # Rose des vents
    angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
    fig_h, ax_h = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3,3))
    ax_h.bar(angles, list(h.values()), color='red', alpha=0.5)
    ax_h.set_theta_zero_location('N'); ax_h.set_theta_direction(-1)
    ax_h.set_facecolor("#0e1117"); fig_h.patch.set_facecolor("#0e1117")
    ax_h.tick_params(colors='white')
    st.pyplot(fig_h)

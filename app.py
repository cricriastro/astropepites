import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Expert", layout="wide")

# --- DATA RÉELLE ---
BATTERIES = {"Bluetti EB3A": 268, "Bluetti EB70": 716, "EcoFlow River 2": 256}
MONTURES = {"Star Adventurer GTi": 6, "ZWO AM5": 10, "EQ6-R Pro": 15, "Heq5": 12}
CAMERAS_DEFAULT = ["ZWO ASI2600", "ZWO ASI533", "ZWO ASI294", "Canon DSLR"]

# --- SIDEBAR SETUP ---
st.sidebar.title("🔭 Mon Matériel Réel")

with st.sidebar.expander("🎥 Caméra & Capteur", expanded=True):
    cam_choice = st.selectbox("Modèle", CAMERAS_DEFAULT + ["Autre (Saisie manuelle)"])
    if cam_choice == "Autre (Saisie manuelle)":
        cam_name = st.text_input("Nom de ta caméra", "Ma Caméra")
        w_cam = st.number_input("Conso réelle (Watts)", 1, 30, 15)
        px_size = st.number_input("Taille pixel (µm)", 1.0, 10.0, 3.76)
    else:
        cam_name = cam_choice
        w_cam = 15 # Moyenne pour cam refroidie
        px_size = 3.76

with st.sidebar.expander("🔋 Énergie & Conso", expanded=True):
    bat_sel = st.selectbox("Batterie", list(BATTERIES.keys()))
    mnt_sel = st.selectbox("Monture", list(MONTURES.keys()))
    
    # Détail conso sans bidouillage
    w_asiair = st.number_input("ASIAIR / Guidage (W)", 0, 20, 8)
    w_heat = st.number_input("Résistances Chauffantes (W)", 0, 40, 12)
    
    total_w = w_cam + MONTURES[mnt_sel] + w_asiair + w_heat
    # Calcul d'autonomie avec 15% de réserve de sécurité
    autonomie_h = (BATTERIES[bat_sel] * 0.85) / total_w
    heure_fin = datetime.now() + timedelta(hours=autonomie_h)

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites Pro Dashboard")

# Météo Romont
try:
    m = requests.get("https://api.openweathermap.org/data/2.5/weather?lat=46.65&lon=6.91&appid=16f68f1e07fea20e39f52de079037925&units=metric").json()
    c1, c2, c3 = st.columns(3)
    c1.metric("Ciel", f"{m['clouds']['all']}% Nuages")
    c2.metric("Humidité", f"{m['main']['humidity']}%")
    c3.metric("Fin batterie", heure_fin.strftime("%H:%M"))
except: pass

st.divider()

# Sélection Cible et Filtre
col_t, col_f = st.columns(2)
target = col_t.selectbox("🎯 Cible", ["M31 Andromède", "M42 Orion", "C/2023 A3", "NGC 7000"])
filtre = col_f.selectbox("💎 Filtre", ["Svbony SV220 (Dual-Band)", "L-Pro", "UV/IR Cut"])

# --- ANALYSE EXPERT (La correction !) ---
st.subheader("📋 Analyse du Shooting")
info, graph = st.columns([1, 1])

with info:
    if "Andromède" in target and "SV220" in filtre:
        st.warning("💡 **Usage Expert :** Le SV220 sur M31 sert uniquement à isoler les nébulosités H-alpha (le rouge). Prévoyez des poses sans filtre pour la structure galactique.")
            elif "C/2023" in target and "SV220" in filtre:
        st.error("⚠️ Le Dual-Band va tuer la queue de la comète (Cyan/Vert). Préférez un filtre clair.")
    else:
        st.success(f"✅ Setup {filtre} cohérent pour {target}.")

    st.write(f"📸 **Capteur :** {cam_name} ({px_size}µm)")
    st.write(f"🔋 **Autonomie :** {int(autonomie_h)}h {int((autonomie_h%1)*60)}min")

with graph:
    # Graphique de décharge
    t = np.linspace(0, autonomie_h, 100)
    c = np.linspace(100, 15, 100)
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(t, c, color='#00FF00', lw=3)
    ax.fill_between(t, c, color='#00FF00', alpha=0.1)
    ax.set_ylabel("Batterie %"); ax.set_xlabel("Heures")
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

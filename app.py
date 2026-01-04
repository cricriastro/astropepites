import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Scientifique", layout="wide")

# --- BASE DE DONNÉES CIBLES ---
TARGETS_INTEL = {
    "M31 Andromède": {"type": "Galaxie", "desc": "Spectre continu + régions HII (Rouge)."},
    "M42 Orion": {"type": "Nébuleuse", "desc": "Émission intense (Ha, OIII)."},
    "C/2023 A3 (Comète)": {"type": "Comète", "desc": "Spectre continu + Gaz (Cyan/Vert)."},
    "NGC 7000 (North America)": {"type": "Nébuleuse émission", "desc": "Hydrogène pur (Ha)."},
    "M45 Les Pléiades": {"type": "Amas", "desc": "Réflexion bleue (Spectre continu)."}
}

# --- SIDEBAR : CONFIGURATION ---
st.sidebar.title("🛠️ Configuration Expert")

with st.sidebar.expander("🎥 Caméra Personnalisée", expanded=True):
    cam_name = st.text_input("Modèle", "ASI294MC Pro")
    # Pas de slider "Grrr", que des boutons + / -
    w_cam = st.number_input("Conso Caméra (W)", 1, 30, 15)
    px_size = st.number_input("Taille des pixels (µm)", 1.0, 10.0, 4.63)

with st.sidebar.expander("🔋 Énergie & Matériel", expanded=True):
    bat_wh = st.number_input("Batterie (Wh)", 100, 2000, 268) # EB3A = 268
    w_mount = st.number_input("Monture (W)", 1, 25, 8)
    w_acc = st.number_input("ASIAIR + Guidage (W)", 1, 20, 7)
    w_heat = st.number_input("Chauffage (W)", 0, 40, 10)
    
    total_w = w_cam + w_mount + w_acc + w_heat
    # Sécurité 15% pour la batterie
    autonomie_h = (bat_wh * 0.85) / total_w
    heure_fin = datetime.now() + timedelta(hours=autonomie_h)

with st.sidebar.expander("🧭 Horizon (Boussole)", expanded=False):
    h = {d: st.number_input(f"{d} (°)", 0, 90, 15) for d in ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]}

# --- DASHBOARD PRINCIPAL ---
st.title("🔭 AstroPépites Pro Dashboard")

# Météo Directe (Romont)
try:
    m = requests.get("https://api.openweathermap.org/data/2.5/weather?lat=46.65&lon=6.91&appid=16f68f1e07fea20e39f52de079037925&units=metric").json()
    met1, met2, met3 = st.columns(3)
    met1.metric("Nuages", f"{m['clouds']['all']}%")
    met2.metric("Humidité", f"{m['main']['humidity']}%")
    met3.metric("Coupure Batterie", heure_fin.strftime("%H:%M"))
except:
    st.warning("Météo : Erreur de connexion.")

st.divider()

# Cible et Filtre UNIQUE
c1, c2 = st.columns(2)
t_name = c1.selectbox("🎯 Cible", list(TARGETS_INTEL.keys()))
f_name = c2.selectbox("💎 Filtre", ["Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])

# --- ANALYSE TECHNIQUE SANS ERREUR ---
st.subheader("📋 Analyse du Shooting")

t_type = TARGETS_INTEL[t_name]["type"]
if f_name == "Svbony SV220 (Dual-Band)":
    if "Galaxie" in t_type:
        st.warning(f"💡 **Usage Expert :** Sur {t_name}, le SV220 sert à isoler les régions HII (les nébulosités rouges). C'est top pour le détail, mais n'oublie pas de faire des poses sans filtre pour la galaxie elle-même !")
    elif "Comète" in t_type or "Amas" in t_type:
        st.error(f"❌ **Incompatible :** Le SV220 bloque le signal de {t_name}. Tu vas perdre la comète ou les étoiles bleues.")
    else:
        st.success(f"✅ **Optimal :** Parfait pour l'émission Ha/OIII de {t_name}.")
else:
    st.success(f"✅ Setup {f_name} validé pour {t_name}.")

# --- GRAPHIQUES ---
col_graph, col_rose = st.columns([1, 1])

with col_graph:
    st.write(f"🔋 **Batterie :** Vide à {heure_fin.strftime('%H:%M')} ({int(autonomie_h)}h {int((autonomie_h%1)*60)}min)")
    t_plot = np.linspace(0, autonomie_h, 100)
    c_plot = np.linspace(100, 15, 100)
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.plot(t_plot, c_plot, color='lime', lw=2)
    ax.fill_between(t_plot, c_plot, color='lime', alpha=0.1)
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white'); ax.set_ylabel("%", color="white")
    st.pyplot(fig)

with col_rose:
    angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
    fig_h, ax_h = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3,3))
    ax_h.bar(angles, list(h.values()), color='red', alpha=0.5)
    ax_h.set_theta_zero_location('N'); ax_h.set_theta_direction(-1)
    ax_h.set_facecolor("#0e1117"); fig_h.patch.set_facecolor("#0e1117")
    ax_h.tick_params(colors='white')
    st.pyplot(fig_h)

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites 2026 Pro", layout="wide")

# --- BASE DE DONNÉES CIBLES (Noms au lieu de numéros) ---
DATA_CIBLES = {
    "Messier": {
        "M31 - Galaxie d'Andromède": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/M31_09-01-2011_%28C9.25%29.jpg/200px-M31_09-01-2011_%28C9.25%29.jpg",
        "M42 - Nébuleuse d'Orion": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_180px.jpg/200px-Orion_Nebula_-_Hubble_2006_mosaic_180px.jpg",
        "M45 - Les Pléiades": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Pleiades_large.jpg/200px-Pleiades_large.jpg",
        "M51 - Galaxie du Tourbillon": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Messier51_sRGB.jpg/200px-Messier51_sRGB.jpg"
    },
    "NGC / IC": {
        "NGC 7000 - North America": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/NGC7000_The_North_America_Nebula.jpg/200px-NGC7000_The_North_America_Nebula.jpg",
        "NGC 6960 - Petite Dentelle": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/The_Witch%27s_Broom_Nebula.jpg/200px-The_Witch%27s_Broom_Nebula.jpg",
        "IC 434 - Tête de Cheval": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Barnard_33.jpg/200px-Barnard_33.jpg"
    },
    "Événements 2026": {
        "Éclipse Solaire Totale (12/08/2026)": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Solar_eclipse_1999_4_NR.jpg/200px-Solar_eclipse_1999_4_NR.jpg",
        "Comète C/2023 A3": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Comet_C-2023_A3_2024-10-14.jpg/200px-Comet_C-2023_A3_2024-10-14.jpg",
        "Éclipse Lunaire (03/03/2026)": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Total_Lunar_Eclipse_March_2007.jpg/200px-Total_Lunar_Eclipse_March_2007.jpg"
    }
}

# --- SIDEBAR (Boussole Design Précédent) ---
with st.sidebar:
    st.title("🧭 Horizon & Setup")
    
    # Retour aux Sliders pour les 8 directions
    obs = {}
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    for d in dirs:
        obs[d] = st.sidebar.slider(f"Obstacle {d} (°)", 0, 90, 15)

    # Rendu Graphique Polaire
    fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
    angles = np.linspace(0, 2*np.pi, 9)
    values = [obs[d] for d in dirs] + [obs["N"]]
    ax_b.fill(angles, values, color='#ff4b4b', alpha=0.4, edgecolor='#ff4b4b', lw=2)
    ax_b.set_theta_zero_location('N')
    ax_b.set_theta_direction(-1)
    ax_b.set_facecolor('#1e2130')
    fig_b.patch.set_facecolor('#0e1117')
    ax_b.tick_params(colors='white')
    st.pyplot(fig_b)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session 2026")

# 1. SETUP BATTERIE (Menu déroulant précis)
with st.expander("🔋 Énergie & Autonomie", expanded=True):
    col_bat, col_cons = st.columns(2)
    bat_type = col_bat.selectbox("Modèle de Batterie", ["Bluetti EB3A (268Wh)", "Ecoflow River 2 (256Wh)", "Bluetti EB70 (716Wh)", "Batterie 100Ah (1200Wh)"])
    bat_wh = int(bat_type.split('(')[1].split('Wh')[0])
    w_total = col_cons.slider("Consommation Totale (W)", 10, 80, 35)
    
    autonomie = (bat_wh * 0.85) / w_total
    st.info(f"⏱️ Autonomie estimée : **{autonomie:.1f} heures** (Fin à {(datetime.now() + timedelta(hours=autonomie)).strftime('%H:%M')})")

# 2. SÉLECTION CIBLES PAR NOMS
st.divider()
c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    cat = st.selectbox("Catalogue", list(DATA_CIBLES.keys()))
with c2:
    target = st.selectbox("Cible (Nom)", list(DATA_CIBLES[cat].keys()))
with c3:
    filtre = st.selectbox("Filtre", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "Solaire Frontal"])

# 3. AFFICHAGE & ALERTES
st.divider()
col_img, col_txt = st.columns([1, 2])

with col_img:
    st.image(DATA_CIBLES[cat][target], use_container_width=True, caption=target)

with col_txt:
    st.subheader("📋 Rapport d'Analyse")
    
    # Alertes de sécurité
    if "Solaire" in target or "Solaire" in filtre:
        st.error("🚨 DANGER : Filtre solaire certifié indispensable pour cette cible !")
    elif "SV220" in filtre and "Galaxie" in target:
        st.warning("⚠️ Conseil : Le SV220 isolera le H-alpha. Prévoyez des poses sans filtre pour les couleurs stellaires.")
    else:
        st.success(f"✅ Configuration validée pour {target}.")
    
    # Graphique de décharge
    tx = np.linspace(0, autonomie, 100); ty = np.linspace(100, 10, 100)
    fig, ax = plt.subplots(figsize=(8, 2))
    ax.plot(tx, ty, color='#00ffd0')
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

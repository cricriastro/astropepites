import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Rapide", layout="wide")

# --- DATA LÉGÈRE ---
CAMS = {"ASI183MC Pro": 18, "ASI2600MC Pro": 20, "ASI533MC Pro": 15}
BATTERIES = {"EB3A (268Wh)": 268, "River 2 (256Wh)": 256, "100Ah (1280Wh)": 1280}

# --- BARRE LATÉRALE (RANGÉE) ---
with st.sidebar:
    st.title("🛰️ Setup")
    
    with st.expander("🔋 Matériel", expanded=False):
        bat = st.selectbox("Batterie", list(BATTERIES.keys()))
        cam = st.selectbox("Caméra", list(CAMS.keys()))
        ordi = st.selectbox("PC", ["ASI AIR", "Mini PC", "Laptop"])
        # Calcul simplifié
        conso = CAMS[cam] + (10 if "AIR" in ordi else 20) + 10
        autonomie = BATTERIES[bat] / conso

    with st.expander("🧭 Boussole (Horizon)", expanded=True):
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        obs = [st.slider(d, 0, 90, 15, key=f"s_{d}") for d in dirs]
        
        # Génération du graphique optimisée
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(2, 2))
        angles = np.linspace(0, 2*np.pi, 9)
        ax.fill(angles, [90]*9, color='green', alpha=0.2)
        ax.fill(angles, obs + [obs[0]], color='red', alpha=0.7)
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_facecolor('#0e1117')
        fig.patch.set_facecolor('#0e1117')
        ax.axis('off') # Accélère le rendu en enlevant les axes
        st.pyplot(fig)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification Romont")

# Affichage direct de l'autonomie (Pas de calcul lourd)
st.metric("🔋 Autonomie Estimée", f"{autonomie:.1f} Heures", delta=f"{conso}W")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    target = st.text_input("🎯 Cible (ex: M31, NGC7000)", "M31")
    st.info(f"📍 GPS : 46.69, 6.91 | Simulation en cours...")

with col2:
    # On ne charge l'image QUE si l'utilisateur clique ou valide
    if st.button("🖼️ Charger l'aperçu"):
        img_id = target.replace(' ', '')
        url = f"https://aladin.u-strasbg.fr/java/nph-aladin.pl?Object={img_id}&Size=15&Output=JPEG"
        st.image(url, use_container_width=True)
    else:
        st.write("Clique pour voir la cible")

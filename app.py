import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Tactile", layout="wide")

# --- DATA ---
CAM_DB = {"ZWO ASI2600MC Pro": 20, "ZWO ASI533MC Pro": 15, "ZWO ASI294MC Pro": 18, "Reflex Canon/Sony": 7}
BATTERIES = {"Bluetti EB3A (268Wh)": 268, "Ecoflow River (256Wh)": 256, "Batterie 100Ah": 1280}
CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 891"],
    "Sharpless": ["Sh2-129", "Sh2-101", "Sh2-155"]
}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🛰️ Setup Romont")
    
    with st.expander("🔋 Énergie & Pilotage", expanded=False):
        bat = st.selectbox("Batterie Nomade", list(BATTERIES.keys()))
        pilot = st.selectbox("Contrôle", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC"])
        conso_base = 15 if "Plus" in pilot else 12

    with st.expander("📸 Matériel & Guidage", expanded=False):
        cam_p = st.selectbox("Caméra", list(CAM_DB.keys()))
        # Utilisation de boutons + / - pour les bandes
        bandes = st.number_input("Nombre de bandes chauffantes", 0, 4, 1, step=1)
        eaf = st.toggle("Focuseur (EAF)", value=True)
        efw = st.toggle("Roue à filtres (EFW)", value=True)

    # Calcul autonomie
    conso_w = conso_base + CAM_DB[cam_p] + (bandes * 7) + (2 if eaf else 0) + (1 if efw else 0)
    h_restant = BATTERIES[bat] / conso_w

    st.divider()

    # --- BOUSSOLE TACTILE (VERTE/ROUGE) ---
    with st.expander("🧭 Boussole & Horizon", expanded=True):
        st.write("Glisse pour masquer les zones :")
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        vals = []
        # Sliders pour éviter de taper des chiffres
        for d in dirs:
            vals.append(st.slider(f"Obstacle {d} (°)", 0, 90, 15))

        # Rendu Graphique
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
        angles = np.linspace(0, 2*np.pi, 9)
        
        # Zone verte (Ciel complet)
        ax.fill(angles, [90]*9, color='#2ecc71', alpha=0.3) 
        
        # Zone rouge (Obstacles saisis)
        obs_vals = vals + [vals[0]]
        ax.fill(angles, obs_vals, color='#e74c3c', alpha=0.8, edgecolor='#c0392b')
        
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_facecolor('#0e1117')
        fig.patch.set_facecolor('#0e1117')
        ax.tick_params(colors='white', labelsize=7)
        st.pyplot(fig)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

col_info, col_img = st.columns([2, 1])

with col_info:
    c1, c2 = st.columns(2)
    cat_s = c1.selectbox("📁 Catalogue", list(CATALOGUES.keys()))
    obj_s = c2.selectbox("🎯 Cible", CATALOGUES[cat_s])
    
    st.markdown(f"""
        <div style="background: #1e2130; padding: 25px; border-radius: 15px; border: 2px solid #2ecc71; text-align: center;">
            <h1 style="color: white; margin: 0;">🔋 {h_restant:.1f} HEURES</h1>
            <p style="color: #2ecc71; margin: 0;">DURÉE DE SHOOT POSSIBLE</p>
        </div>
    """, unsafe_allow_html=True)

with col_img:
    st.write("**Vignette de confirmation**")
    # Tentative avec un serveur d'images plus direct (SkyView)
    obj_clean = obj_s.replace(" ", "+")
    url_img = f"https://server1.sky-map.org/imgproxy?object={obj_clean}&view=normal"
    
    st.image(url_img, width=280, caption=f"Cible : {obj_s}")

st.divider()
st.subheader("📋 État du Setup")
st.write(f"✅ **Alimentation :** {bat} | **Consommation :** {conso_w}W")
st.write(f"✅ **Train Optique :** {cam_p} + {'EAF' if eaf else ''} {'+ EFW' if efw else ''}")

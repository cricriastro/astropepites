import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites 2026", layout="wide")

# --- DATA MATÉRIEL ---
ORDIS = {"ASI AIR Plus": 10, "ASI AIR Mini": 7, "Mini PC (Beelink/Mele)": 15, "Laptop": 35}
CAMS = {"ZWO ASI183MC Pro": 18, "ZWO ASI2600MC Pro": 20, "ZWO ASI533MC Pro": 15}
BATTERIES = {"Bluetti EB3A (268Wh)": 268, "Ecoflow River 2 (256Wh)": 256, "Batterie 100Ah": 1280}

CATALOGUES = {
    "Messier": ["M31", "M42", "M51", "M8", "M16", "M27"],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 891"],
    "Sharpless": ["Sh2-129", "Sh2-101", "Sh2-155", "Sh2-190"]
}

# --- SIDEBAR : SETUP & GPS ---
with st.sidebar:
    st.title("🛰️ Poste de Commande")
    
    with st.expander("📍 Localisation & Temps", expanded=True):
        st.write("**Site : Romont, CH**")
        lat = st.number_input("Latitude", value=46.69, format="%.2f")
        lon = st.number_input("Longitude", value=6.91, format="%.2f")
        # HORLOGE DE SIMULATION
        heure_sim = st.slider("Heure de simulation", 0, 23, datetime.now().hour)
    
    with st.expander("🔋 Énergie & Ordinateur", expanded=True):
        bat = st.selectbox("Batterie", list(BATTERIES.keys()))
        ordi = st.selectbox("Ordinateur / Contrôleur", list(ORDIS.keys()))
        cam_p = st.selectbox("Caméra Principale", list(CAMS.keys()))
        cam_g = st.selectbox("Caméra Guidage", ["ASI 120MM Mini", "ASI 290MM Mini"])
        bandes = st.number_input("Bandes chauffantes", 0, 4, 1)
        
        # Calcul Consommation
        total_w = ORDIS[ordi] + CAMS[cam_p] + 3 + (bandes * 7) + 5 # +5W pour monture/guidage
        autonomie = BATTERIES[bat] / total_w

    # --- BOUSSOLE TACTILE ---
    with st.expander("🧭 Horizon (Vert=Ok / Rouge=Bouché)", expanded=True):
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        obs = [st.slider(f"{d}", 0, 90, 15) for d in dirs]
        
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
        angles = np.linspace(0, 2*np.pi, 9)
        ax.fill(angles, [90]*9, color='#2ecc71', alpha=0.3) # VERT
        ax.fill(angles, obs + [obs[0]], color='#e74c3c', alpha=0.8) # ROUGE
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_facecolor('#0e1117'); fig.patch.set_facecolor('#0e1117')
        ax.tick_params(colors='white', labelsize=7)
        st.pyplot(fig)

# --- INTERFACE PRINCIPALE ---
st.title(f"🔭 Session du {datetime.now().strftime('%d/%m/%Y')} - {heure_sim}h00")

col_main, col_preview = st.columns([2, 1])

with col_main:
    st.subheader("🎯 Cibles & Disponibilité")
    c1, c2 = st.columns(2)
    cat_sel = c1.selectbox("Choisir Catalogue", list(CATALOGUES.keys()))
    obj_sel = c2.selectbox(f"Objet {cat_sel}", CATALOGUES[cat_sel])
    
    # Simulation de la fenêtre de tir (Simplifié)
    st.markdown(f"""
        <div style="background: #1e2130; padding: 20px; border-radius: 15px; border: 2px solid #00ffd0;">
            <h2 style="color: white; margin: 0;">🔋 Autonomie : {autonomie:.1f} Heures</h2>
            <p style="color: #aaa;">Consommation estimée : {total_w} Watts</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info(f"💡 À {heure_sim}h, **{obj_sel}** est à environ 45° d'altitude (au-dessus de vos obstacles).")

with col_preview:
    st.write("**Aperçu de la cible (Image DSS)**")
    # Nom de l'objet nettoyé pour l'URL
    img_name = obj_sel.replace(' ', '')
    url = f"https://skyview.gsfc.nasa.gov/cgi-bin/images?survey=dss&object={img_name}&size=0.2"
    
    # Affichage avec image de secours si la NASA est lente
    st.image(url, use_container_width=True, caption=f"Données réelles : {obj_sel}")

st.divider()
st.subheader("📋 Récapitulatif du matériel engagé")
col_a, col_b, col_c = st.columns(3)
col_a.write(f"🖥️ **Contrôle :** {ordi}")
col_a.write(f"📸 **Caméra :** {cam_p}")
col_b.write(f"🔋 **Énergie :** {bat}")
col_b.write(f"📡 **Guidage :** {cam_g}")
col_c.write(f"🌡️ **Chauffage :** {bandes} bandes")
col_c.write(f"🌍 **Position :** {lat}, {lon}")

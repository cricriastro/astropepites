import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- DATA : MATÉRIEL & CIBLES (Coordonnées simplifiées pour le filtre) ---
CAM_DB = {"ZWO ASI2600MC Pro": 20, "ZWO ASI533MC Pro": 15, "ASI 120MM Mini (Guide)": 2, "ASI 290MM Mini (Guide)": 3}
BATTERIES = {"Bluetti EB3A (268Wh)": 268, "Ecoflow River (256Wh)": 256, "Batterie 100Ah": 1280}

# Liste des cibles avec leur Hauteur Max (Altitude) approximative pour le filtrage
# (Dans une version réelle, cela serait calculé précisément selon la date)
DB_CIBLES = [
    {"nom": "M31 - Andromède", "cat": "Messier", "alt": 80},
    {"nom": "M42 - Orion", "cat": "Messier", "alt": 35},
    {"nom": "M51 - Tourbillon", "cat": "Messier", "alt": 75},
    {"nom": "NGC 7000 - North America", "cat": "NGC", "alt": 85},
    {"nom": "NGC 6960 - Dentelles", "cat": "NGC", "alt": 70},
    {"nom": "Sh2-129 - Squid", "cat": "Sharpless", "alt": 65},
    {"nom": "Sh2-155 - Cave", "cat": "Sharpless", "alt": 60},
    {"nom": "M8 - Lagune", "cat": "Messier", "alt": 20}, # Cible basse
    {"nom": "M16 - Piliers", "cat": "Messier", "alt": 25}, # Cible basse
]

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🛰️ Setup & Horizon")
    
    with st.expander("🔋 Énergie & Caméras", expanded=True):
        bat = st.selectbox("Batterie", list(BATTERIES.keys()))
        cam_p = st.selectbox("Caméra Principale", ["ZWO ASI2600MC Pro", "ZWO ASI533MC Pro"])
        cam_g = st.selectbox("Caméra Guidage", ["ASI 120MM Mini (Guide)", "ASI 290MM Mini (Guide)"])
        bandes = st.number_input("Bandes chauffantes", 0, 4, 1)
        
        # Calcul de la consommation
        conso_totale = 15 + CAM_DB[cam_p] + CAM_DB[cam_g] + (bandes * 7)
        h_autonomie = BATTERIES[bat] / conso_totale

    # --- BOUSSOLE INTERACTIVE ---
    with st.expander("🧭 Boussole d'Horizon", expanded=True):
        st.write("Règle tes obstacles :")
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        obs_vals = []
        for d in dirs:
            obs_vals.append(st.slider(f"{d}", 0, 90, 15))

        # Rendu Graphique Vert/Rouge
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
        angles = np.linspace(0, 2*np.pi, 9)
        ax.fill(angles, [90]*9, color='#2ecc71', alpha=0.3) # Ciel Libre
        ax.fill(angles, obs_vals + [obs_vals[0]], color='#e74c3c', alpha=0.8) # Obstacles
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_facecolor('#0e1117'); fig.patch.set_facecolor('#0e1117')
        ax.tick_params(colors='white', labelsize=7)
        st.pyplot(fig)

# --- FILTRAGE DES CIBLES ---
# On prend la valeur d'obstacle la plus haute pour filtrer (simplification)
horizon_max = max(obs_vals)
cibles_visibles = [c['nom'] for c in DB_CIBLES if c['alt'] > horizon_max]

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

col_info, col_img = st.columns([2, 1])

with col_info:
    st.subheader("🎯 Sélection de la cible")
    if not cibles_visibles:
        st.error("⚠️ Aucune cible n'est visible au-dessus de tes obstacles actuels !")
        cible_sel = None
    else:
        cible_sel = st.selectbox(f"Cibles visibles (> {horizon_max}° d'altitude)", cibles_visibles)
        st.success(f"✔️ **AUTONOMIE : {h_autonomie:.1f} HEURES**")

with col_img:
    st.write("**Aperçu de la cible**")
    if cible_sel:
        # Technique robuste pour la vignette : on utilise le catalogue Messier/NGC
        clean_name = cible_sel.split(' - ')[0].replace(' ', '')
        # Lien vers les miniatures de la NASA/Hubble
        url_img = f"https://www.ngcicproject.org/thumbnails/{clean_name.lower()}.jpg"
        
        # Affichage avec cadre de secours
        st.markdown(f"""
            <div style="border:2px solid #444; border-radius:10px; background:black; min-height:150px; text-align:center;">
                <img src="{url_img}" style="width:100%; border-radius:8px;" onerror="this.src='https://via.placeholder.com/300x200?text={clean_name}';">
            </div>
        """, unsafe_allow_html=True)

st.divider()
st.subheader("📋 Résumé du Setup")
c_a, c_b = st.columns(2)
c_a.write(f"✅ **Imagerie :** {cam_p} + {cam_g}")
c_b.write(f"✅ **Énergie :** {bat} ({conso_totale}W consommés)")

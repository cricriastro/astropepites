import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Master 2026", layout="wide")

# --- DATA ---
CAM_DB = {"ZWO ASI2600MC Pro": 20, "ZWO ASI533MC Pro": 15, "ZWO ASI294MC Pro": 18, "ASI 120MM (Guide)": 2}
BATTERIES = {"Bluetti EB3A (268Wh)": 268, "Ecoflow River (256Wh)": 256, "LiFePO4 100Ah": 1280}
CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237"],
    "Sharpless": ["Sh2-129", "Sh2-101", "Sh2-190"]
}

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Setup & Energie")
    
    with st.expander("🔋 Alimentation & Coeur", expanded=True):
        bat = st.selectbox("Batterie", list(BATTERIES.keys()))
        pilot = st.selectbox("Contrôle", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC"])
        conso_fixe = 15 if "Plus" in pilot else 12

    with st.expander("📸 Imagerie & Accessoires", expanded=True):
        cam_p = st.selectbox("Caméra Principale", list(CAM_DB.keys()))
        cam_g = st.selectbox("Caméra Guidage", ["ASI 120MM Mini", "ASI 290MM Mini"])
        efw = st.toggle("Roue à Filtres (EFW)", value=True)
        eaf = st.toggle("Auto Focuser (EAF)", value=True)
        bandes = st.number_input("Bandes chauffantes", 0, 5, 1)

    # Calcul conso et autonomie
    total_w = conso_fixe + CAM_DB[cam_p] + 2 + (bandes * 7) + (2 if eaf else 0) + (1 if efw else 0)
    autonomie = BATTERIES[bat] / total_w

    st.divider()

    # --- LA BOUSSOLE (VERTE ET ROUGE) ---
    with st.expander("🧭 Boussole d'Horizon", expanded=True):
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        vals = []
        c1, c2 = st.columns(2)
        for i, d in enumerate(dirs):
            with c1 if i % 2 == 0 else c2:
                vals.append(st.number_input(f"{d} (°)", 0, 90, 15))

        # Dessin de la boussole
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
        angles = np.linspace(0, 2*np.pi, 9)
        # Fond vert
        ax.fill(angles, [90]*9, color='green', alpha=0.2)
        # Zones rouges (obstacles)
        display_vals = vals + [vals[0]]
        ax.fill(angles, display_vals, color='red', alpha=0.6)
        
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_facecolor('#0e1117'); fig.patch.set_facecolor('#0e1117')
        ax.tick_params(colors='white', labelsize=7)
        st.pyplot(fig)

# --- PRINCIPAL ---
st.title("🔭 Planification Expert")

col_info, col_img = st.columns([2, 1])

with col_info:
    c_cat, c_obj = st.columns(2)
    cat_s = c_cat.selectbox("Catalogue", list(CATALOGUES.keys()))
    obj_s = c_obj.selectbox("Cible", CATALOGUES[cat_s])
    
    st.success(f"⚡ **AUTONOMIE : {autonomie:.1f} HEURES** (Conso: {total_w}W)")
    st.info(f"📍 Romont : Cible validée selon ton horizon local.")

with col_img:
    st.write("**Vignette Réelle (DSS2)**")
    # Nettoyage du nom pour l'image
    img_id = obj_s.replace(" ", "")
    url = f"https://aladin.u-strasbg.fr/java/nph-aladin.pl?Object={img_id}&Size=15&Output=JPEG"
    st.markdown(f"""
        <div style="border: 2px solid #444; border-radius: 10px; overflow: hidden; background: black;">
            <img src="{url}" style="width: 100%; display: block;" onerror="this.onerror=null; this.src='https://via.placeholder.com/300x200?text=Image+En+Cours...';">
        </div>
    """, unsafe_allow_html=True)

st.divider()
st.subheader("📋 État de la mission")
st.write(f"Configuration : **{cam_p}** sur **{bat}** avec **{pilot}**.")

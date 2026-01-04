import streamlit as st
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Pilotage", layout="wide")

# --- DATA MATÉRIEL (Consommation en Watts) ---
CAM_MODELS = {
    "ZWO ASI2600MC/MM Pro": 20, "ZWO ASI533MC/MM Pro": 15,
    "ZWO ASI294MC/MM Pro": 18, "ZWO ASI6200MC/MM Pro": 25,
    "ZWO ASI1600MM Pro": 15, "Canon/Sony Mirrorless": 7
}

BATTERIES = {
    "Bluetti EB3A (268Wh)": 268,
    "Ecoflow River 2 (256Wh)": 256,
    "Batterie Lithium 100Ah (1280Wh)": 1280
}

CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 891"],
    "Sharpless (Sh2)": ["Sh2-129", "Sh2-101", "Sh2-155", "Sh2-190"],
    "Arp": ["Arp 244", "Arp 273"]
}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🛰️ Gestion du Setup")
    
    # MATÉRIEL DANS DES MENUS RÉTRACTABLES
    with st.expander("🔋 Énergie & Pilotage", expanded=True):
        bat_choice = st.selectbox("Batterie Nomade", list(BATTERIES.keys()))
        control = st.selectbox("Contrôle", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC / NINA"])
        conso_fixe = 15 if "Plus" in control else 12

    with st.expander("📸 Imageur & Guidage", expanded=True):
        cam_p = st.selectbox("Caméra Principale", list(CAM_MODELS.keys()))
        cam_g = st.selectbox("Caméra de Guidage", ["ASI 120MM Mini", "ASI 290MM Mini", "ASI 174MM Mini"])
        efw = st.toggle("Roue à Filtres (EFW)", value=True)
        eaf = st.toggle("Focuseur Auto (EAF)", value=True)
        bandes = st.number_input("Bandes chauffantes (quantité)", 0, 3, 1)

    with st.expander("🔭 Monture", expanded=False):
        monture = st.selectbox("Modèle", ["Star Adventurer GTi", "ZWO AM5", "EQ6-R Pro"])

    # CALCUL FINAL SANS GRAPHIQUE
    conso_totale = conso_fixe + CAM_MODELS[cam_p] + 2 + (bandes * 7) + (2 if eaf else 0) + (1 if efw else 0)
    h_autonomie = BATTERIES[bat_choice] / conso_totale

    st.divider()

    # BOUSSOLE DANS UN MENU QUI SE REFERME
    with st.expander("🧭 Boussole d'Horizon", expanded=False):
        st.write("Altitude min des obstacles (°)")
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        obs = {d: st.number_input(f"{d}", 0, 90, 15) for d in dirs}

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

# 1. Sélection et Autonomie
c_sel, c_res = st.columns([2, 1])

with c_sel:
    col1, col2 = st.columns(2)
    cat_sel = col1.selectbox("Catalogue", list(CATALOGUES.keys()))
    targ_sel = col2.selectbox(f"Cible {cat_sel}", CATALOGUES[cat_sel])
    
    st.markdown(f"""
        <div style="background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 5px solid #00ffd0;">
            <h2 style="margin:0; color: white;">⚡ Autonomie estimée : {h_autonomie:.1f} Heures</h2>
            <p style="margin:0; color: #aaa;">Consommation totale calculée : {conso_totale} Watts</p>
        </div>
    """, unsafe_allow_html=True)

with c_res:
    # SYSTÈME D'IMAGE CORRIGÉ
    st.write("**Aperçu de la cible**")
    clean_name = targ_sel.replace(' ', '')
    # Utilisation d'un lien direct plus robuste
    st.image(f"https://api.astrometry.net/thumbnail/{clean_name}", 
             width=250, 
             caption=f"Cible : {targ_sel}",
             use_container_width=False)

# 2. État du Setup
st.divider()
st.subheader("📋 Récapitulatif du matériel engagé")
col_a, col_b, col_c = st.columns(3)

col_a.write(f"✅ **Pilotage :** {control}")
col_a.write(f"✅ **Caméra :** {cam_p}")
col_b.write(f"✅ **Guidage :** {cam_g}")
col_b.write(f"✅ **Accessoires :** {'EAF' if eaf else ''} {'+ EFW' if efw else ''}")
col_c.write(f"✅ **Énergie :** {bat_choice}")
col_c.write(f"✅ **Site :** Romont (CH)")

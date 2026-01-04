import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Setup Complet", layout="wide")

# --- 1. CATALOGUES ---
CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 891", "NGC 4565"],
    "Sharpless (Sh2)": [f"Sh2-{i}" for i in [1, 101, 129, 155, 190, 240]],
    "Arp (Galaxies)": [f"Arp {i}" for i in [244, 188, 273, 297]],
}

# --- 2. BARRE LATÉRALE : GESTION TOTALE DU MATÉRIEL ---
with st.sidebar:
    st.title("⚙️ Configuration Setup")
    
    # --- SECTION ÉNERGIE & PILOTAGE ---
    with st.expander("⚡ Énergie & Intelligence", expanded=True):
        batterie = st.selectbox("Batterie", ["Bluetti EB3A (268Wh)", "Ecoflow River 2", "Batterie Marine 100Ah"])
        pilotage = st.radio("Contrôle", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC (NINA)"], horizontal=True)
        st.caption("Consommation estimée : 25-35W")

    # --- SECTION IMAGERIE (Caméra & Filtres) ---
    with st.expander("📸 Train Imageur", expanded=False):
        cam_principale = st.selectbox("Caméra Principale", ["ZWO ASI2600MC Pro", "ZWO ASI533MC Pro", "ZWO ASI294MC"])
        filtres = st.multiselect("Filtres en stock", ["Clair / UV-IR", "Svbony SV220", "Optolong L-Pro", "L-Extreme"], default=["Clair / UV-IR"])
        st.checkbox("Bande chauffante (Caméra)", value=True)

    # --- SECTION GUIDAGE & FOCUS ---
    with st.expander("🎯 Guidage & Focus", expanded=False):
        cam_guidage = st.selectbox("Caméra Guidage", ["ZWO ASI120MM Mini", "ZWO ASI290MM Mini"])
        focuseur = st.toggle("EAF (Auto Focuser) actif", value=True)
        st.checkbox("Bande chauffante (Lunette guide)", value=False)

    # --- SECTION MONTURE ---
    with st.expander("🔭 Monture & Mécanique", expanded=False):
        monture = st.selectbox("Monture", ["Star Adventurer GTi", "ZWO AM5", "EQ6-R Pro"])
        st.info(f"Site : Romont (46.65, 6.91)")

    # --- BOUSSOLE (Toujours visible pour sécurité) ---
    st.divider()
    st.subheader("🧭 Horizon Local")
    dirs = ["N", "E", "S", "O"]
    obs = {d: st.number_input(f"Obstacle {d} (°)", 0, 90, 15) for d in dirs}

# --- 3. INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

col_sel, col_vignette, col_conseil = st.columns([1.5, 1, 1])

with col_sel:
    cat = st.selectbox("📁 Choisir Catalogue", list(CATALOGUES.keys()))
    target = st.selectbox(f"🎯 Cible dans {cat}", CATALOGUES[cat])

with col_vignette:
    # LA VIGNETTE CHANGE MAINTENANT !
    # On simule un changement d'aspect selon le catalogue
    style = "radial-gradient(circle, #2e3141 0%, #0e1117 100%)"
    if "Sharpless" in cat: style = "radial-gradient(circle, #4a1111 0%, #0e1117 100%)"
    if "Arp" in cat: style = "radial-gradient(circle, #11224a 0%, #0e1117 100%)"
    
    st.markdown(f"""
        <div style="height: 120px; border: 2px solid #555; border-radius: 15px; 
                    background: {style}; display: flex; align-items: center; justify-content: center; flex-direction: column;">
            <span style="font-size: 40px;">{'✨' if 'M' in target else '🌀'}</span>
            <b style="color: white;">{target}</b>
        </div>
    """, unsafe_allow_html=True)

with col_conseil:
    if "Sharpless" in cat or "NGC 7000" in target:
        st.warning("💡 Conseil : **SV220** requis")
    else:
        st.info("💡 Conseil : **Filtre Clair**")

# --- 4. ANALYSE DE LA SESSION ---
st.divider()
c_rep, c_graph = st.columns([1, 1.5])

with c_rep:
    st.subheader("📋 État du Setup")
    st.write(f"✅ **Pilotage :** {pilotage}")
    st.write(f"✅ **Imagerie :** {cam_principale}")
    st.write(f"✅ **Guidage :** {cam_guidage} + {'EAF' if focuseur else 'Manuel'}")
    st.write(f"✅ **Monture :** {monture}")
    st.caption(f"Autonomie estimée sur {batterie} : ~7.5h")

with c_graph:
    # Courbe de batterie simplifiée
    t = np.linspace(0, 10, 100)
    b = np.exp(-t/15) * 100
    fig, ax = plt.subplots(figsize=(6, 2.5))
    ax.plot(t, b, color="#00ffd0")
    ax.set_title("Décharge théorique (%)", color="white", fontsize=10)
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white', labelsize=8)
    st.pyplot(fig)

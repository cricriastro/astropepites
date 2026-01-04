import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Master", layout="wide")

# --- DATA : CAMÉRAS (Conso en Watts) ---
CAM_DB = {
    "ZWO ASI2600MC/MM Pro": 20.0, "ZWO ASI533MC/MM Pro": 15.0,
    "ZWO ASI294MC/MM Pro": 18.0, "ZWO ASI1600MM Pro": 15.0,
    "ZWO ASI6200MC/MM Pro": 25.0, "Sony A7III / Canon R6": 5.0
}

CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 891", "NGC 4565"],
    "Sharpless (Sh2)": [f"Sh2-{i}" for i in [1, 101, 129, 155, 190, 240]],
    "Arp": ["Arp 244", "Arp 188", "Arp 273"]
}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🛠️ Mon Setup")
    
    with st.expander("🔋 Énergie & Pilotage", expanded=True):
        bat_type = st.selectbox("Batterie", ["Bluetti EB3A (268Wh)", "Ecoflow River (256Wh)", "100Ah Deep Cycle"])
        wh_total = 268 if "EB3A" in bat_type else (256 if "River" in bat_type else 1200)
        pilotage = st.selectbox("Contrôle", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC"])
        conso_fixe = 12 if "Mini" in pilotage else 18 # Watts (inclut monture idle)

    with st.expander("📸 Train Optique & Focus", expanded=True):
        cam = st.selectbox("Caméra Principale", list(CAM_DB.keys()))
        efw = st.toggle("Roue à Filtres (EFW)", value=True)
        eaf = st.toggle("Auto Focuser (EAF)", value=True)
        bandes = st.number_input("Nombre de bandes chauffantes", 0, 3, 1)
        
        # Calcul de la consommation dynamique
        conso_setup = conso_fixe + CAM_DB[cam] + (bandes * 7) + (2 if eaf else 0) + (1 if efw else 0)
        autonomie = wh_total / conso_setup

    st.divider()
    
    # --- BOUSSOLE (Graphique au-dessus des réglages) ---
    st.subheader("🧭 Horizon Local")
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    
    # Initialisation des valeurs (par défaut 15°)
    if 'obs' not in st.session_state:
        st.session_state.obs = {d: 15 for d in dirs}

    # Affichage du graphique EN PREMIER
    fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
    angles = np.linspace(0, 2*np.pi, 9)
    vals = [st.session_state.obs[d] for d in dirs] + [st.session_state.obs["N"]]
    ax_b.fill(angles, vals, color='#ff4b4b', alpha=0.4, edgecolor='#ff4b4b')
    ax_b.set_theta_zero_location('N')
    ax_b.set_theta_direction(-1)
    ax_b.set_facecolor('#1e2130'); fig_b.patch.set_facecolor('#0e1117')
    ax_b.tick_params(colors='white', labelsize=7)
    st.pyplot(fig_b)

    # Réglages EN DESSOUS
    c1, c2 = st.columns(2)
    for i, d in enumerate(dirs):
        with c1 if i % 2 == 0 else c2:
            st.session_state.obs[d] = st.number_input(f"{d} (°)", 0, 90, st.session_state.obs[d])

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

col_sel, col_img = st.columns([2, 1])

with col_sel:
    c_cat, c_targ = st.columns(2)
    cat_sel = c_cat.selectbox("Catalogue", list(CATALOGUES.keys()))
    targ_sel = c_targ.selectbox(f"Cible {cat_sel}", CATALOGUES[cat_sel])
    
    st.metric("Consommation Totale", f"{conso_setup} W")
    st.info(f"⏳ Autonomie estimée : **{autonomie:.1f} heures** à Romont.")

with col_img:
    # SYSTÈME DE VIGNETTE ROBUSTE
    st.write("**Aperçu de la cible**")
    clean_name = targ_sel.replace(' ', '')
    img_url = f"https://aladin.u-strasbg.fr/java/nph-aladin.pl?Object={clean_name}&Size=15&Output=JPEG"
    
    # Tentative d'affichage avec un "alt" si l'image est lente
    st.markdown(f"""
        <div style="background: #1e2130; border-radius: 10px; padding: 5px; text-align: center; border: 1px solid #444;">
            <img src="{img_url}" style="width: 100%; border-radius: 5px;" onerror="this.parentElement.innerHTML='<br>🔭<br>Image en cours...<br><br>';">
        </div>
    """, unsafe_allow_html=True)

# --- GRAPH DE DÉCHARGE ---
st.divider()
t = np.linspace(0, autonomie, 100)
b = np.linspace(100, 0, 100)
fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(t, b, color="#00ffd0", lw=3)
ax.fill_between(t, b, color="#00ffd0", alpha=0.1)
ax.set_title(f"Courbe de décharge théorique ({bat_type})", color="white")
ax.set_ylabel("% Batterie")
ax.set_xlabel("Heures")
ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
ax.tick_params(colors='white')
st.pyplot(fig)

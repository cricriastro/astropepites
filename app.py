import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Expert 2026", layout="wide")

# --- DATA : CAMÉRAS & CONSOMMATION (Watts) ---
CAM_DB = {
    "ZWO ASI2600MC/MM Pro": 20.0, "ZWO ASI533MC/MM Pro": 15.0,
    "ZWO ASI294MC/MM Pro": 18.0, "ZWO ASI1600MM Pro": 15.0,
    "ZWO ASI071MC Pro": 22.0, "ZWO ASI6200MC/MM Pro": 25.0,
    "Sony A7III / Canon R6 (DSLR)": 5.0, "ASI 120MM/290MM (Non refroidie)": 2.0
}

CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 891", "NGC 4565", "NGC 6946"],
    "Sharpless (Sh2)": [f"Sh2-{i}" for i in [1, 101, 129, 155, 190, 240, 276]],
    "Abell (Planétaires)": [f"Abell {i}" for i in [21, 31, 33, 39, 70, 85]],
    "Arp (Galaxies)": [f"Arp {i}" for i in [244, 188, 273, 297]]
}

# --- SIDEBAR : CONFIGURATION SETUP ---
with st.sidebar:
    st.title("🛠️ Mon Setup")
    
    with st.expander("🔋 Énergie & Pilotage", expanded=True):
        bat_capa = st.selectbox("Batterie Nomade", ["Bluetti EB3A (268Wh)", "Ecoflow River 2 (256Wh)", "Batterie 100Ah (1200Wh)"], index=0)
        wh_total = 268 if "EB3A" in bat_capa else (256 if "River" in bat_capa else 1200)
        pilotage = st.selectbox("Contrôle", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC (NINA)"])
        conso_base = 15 if "Plus" in pilotage else 10 # Conso ASI AIR + Monture idle

    with st.expander("📸 Imagerie & Guidage", expanded=True):
        cam_model = st.selectbox("Caméra Principale", list(CAM_DB.keys()))
        conso_cam = CAM_DB[cam_model]
        bandes = st.multiselect("Bandes Chauffantes", ["Lunette Principale", "Lunette Guide"])
        conso_bandes = len(bandes) * 7 # Env 7W par bande
        eaf = st.toggle("Focusser Auto (EAF)", value=True)

    with st.expander("🔭 Monture", expanded=False):
        monture = st.selectbox("Modèle", ["Star Adventurer GTi", "ZWO AM5", "EQ6-R Pro"])

    # CALCUL AUTONOMIE
    conso_totale = conso_base + conso_cam + conso_bandes + (2 if eaf else 0)
    autonomie = wh_total / conso_totale

    st.divider()
    # --- BOUSSOLE RETOUR ---
    st.subheader("🧭 Boussole d'Horizon")
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    obs = {d: st.number_input(f"{d} (°)", 0, 90, 15, key=f"bous_{d}") for d in dirs}

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification Expert : Romont")

# 1. SÉLECTION CIBLE
c1, c2 = st.columns([2, 1])
with c1:
    col_cat, col_targ = st.columns(2)
    cat_sel = col_cat.selectbox("Catalogue", list(CATALOGUES.keys()))
    targ_sel = col_targ.selectbox(f"Objet {cat_sel}", CATALOGUES[cat_sel])
    
    st.info(f"⚡ **Estimation Énergie :** Consommation de **{conso_totale}W**. Autonomie théorique de **{autonomie:.1f} heures**.")

with c2:
    # LA VRAIE VIGNETTE (Via Aladin Lite / DSS2)
    st.write("**Vraie image (DSS2/Archives)**")
    # On nettoie le nom pour l'URL
    img_name = targ_sel.replace(' ', '')
    st.image(f"https://aladin.u-strasbg.fr/java/nph-aladin.pl?Object={img_name}&Size=20&Output=JPEG", 
             use_container_width=True, caption=f"Données réelles : {targ_sel}")

# 2. ANALYSE ET GRAPH DE DÉCHARGE
st.divider()
res_col, graph_col = st.columns([1, 2])

with res_col:
    st.subheader("📋 Rapport de Mission")
    st.write(f"✅ **Cible :** {targ_sel}")
    st.write(f"✅ **Setup :** {cam_model} / {monture}")
    if autonomie < 4:
        st.error(f"⚠️ Batterie faible pour une nuit complète !")
    else:
        st.success(f"✔️ Prêt pour une session de {autonomie:.1f}h")

    # Petit rappel Boussole visuel
    fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(2, 2))
    angles = np.linspace(0, 2*np.pi, 9)
    ax_b.fill(angles, [obs[d] for d in dirs] + [obs["N"]], color='red', alpha=0.3)
    ax_b.set_facecolor('#0e1117'); fig_b.patch.set_facecolor('#0e1117')
    ax_b.set_yticklabels([]); ax_b.set_xticklabels([])
    st.pyplot(fig_b)

with graph_col:
    # Graphique de décharge basé sur ton matériel réel
    time_axis = np.linspace(0, autonomie, 100)
    batt_axis = np.linspace(100, 0, 100)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(time_axis, batt_axis, color='#00ffd0', lw=3)
    ax.fill_between(time_axis, batt_axis, color='#00ffd0', alpha=0.1)
    ax.set_ylabel("% Batterie")
    ax.set_xlabel("Heures de shooting")
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

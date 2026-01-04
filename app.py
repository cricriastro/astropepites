import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Planificateur Expert", layout="wide")

# --- DATA MATÉRIEL (Listes complètes) ---
EQUIPEMENT = {
    "Batteries": {
        "Bluetti EB3A (268Wh)": 268,
        "Bluetti EB70 (716Wh)": 716,
        "Ecoflow River 2 (256Wh)": 256,
        "Ecoflow River 2 Max (512Wh)": 512,
        "Jackery Explorer 240 (240Wh)": 240,
        "Batterie Marine / AGM 100Ah (1200Wh)": 1200
    },
    "Montures": ["Star Adventurer GTi", "HEQ5 Pro", "EQ6-R Pro", "AM5 ZWO", "ZWO AM3", "Sky-Watcher EQ8-R"],
    "Caméras": ["ZWO ASI2600MM/MC Pro", "ZWO ASI533MM/MC Pro", "ZWO ASI294MM/MC Pro", "ZWO ASI1600MM Pro", "Canon/Nikon DSLR", "Sony Alpha (Mirrorless)"]
}

# --- FONCTION MÉTÉO ---
def get_weather():
    api_key = "16f68f1e07fea20e39f52de079037925"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat=46.65&lon=6.91&appid={api_key}&units=metric"
    try:
        return requests.get(url).json()['list'][:8]
    except: return None

# --- SIDEBAR : TÉLÉMÉTRIE COMPACTE ---
with st.sidebar:
    st.title("📡 État du Ciel")
    
    # Météo verticale compacte
    forecast = get_weather()
    if forecast:
        for s in forecast[:5]:
            h = datetime.fromtimestamp(s['dt']).strftime('%H:%M')
            n = s['clouds']['all']
            st.write(f"{'🟢' if n<20 else '🟡' if n<50 else '🔴'} **{h}** : {n}% nuages")

    st.divider()
    st.title("🧭 Boussole & Horizon")
    # Boussole simplifiée
    h_n = st.number_input("Obstacle Nord (°)", 0, 90, 15)
    h_s = st.number_input("Obstacle Sud (°)", 0, 90, 15)
    st.caption("Coordonnées : Romont (46.65, 6.91)")

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Configuration de la Session")

# 1. MENUS DÉROULANTS MATÉRIEL
with st.expander("⚙️ Sélection du Matériel", expanded=True):
    col_mat1, col_mat2, col_mat3 = st.columns(3)
    
    with col_mat1:
        mnt_choice = st.selectbox("Ma Monture", EQUIPEMENT["Montures"])
        cam_choice = st.selectbox("Ma Caméra", EQUIPEMENT["Caméras"])
        
    with col_mat2:
        bat_choice = st.selectbox("Ma Batterie Nomade", list(EQUIPEMENT["Batteries"].keys()))
        bat_cap = EQUIPEMENT["Batteries"][bat_choice]
        w_cons = st.slider("Consommation estimée (Watts)", 5, 100, 30)
        
    with col_mat3:
        # Calcul précis de l'autonomie
        autonomie = (bat_cap * 0.80) / w_cons # 80% de décharge max pour sécurité
        h_fin = datetime.now() + timedelta(hours=autonomie)
        st.metric("Autonomie estimée", f"{autonomie:.1f} h")
        st.info(f"Coupure à : {h_fin.strftime('%H:%M')}")

# 2. SÉLECTION CIBLE (TOUS CATALOGUES)
st.divider()
st.subheader("🎯 Cibles & Catalogues")
c1, c2, c3 = st.columns([1, 1, 2])

with c1:
    cat_type = st.selectbox("Catalogue", ["Messier (M)", "NGC", "IC", "Sharpless (Sh2)", "Caldwell (C)", "Comètes / Spécial"])
with c2:
    if "Comètes" in cat_type:
        target = st.selectbox("Événement", ["C/2023 A3 (Tsuchinshan)", "Perséides", "Éclipse Solaire", "Lune"])
    else:
        num = st.number_input(f"Numéro {cat_type}", 1, 8000, 31)
        target = f"{cat_type} {num}"
with c3:
    filtre = st.selectbox("Filtre installé", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut", "Filtre Solaire"])

# 3. ANALYSE ET ALERTES
st.divider()
col_txt, col_vis = st.columns([2, 1])

with col_txt:
    st.subheader("📋 Rapport d'Analyse")
    
    # Système d'alertes dynamique
    if "SV220" in filtre:
        if "M 31" in target or "M 51" in target or "NGC" in target:
            st.warning("⚠️ **Conseil Expert** : Le SV220 est génial pour isoler le H-alpha dans les galaxies. Mixez vos images avec du 'Sans Filtre' pour un rendu naturel.")
        elif "C/" in target or "Amas" in cat_type:
            st.error("❌ **Incompatible** : Ce filtre bloque le signal des comètes. Utilisez 'Sans Filtre'.")
            
    elif "Sans Filtre" in filtre and ("Solaire" in target or "Soleil" in target):
        st.error("🚨 **DANGER CRITIQUE** : Pas de visée solaire sans filtre frontal ! Risque de destruction du capteur.")
    
    else:
        st.success(f"✅ Configuration validée pour {target} avec {filtre}.")

with col_vis:
    # Petite vignette placeholder
    st.image("https://via.placeholder.com/200x120.png?text=Aperçu+Cible", caption=target)

# 4. GRAPHIQUE DE DÉCHARGE
tx = np.linspace(0, autonomie, 100); ty = np.linspace(100, 10, 100)
fig, ax = plt.subplots(figsize=(10, 2))
ax.plot(tx, ty, color='#00ffd0', lw=2)
ax.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
ax.tick_params(colors='white')
st.pyplot(fig)

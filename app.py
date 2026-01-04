import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Précision Horizon", layout="wide")

# --- DATA CATALOGUES & VIGNETTES ---
# On utilise l'API Astrobin ou des miniatures Wikimedia pour les vignettes
CIBLES_DB = {
    "Messier": {
        "M31": {"alt": 72, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/M31_09-01-2011_%28C9.25%29.jpg/150px-M31_09-01-2011_%28C9.25%29.jpg"},
        "M42": {"alt": 45, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_180px.jpg/150px-Orion_Nebula_-_Hubble_2006_mosaic_180px.jpg"},
        "M45": {"alt": 65, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Pleiades_large.jpg/150px-Pleiades_large.jpg"}
    },
    "NGC": {
        "NGC 7000": {"alt": 50, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/NGC7000_The_North_America_Nebula.jpg/150px-NGC7000_The_North_America_Nebula.jpg"},
        "NGC 6960": {"alt": 35, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/The_Witch%27s_Broom_Nebula.jpg/150px-The_Witch%27s_Broom_Nebula.jpg"}
    }
}

# --- FONCTION MÉTÉO ---
def get_weather():
    api_key = "16f68f1e07fea20e39f52de079037925"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat=46.65&lon=6.91&appid={api_key}&units=metric"
    try: return requests.get(url).json()['list'][:6]
    except: return None

# --- SIDEBAR : TÉLÉMÉTRIE & BOUSSOLE 8 DIRECTIONS ---
with st.sidebar:
    st.title("🛰️ État du Ciel")
    forecast = get_weather()
    if forecast:
        for s in forecast:
            h = datetime.fromtimestamp(s['dt']).strftime('%H:%M')
            n = s['clouds']['all']
            st.write(f"{'🟢' if n<20 else '🔴'} **{h}** : {n}% nuages")

    st.divider()
    st.title("🧭 Boussole d'Horizon")
    st.caption("Élévation min des obstacles (°)")
    
    # Les 8 directions pour une précision maximale
    col_obs1, col_obs2 = st.columns(2)
    with col_obs1:
        obs_n = st.slider("Nord", 0, 90, 15)
        obs_ne = st.slider("N-Est", 0, 90, 10)
        obs_e = st.slider("Est", 0, 90, 20)
        obs_se = st.slider("S-Est", 0, 90, 25)
    with col_obs2:
        obs_s = st.slider("Sud", 0, 90, 30)
        obs_so = st.slider("S-Ouest", 0, 90, 20)
        obs_o = st.slider("Ouest", 0, 90, 15)
        obs_no = st.slider("N-Ouest", 0, 90, 10)

    # Graphique Polaire 8 Points
    fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
    # Angles pour N, NE, E, SE, S, SO, O, NO, N
    angles = np.linspace(0, 2*np.pi, 9)
    # On réorganise les valeurs pour correspondre au sens horaire (N=0)
    values = [obs_n, obs_ne, obs_e, obs_se, obs_s, obs_so, obs_o, obs_no, obs_n]
    
    ax_b.fill(angles, values, color='#ff4b4b', alpha=0.4, edgecolor='#ff4b4b', lw=2)
    ax_b.set_theta_zero_location('N')
    ax_b.set_theta_direction(-1) # Sens horaire
    ax_b.set_thetagrids(np.degrees(angles[:-1]), labels=['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'])
    ax_b.set_facecolor('#1e2130')
    fig_b.patch.set_facecolor('#0e1117')
    ax_b.tick_params(colors='white')
    st.pyplot(fig_b)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification Pro")

# 1. MATÉRIEL & BATTERIE
with st.expander("🔋 Énergie & Setup", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        bat_wh = st.selectbox("Batterie Nomade", [256, 268, 512, 716, 1200], format_func=lambda x: f"{x} Wh")
    with c2:
        w_total = st.slider("Consommation Totale (W)", 10, 80, 35)
    with c3:
        autonomie = (bat_wh * 0.85) / w_total
        st.metric("Autonomie", f"{autonomie:.1f} h", delta=f"Fin: {(datetime.now()+timedelta(hours=autonomie)).strftime('%H:%M')}")

# 2. CATALOGUES & VIGNETTES
st.divider()
col_sel1, col_sel2, col_vignette = st.columns([1, 1, 1])

with col_sel1:
    cat = st.selectbox("Catalogue", list(CIBLES_DB.keys()))
with col_sel2:
    # Filtrage intelligent : on ne montre que ce qui est "shootable"
    target = st.selectbox("Cible", list(CIBLES_DB[cat].keys()))
with col_vignette:
    # Affichage de la vignette réelle
    st.image(CIBLES_DB[cat][target]["img"], width=150, caption=f"Aperçu {target}")

# 3. ANALYSE & ALERTES
st.divider()
col_txt, col_graph = st.columns([1, 1])

with col_txt:
    st.subheader("📋 Analyse du Shooting")
    filtre = st.selectbox("Filtre installé", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])
    
    # Alertes dynamiques
    if "SV220" in filtre and "M31" in target:
        st.warning("⚠️ **Mode Expert** : Le SV220 est parfait pour les nébuleuses rouges de M31. Prévoyez du 'Sans Filtre' pour la structure.")
    elif "Sans Filtre" in filtre:
        st.success(f"✅ **Signal Continu** : Configuration idéale pour {target}.")

with col_graph:
    # Courbe de batterie
    tx = np.linspace(0, autonomie, 100); ty = np.linspace(100, 10, 100)
    fig_d, ax_d = plt.subplots(figsize=(8, 2.5))
    ax_d.plot(tx, ty, color='#00ffd0', lw=2)
    ax_d.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
    ax_d.set_facecolor("#0e1117"); fig_d.patch.set_facecolor("#0e1117")
    ax_d.tick_params(colors='white')
    st.pyplot(fig_d)

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Horizon & Visibilité", layout="wide")

# --- DATA & CATALOGUES ---
BATTERIES = {
    "Bluetti EB3A (268Wh)": 268, "Bluetti EB70 (716Wh)": 716,
    "Ecoflow River 2 (256Wh)": 256, "Batterie 100Ah AGM (1200Wh)": 1200
}

# Simulation d'une base de données avec visibilité (Altitude simplifiée pour l'exemple)
CIBLES_DATA = {
    "Messier": {"M31": 70, "M42": 45, "M45": 60, "M51": 30, "M81": 55},
    "NGC": {"NGC 7000": 40, "NGC 6960": 35, "NGC 2237": 20},
    "IC": {"IC 434": 25, "IC 1396": 50},
    "Sharpless": {"Sh2-155": 45, "Sh2-101": 30}
}

# --- FONCTION MÉTÉO ---
def get_weather():
    api_key = "16f68f1e07fea20e39f52de079037925"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat=46.65&lon=6.91&appid={api_key}&units=metric"
    try: return requests.get(url).json()['list'][:6]
    except: return None

# --- SIDEBAR : TÉLÉMÉTRIE & BOUSSOLE D'HORIZON ---
with st.sidebar:
    st.title("🛰️ État du Ciel")
    
    # Météo
    forecast = get_weather()
    if forecast:
        for s in forecast:
            h = datetime.fromtimestamp(s['dt']).strftime('%H:%M')
            n = s['clouds']['all']
            st.write(f"{'🟢' if n<20 else '🔴'} **{h}** : {n}% nuages")

    st.divider()
    st.title("🧭 Boussole d'Horizon")
    st.caption("Zones bouchées (Altitude min)")
    obs_n = st.slider("Nord (°)", 0, 90, 20)
    obs_e = st.slider("Est (°)", 0, 90, 10)
    obs_s = st.slider("Sud (°)", 0, 90, 30)
    obs_w = st.slider("Ouest (°)", 0, 90, 15)

    # Affichage de la Boussole
    fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
    angles = [0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi]
    values = [obs_n, obs_e, obs_s, obs_w, obs_n]
    ax_b.fill(angles, values, color='red', alpha=0.3)
    ax_b.set_yticklabels([])
    ax_b.set_facecolor('#1e2130')
    fig_b.patch.set_facecolor('#0e1117')
    ax_b.tick_params(colors='white')
    st.pyplot(fig_b)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

# 1. MATÉRIEL & BATTERIE
with st.expander("⚙️ Configuration du Matériel", expanded=True):
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        bat_choice = st.selectbox("Batterie", list(BATTERIES.keys()))
        w_cons = st.slider("Consommation (W)", 10, 80, 35)
    with c_m2:
        cam_choice = st.selectbox("Caméra", ["ZWO ASI2600MC", "ZWO ASI294MC", "DSLR"])
        focale = st.number_input("Focale (mm)", 50, 2000, 400)
    with c_m3:
        autonomie = (BATTERIES[bat_choice] * 0.8) / w_cons
        st.metric("Autonomie", f"{autonomie:.1f} h")
        st.caption(f"Fin de session : {(datetime.now() + timedelta(hours=autonomie)).strftime('%H:%M')}")

# 2. CATALOGUES & CIBLES VISIBLES
st.divider()
st.subheader("🎯 Cibles Visibles (Depuis Romont)")
c1, c2, c3 = st.columns([1, 1, 2])

with c1:
    cat = st.selectbox("Catalogue", list(CIBLES_DATA.keys()))
with c2:
    # Filtrage : On ne montre que les cibles au-dessus de l'horizon moyen (ex: 20°)
    cibles_dispo = [name for name, alt in CIBLES_DATA[cat].items() if alt > 20]
    target = st.selectbox("Cible", cibles_dispo)
with c3:
    filtre = st.selectbox("Filtre", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])

# 3. ANALYSE & VIGNETTE
col_vignette, col_analyse = st.columns([1, 2])

with col_vignette:
    # Vignette simulée (Remplace par tes vrais chemins d'images si besoin)
    st.image(f"https://via.placeholder.com/300x200.png?text={target}", caption=f"Aperçu {target}")

with col_analyse:
    st.subheader("📋 Rapport d'Analyse")
    
    # Alertes intelligentes
    alt_cible = CIBLES_DATA[cat][target]
    if alt_cible < 30:
        st.warning(f"⚠️ **Altitude Basse ({alt_cible}°)** : Risque de turbulence atmosphérique important.")
    
    if "SV220" in filtre and ("M31" in target or "M51" in target):
        st.info("💡 **Conseil** : Le SV220 isolera les régions H-alpha. Cumulez avec des poses 'Sans Filtre'.")
    elif "Sans Filtre" in filtre and "M42" in target:
        st.success("✅ **Signal optimal** : Parfait pour capturer les extensions gazeuses et les poussières.")
    else:
        st.success(f"✅ Configuration validée pour {target}.")

# 4. GRAPHIQUE D'AUTONOMIE
st.divider()
tx = np.linspace(0, autonomie, 100); ty = np.linspace(100, 10, 100)
fig, ax = plt.subplots(figsize=(12, 2))
ax.plot(tx, ty, color='#00ffd0', lw=2)
ax.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
ax.tick_params(colors='white')
st.pyplot(fig)

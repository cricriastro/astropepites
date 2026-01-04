import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Master 2026", layout="wide")

# --- STYLE VISUEL ---
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 8px; border: 1px solid #3e445b; }
    .stAlert { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES CIBLES & VIGNETTES ---
# Note : Les liens d'images sont des exemples, tu pourras les personnaliser.
CATALOGUES = {
    "🌌 Messier (Galaxies/Nébuleuses)": {
        "M31 Andromède": {"type": "Galaxie", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/M31_09-01-2011_%28C9.25%29.jpg/150px-M31_09-01-2011_%28C9.25%29.jpg", "hint": "Ha possible"},
        "M42 Orion": {"type": "Nébuleuse", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_180px.jpg/150px-Orion_Nebula_-_Hubble_2006_mosaic_180px.jpg", "hint": "Ha/OIII"},
        "M45 Pléiades": {"type": "Amas", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Pleiades_large.jpg/150px-Pleiades_large.jpg", "hint": "Continu"},
        "M51 Tourbillon": {"type": "Galaxie", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Messier51_sRGB.jpg/150px-Messier51_sRGB.jpg", "hint": "Ha possible"}
    },
    "☄️ Événements & Comètes": {
        "C/2023 A3 (Tsuchinshan)": {"type": "Comète", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Comet_C-2023_A3_2024-10-14.jpg/150px-Comet_C-2023_A3_2024-10-14.jpg", "hint": "Continu"},
        "Pluie de Météores": {"type": "Météores", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Perseid_meteor_2007.jpg/150px-Perseid_meteor_2007.jpg", "hint": "Clair"},
        "Éclipse Solaire": {"type": "Solaire", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Solar_eclipse_1999_4_NR.jpg/150px-Solar_eclipse_1999_4_NR.jpg", "hint": "Solaire"}
    }
}

# --- LOGIQUE MÉTÉO ---
def get_weather_forecast():
    api_key = "16f68f1e07fea20e39f52de079037925"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat=46.65&lon=6.91&appid={api_key}&units=metric&lang=fr"
    try:
        data = requests.get(url).json()
        return data['list'][:8]
    except: return None

# --- SIDEBAR SETUP ---
st.sidebar.title("🛠️ Mon Setup Astro")

with st.sidebar.expander("🎥 Matériel", expanded=True):
    cam_model = st.selectbox("Caméra", ["ZWO ASI294MC Pro", "ZWO ASI2600MC", "ZWO ASI533MC", "DSLR", "Autre"])
    w_cam = st.number_input("Conso Caméra (W)", 1, 30, 15)
    focale = st.number_input("Focale Tube (mm)", 50, 3000, 400)
    pixel = st.number_input("Taille Pixel (µm)", 1.0, 10.0, 4.63)

with st.sidebar.expander("🔋 Énergie (EB3A)", expanded=True):
    w_mnt = st.number_input("Monture (W)", 1, 25, 8)
    w_acc = st.number_input("ASIAIR/EAF (W)", 1, 20, 8)
    w_heat = st.number_input("Chauffage (W)", 0, 40, 12)
    
    total_w = w_cam + w_mnt + w_acc + w_heat
    autonomie_h = (268 * 0.85) / total_w
    heure_fin = datetime.now() + timedelta(hours=autonomie_h)

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites Master Dashboard")

# 1. MÉTÉO ET FENÊTRE DE TIR
st.subheader("☁️ Prévisions Horaires & Opportunités (Romont)")
forecast = get_weather_forecast()
if forecast:
    cols = st.columns(8)
    for i, s in enumerate(forecast):
        h_txt = datetime.fromtimestamp(s['dt']).strftime('%H:%M')
        n = s['clouds']['all']
        ico = "🟢" if n < 20 else "🟡" if n < 60 else "🔴"
        cols[i].metric(f"{ico} {h_txt}", f"{n}%")
    
    # Alerte si le ciel se dégage
    trouees = [datetime.fromtimestamp(s['dt']).strftime('%H:%M') for s in forecast if s['clouds']['all'] < 25]
    if trouees:
        st.success(f"✨ **Alerte Ciel Clair :** Excellentes conditions prévues à {', '.join(trouees)} !")

st.divider()

# 2. SÉLECTION CIBLE AVEC VIGNETTE
c1, c2 = st.columns([1, 2])
with c1:
    cat_name = st.selectbox("📂 Catalogue", list(CATALOGUES.keys()))
    target_name = st.selectbox("🎯 Cible", list(CATALOGUES[cat_name].keys()))
    filtre = st.selectbox("💎 Filtre installé", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])
    
    # Vignette
    st.image(CATALOGUES[cat_name][target_name]["img"], width=180, caption=target_name)

with c2:
    st.subheader("📋 Analyse & Alertes")
    target_data = CATALOGUES[cat_name][target_name]
    
    # SYSTÈME D'ALERTES CROISÉES
    if "SV220" in filtre:
        if "Galaxie" in target_data['type']:
            st.warning("💡 **ALERTE EXPERT :** Le SV220 sur une galaxie (M31/M51) sert à faire ressortir les nébuleuses H-alpha. C'est parfait, mais prévois des poses sans filtre pour les étoiles !")
        elif "Comète" in target_data['type'] or "Amas" in target_data['type']:
            st.error(f"❌ **ALERTE ERREUR :** Le SV220 bloque le signal de {target_name}. Utilise 'Sans Filtre' ou 'L-Pro'.")
    
    elif "Sans Filtre" in filtre:
        if "Solaire" in target_data['type']:
            st.error("🔥 **DANGER CRITIQUE :** Filtre solaire frontal indispensable ! Ne pointe pas le soleil sans protection.")
        else:
            st.success(f"✅ **Signal Pur :** Parfait pour capturer tout le spectre de {target_name}.")
            
    # INFOS TECHNIQUES
    echantillon = (pixel / focale) * 206.265
    st.info(f"📐 Échantillonnage : **{echantillon:.2f}\"/pixel**")
    st.write(f"⏱️ Autonomie : **{int(autonomie_h)}h {int((autonomie_h%1)*60)}min**")
    st.info(f"🔋 **Batterie vide à : {heure_fin.strftime('%H:%M')}**")

# 3. GRAPHIQUE DE SESSION
tx = np.linspace(0, autonomie_h, 100); ty = np.linspace(100, 15, 100)
fig, ax = plt.subplots(figsize=(10, 2))
ax.plot(tx, ty, color='#00ffd0', lw=2)
ax.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
ax.tick_params(colors='white'); ax.set_ylabel("%", color="white")
st.pyplot(fig)

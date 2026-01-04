import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Ultimate", layout="wide")

# --- BASE DE DONNÉES IMAGES & INFOS ---
# Simulé avec des placeholders pour l'exemple, à remplacer par tes URLs
DB_CIBLES = {
    "M31 Andromède": {"type": "Galaxie", "img": "https://img.astrometry.net/31/m31.jpg", "desc": "Spectre continu + Régions HII."},
    "M42 Orion": {"type": "Nébuleuse", "img": "https://img.astrometry.net/42/m42.jpg", "desc": "Émission intense Ha/OIII."},
    "NGC 7000": {"type": "Nébuleuse", "img": "https://img.astrometry.net/7000/ngc7000.jpg", "desc": "Émission Hydrogène pur."},
    "C/2023 A3": {"type": "Comète", "img": "https://img.astrometry.net/comet.jpg", "desc": "Spectre continu (Poussière)."},
    "Éclipse Solaire": {"type": "Solaire", "img": "https://img.astrometry.net/sun.jpg", "desc": "FILTRE SOLAIRE OBLIGATOIRE."},
    "Pluie de Météores": {"type": "Météores", "img": "https://img.astrometry.net/meteors.jpg", "desc": "Grand angle sans filtre."}
}

# --- FONCTION PRÉVISIONS HORAIRES ---
def get_weather():
    api_key = "16f68f1e07fea20e39f52de079037925"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat=46.65&lon=6.91&appid={api_key}&units=metric"
    try:
        return requests.get(url).json()['list'][:8]
    except: return None

# --- SIDEBAR : LE MATÉRIEL ---
st.sidebar.title("🛠️ Mon Setup Pro")
with st.sidebar.expander("🎥 Caméra & Optique", expanded=True):
    cam = st.selectbox("Caméra", ["ZWO ASI294MC Pro", "ZWO ASI2600MC", "ZWO ASI533MC", "DSLR", "Autre"])
    w_cam = st.number_input("Conso (W)", 1, 30, 15)
    focale = st.number_input("Focale (mm)", 50, 3000, 400)

with st.sidebar.expander("🔋 Énergie (EB3A)", expanded=True):
    bat_wh = 268
    total_w = w_cam + st.number_input("Monture (W)", 1, 20, 8) + st.number_input("Accessoires (W)", 1, 20, 10)
    autonomie = (bat_wh * 0.85) / total_w
    h_fin = datetime.now() + timedelta(hours=autonomie)

# --- DASHBOARD ---
st.title("🛰️ AstroPépites Dashboard")

# Météo Horaires
forecast = get_weather()
if forecast:
    st.subheader("☁️ Fenêtre de tir (Romont)")
    cols = st.columns(8)
    for i, s in enumerate(forecast):
        h = datetime.fromtimestamp(s['dt']).strftime('%H:%M')
        n = s['clouds']['all']
        ico = "🟢" if n < 20 else "🟡" if n < 60 else "🔴"
        cols[i].metric(f"{ico} {h}", f"{n}%")

st.divider()

# Sélection Cible avec Vignette
c1, c2 = st.columns([1, 2])
with c1:
    target_name = st.selectbox("🎯 Cible (Messier / NGC / Spécial)", list(DB_CIBLES.keys()))
    filtre = st.selectbox("💎 Filtre", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])
    
    # Affichage de la vignette (petite taille)
    st.image("https://via.placeholder.com/150", caption=target_name, width=150)

with c2:
    st.subheader("📋 Analyse du Shooting")
    t_info = DB_CIBLES[target_name]
    
    # Logique d'alerte filtrage
    if "SV220" in filtre:
        if "Galaxie" in t_info['type']:
            st.warning(f"💡 **Note :** Le SV220 sur {target_name} isole le H-alpha. Mixez avec du 'Sans Filtre'.")
        elif "Comète" in t_info['type']:
            st.error("❌ **Incompatible :** Le Dual-Band tue le signal des comètes.")
    elif "Sans Filtre" in filtre and "Solaire" in t_info['type']:
        st.error("🔥 **DANGER :** Filtre solaire frontal requis !")
    else:
        st.success(f"✅ Setup validé pour {target_name}.")

    st.write(f"⏱️ **Autonomie estimée :** {int(autonomie)}h {int((autonomie%1)*60)}min")
    st.info(f"🔋 **Batterie vide à : {h_fin.strftime('%H:%M')}**")

# Graphique de batterie
tx = np.linspace(0, autonomie, 100); ty = np.linspace(100, 0, 100)
fig, ax = plt.subplots(figsize=(10, 2))
ax.plot(tx, ty, color='#00ffd0', lw=2)
ax.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
ax.tick_params(colors='white')
st.pyplot(fig)

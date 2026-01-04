import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION VITRINE ---
st.set_page_config(page_title="AstroPépites Pro 2026", layout="wide")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e445b; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS CLÉS ---
def get_weather_forecast():
    # Utilisation de ta clé API pour Romont
    api_key = "16f68f1e07fea20e39f52de079037925"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat=46.65&lon=6.91&appid={api_key}&units=metric&lang=fr"
    try:
        data = requests.get(url).json()
        return data['list'][:8] # On prend les prochaines 24h (pas de 3h)
    except:
        return None

# --- SIDEBAR : LE MATÉRIEL ---
st.sidebar.title("🔭 Ma Configuration")

with st.sidebar.expander("🎥 Capteur & Optique", expanded=True):
    cam_name = st.text_input("Caméra", "ZWO ASI294MC Pro")
    w_cam = st.number_input("Conso Caméra (W)", 1, 30, 15)
    px_size = st.number_input("Taille Pixel (µm)", 1.0, 10.0, 4.63)
    focale = st.number_input("Focale tube (mm)", 50, 3000, 400)

with st.sidebar.expander("🔋 Énergie (Bluetti EB3A)", expanded=True):
    bat_wh = 268 
    w_mnt = st.number_input("Monture (W)", 1, 25, 8)
    w_asiair = st.number_input("ASIAIR/Guidage (W)", 1, 25, 8)
    w_heat = st.number_input("Chauffage (W)", 0, 40, 12)
    
    total_w = w_cam + w_mnt + w_asiair + w_heat
    autonomie_h = (bat_wh * 0.85) / total_w
    heure_fin = datetime.now() + timedelta(hours=autonomie_h)

# --- DASHBOARD PRINCIPAL ---
st.title("🌌 AstroPépites Dashboard Pro")

# --- SECTION MÉTÉO & FENÊTRE DE TIR ---
st.subheader("☁️ Prévisions & Fenêtre de Tir (Romont)")
forecast = get_weather_forecast()

if forecast:
    cols = st.columns(len(forecast))
    for i, slot in enumerate(forecast):
        heure = datetime.fromtimestamp(slot['dt']).strftime('%H:%M')
        nuages = slot['clouds']['all']
        # Couleur selon couverture
        color = "🟢" if nuages < 20 else "🟡" if nuages < 60 else "🔴"
        cols[i].metric(f"{color} {heure}", f"{nuages}%", f"{slot['main']['temp']}°C", delta_color="inverse")
    
    # Analyse de la meilleure heure
    clear_slots = [datetime.fromtimestamp(s['dt']).strftime('%H:%M') for s in forecast if s['clouds']['all'] < 30]
    if clear_slots:
        st.success(f"✨ **Ciel dégagé prévu à : {', '.join(clear_slots)}**. C'est le moment de chauffer le capteur !")
    else:
        st.warning("☁️ Pas de trouée majeure prévue dans les prochaines heures.")

st.divider()

# --- CIBLE & ANALYSE SCIENTIFIQUE ---
c1, c2 = st.columns(2)
target = c1.text_input("🎯 Cible (Messier, NGC, Comète, Éclipse...)", "M31 Andromède")
filtre = c2.selectbox("💎 Filtre", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])

st.subheader("📋 Analyse du Shooting")
info_col, graph_col = st.columns([1, 1])

with info_col:
    # Échantillonnage
    echantillon = (px_size / focale) * 206.265
    st.info(f"📐 Échantillonnage : **{echantillon:.2f}\"/pixel**")
    
    # Logique Filtre Expert
    t = target.lower()
    if "sv220" in filtre.lower():
        if "m31" in t or "andromède" in t or "m51" in t:
            st.warning("💡 **Expert :** Le SV220 isolera les régions HII (nuages rouges) de la galaxie. Prévoyez des poses sans filtre pour la structure stellaire.")
        elif "comète" in t or "c/202" in t:
            st.error("❌ **Incompatible :** Le Dual-Band bloque le spectre continu des comètes. Passez en 'Sans Filtre'.")
    elif "sans filtre" in filtre.lower() and "éclipse" in t:
        st.error("🚫 **DANGER :** Filtre solaire obligatoire pour une éclipse solaire !")
    else:
        st.success(f"✅ Setup {filtre} cohérent pour {target}.")

with graph_col:
    st.write(f"🔋 **Batterie :** Fin à **{heure_fin.strftime('%H:%M')}**")
    tx = np.linspace(0, autonomie_h, 100); ty = np.linspace(100, 15, 100)
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(tx, ty, color='#00ffd0', lw=2)
    ax.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white'); ax.grid(color='#2e334d', linestyle='--')
    st.pyplot(fig)

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# --- CONFIGURATION & SÉCURITÉ ---
st.set_page_config(page_title="AstroPépites Romont Expert", layout="wide")

# Récupération de ta clé depuis tes secrets configurés
WEATHER_API_KEY = st.secrets["openweather_key"]

# --- FONCTION MÉTÉO SÉCURISÉE ---
def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=fr"
    try:
        r = requests.get(url).json()
        return {
            "temp": r['main']['temp'],
            "clouds": r['clouds']['all'],
            "humidity": r['main']['humidity'],
            "desc": r['weather'][0]['description'].capitalize()
        }
    except Exception as e:
        return None

# --- DONNÉES MATÉRIEL & CATALOGUES ---
ORDIS = {"ASI AIR Plus": 10, "ASI AIR Mini": 7, "Mini PC (NINA)": 15, "Laptop": 35}
CAMS = {"ZWO ASI183MC Pro": 18, "ZWO ASI2600MC Pro": 20, "ZWO ASI533MC Pro": 15}
BATTERIES = {"Bluetti EB3A (268Wh)": 268, "Ecoflow River 2 (256Wh)": 256, "Batterie 100Ah": 1280}

CATALOGUES = {
    "Messier": ["M1", "M31", "M33", "M42", "M45", "M51", "M81", "M101"],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 6946", "NGC 891"],
    "Sharpless": ["Sh2-129", "Sh2-101", "Sh2-155", "Sh2-190"],
    "Arp / Abell": ["Arp 244", "Arp 273", "Abell 21"]
}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🛰️ Pilotage Romont")
    
    # MÉTÉO LIVE (Utilise ta clé secrète)
    st.subheader("☁️ Ciel en Direct")
    w = get_weather(46.69, 6.91)
    if w:
        c1, c2 = st.columns(2)
        c1.metric("Temp", f"{w['temp']}°C")
        c2.metric("Nuages", f"{w['clouds']}%")
        
        # Alerte Humidité / Rosée
        if w['humidity'] > 80:
            st.error(f"💧 Humidité : {w['humidity']}% ! Active le chauffage.")
        else:
            st.success(f"✅ Humidité : {w['humidity']}%")
        st.caption(f"État : {w['desc']}")
    
    st.divider()

    with st.expander("🔋 Setup & Énergie", expanded=True):
        bat = st.selectbox("Batterie", list(BATTERIES.keys()))
        ordi = st.selectbox("Ordinateur", list(ORDIS.keys()))
        cam_p = st.selectbox("Caméra Principale", list(CAMS.keys()))
        cam_g = st.selectbox("Caméra Guidage", ["ASI 120MM Mini", "ASI 290MM Mini"])
        efw = st.toggle("Roue à Filtres (EFW)", value=True)
        eaf = st.toggle("Auto Focuser (EAF)", value=True)
        bandes = st.number_input("Bandes chauffantes", 0, 4, 1)
        
        # Calcul Consommation précis
        total_w = ORDIS[ordi] + CAMS[cam_p] + 3 + (bandes * 7) + (2 if eaf else 0) + (1 if efw else 0) + 5
        autonomie = BATTERIES[bat] / total_w

    with st.expander("🧭 Boussole d'Horizon", expanded=True):
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        obs = [st.slider(f"{d}", 0, 90, 15) for d in dirs]
        
        # Graphique VERT (Ciel) et ROUGE (Obstacles)
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
        angles = np.linspace(0, 2*np.pi, 9)
        ax.fill(angles, [90]*9, color='#2ecc71', alpha=0.3)
        ax.fill(angles, obs + [obs[0]], color='#e74c3c', alpha=0.8)
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_facecolor('#0e1117'); fig.patch.set_facecolor('#0e1117')
        ax.tick_params(colors='white', labelsize=7)
        st.pyplot(fig)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

col_main, col_preview = st.columns([2, 1])

with col_main:
    # Horloge nocturne étendue
    h_sim = st.select_slider("🕒 Heure de simulation", 
                             options=[f"{h}h" for h in [18,19,20,21,22,23,0,1,2,3,4,5,6]], value="23h")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    cat_sel = c1.selectbox("📁 Catalogue", list(CATALOGUES.keys()))
    obj_sel = c2.selectbox(f"🎯 Objet dans {cat_sel}", CATALOGUES[cat_sel])
    
    st.markdown(f"""
        <div style="background: #1e2130; padding: 25px; border-radius: 15px; border: 2px solid #00ffd0; text-align: center;">
            <h1 style="color: white; margin: 0;">🔋 Autonomie : {autonomie:.1f} Heures</h1>
            <p style="color: #00ffd0; margin: 0;">Consommation : {total_w} Watts | GPS : 46.69, 6.91</p>
        </div>
    """, unsafe_allow_html=True)

with col_preview:
    # VIGNETTE SÉCURISÉE (Serveur Aladin Strasbourg)
    st.write("**Aperçu Réel (Aladin/DSS)**")
    obj_clean = obj_sel.replace(' ', '').replace('-', '')
    img_url = f"https://aladin.u-strasbg.fr/java/nph-aladin.pl?Object={obj_clean}&Size=15&Output=JPEG"
    
    st.markdown(f"""
        <div style="border: 2px solid #444; border-radius: 10px; overflow: hidden; background: black;">
            <img src="{img_url}" style="width: 100%; display: block;" 
                 onerror="this.src='https://via.placeholder.com/300x300/1e2130/ffffff?text={obj_sel}';">
        </div>
    """, unsafe_allow_html=True)

st.divider()
st.subheader("📋 Récapitulatif du matériel")
cola, colb, colc = st.columns(3)
with cola:
    st.write(f"🖥️ **Ordinateur :** {ordi}")
    st.write(f"📸 **Caméra :** {cam_p}")
with colb:
    st.write(f"⚙️ **Accessoires :** {'EAF' if eaf else ''} {'+ EFW' if efw else ''}")
    st.write(f"📡 **Guidage :** {cam_g}")
with colc:
    st.write(f"🌡️ **Chauffage :** {bandes} bande(s)")
    st.write(f"🔋 **Source :** {bat}")

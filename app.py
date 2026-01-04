import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Romont", layout="wide")

# --- RÉCUPÉRATION SÉCURISÉE DE TA CLÉ ---
# Assure-toi que dans tes secrets Streamlit, le nom est exactement : openweather_key
try:
    API_KEY = st.secrets["openweather_key"]
except:
    API_KEY = None

# --- DONNÉES CATALOGUES ---
CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 891", "NGC 4565", "NGC 6946"],
    "Sharpless": [f"Sh2-{i}" for i in [129, 101, 155, 190, 240, 276]],
    "Arp / Abell": ["Arp 244", "Arp 273", "Abell 21", "Abell 33", "Abell 39"]
}

# --- BARRE LATÉRALE (Matériel & Boussole inchangés) ---
with st.sidebar:
    st.title("🛰️ Configuration")
    
    # 1. BLOC MÉTÉO (CORRIGÉ)
    st.subheader("☁️ Météo Live")
    if API_KEY:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat=46.69&lon=6.91&appid={API_KEY}&units=metric&lang=fr"
        try:
            res = requests.get(url).json()
            col_w1, col_w2 = st.columns(2)
            col_w1.metric("Temp", f"{res['main']['temp']}°C")
            col_w2.metric("Nuages", f"{res['clouds']['all']}%")
            st.write(f"**État :** {res['weather'][0]['description']}")
            if res['main']['humidity'] > 80:
                st.warning(f"💧 Humidité élevée : {res['main']['humidity']}%")
        except:
            st.error("⚠️ Erreur de connexion API. Vérifie ta clé.")
    else:
        st.info("ℹ️ Clé API non détectée dans les Secrets.")

    st.divider()

    # 2. TON MATÉRIEL (Ok)
    with st.expander("🎒 Setup Complet", expanded=False):
        bat = st.selectbox("Batterie", ["Bluetti EB3A (268Wh)", "Ecoflow River 2 (256Wh)", "100Ah (1280Wh)"])
        ordi = st.selectbox("Ordinateur", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC (NINA)", "Laptop"])
        cam_p = st.selectbox("Caméra Principale", ["ASI 183MC Pro", "ASI 2600MC Pro", "ASI 533MC Pro"])
        cam_g = st.selectbox("Caméra Guidage", ["ASI 120MM Mini", "ASI 290MM Mini"])
        efw = st.toggle("Roue à Filtres (EFW)", value=True)
        eaf = st.toggle("Auto Focuser (EAF)", value=True)
        bandes = st.number_input("Bandes chauffantes", 0, 4, 1)

    # 3. TA BOUSSOLE (Ok)
    with st.expander("🧭 Horizon (Réglages)", expanded=True):
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        obs = [st.slider(d, 0, 90, 15, key=f"b_{d}") for d in dirs]
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(2.5, 2.5))
        angles = np.linspace(0, 2*np.pi, 9)
        ax.fill(angles, [90]*9, color='#2ecc71', alpha=0.3)
        ax.fill(angles, obs + [obs[0]], color='#e74c3c', alpha=0.8)
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        ax.set_facecolor('#0e1117'); fig.patch.set_facecolor('#0e1117'); ax.axis('off')
        st.pyplot(fig)

# --- CALCUL AUTONOMIE ---
wh = 268 if "EB3A" in bat else (256 if "River" in bat else 1280)
conso = (15 if "Plus" in ordi else 10) + 18 + (bandes * 7) + 8
autonomie = wh / conso

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification Romont")

c_sel, c_img = st.columns([2, 1])

with c_sel:
    # 4. CATALOGUES (RETOUR)
    c1, c2 = st.columns(2)
    cat_sel = c1.selectbox("📁 Choisir Catalogue", list(CATALOGUES.keys()))
    obj_sel = c2.selectbox(f"🎯 Objet dans {cat_sel}", CATALOGUES[cat_sel])
    
    h_sim = st.select_slider("🕒 Heure de simulation", options=[f"{h}h" for h in [18,19,20,21,22,23,0,1,2,3,4,5,6]], value="23h")

    st.markdown(f"""
        <div style="background: #1e2130; padding: 25px; border-radius: 15px; border: 2px solid #00ffd0; text-align: center;">
            <h1 style="color: white; margin: 0;">🔋 {autonomie:.1f} Heures d'autonomie</h1>
            <p style="color: #aaa; margin: 0;">Position : 46.69 N, 6.91 E</p>
        </div>
    """, unsafe_allow_html=True)

with c_img:
    st.write("**Aperçu Cible (Stable)**")
    # NOUVELLE MÉTHODE IMAGE : Sky-Map est plus rapide pour les vignettes
    clean_name = obj_sel.replace(' ', '+')
    img_url = f"https://server1.sky-map.org/imgproxy?object={clean_name}&view=normal"
    
    st.image(img_url, use_container_width=True, caption=f"Cible : {obj_sel}")

st.divider()
st.subheader("📋 État du Setup")
st.write(f"✅ {ordi} + {cam_p} + {cam_g} | ⚙️ EAF: {'Oui' if eaf else 'Non'} | EFW: {'Oui' if efw else 'Non'} | 🔥 {bandes} bande(s)")

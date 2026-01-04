import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Romont", layout="wide")

# --- RÉCUPÉRATION SÉCURISÉE CLÉ MÉTÉO ---
# Assure-toi que dans tes Secrets Streamlit, le nom est : openweather_key
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

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🛰️ Configuration")
    
    # 1. MÉTÉO (CORRIGÉE)
    st.subheader("☁️ Météo Live Romont")
    if API_KEY:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat=46.69&lon=6.91&appid={API_KEY}&units=metric&lang=fr"
            data = requests.get(url).json()
            c1, c2 = st.columns(2)
            c1.metric("Temp", f"{data['main']['temp']}°C")
            c2.metric("Nuages", f"{data['clouds']['all']}%")
            st.info(f"État : {data['weather'][0]['description']}")
        except:
            st.error("Erreur API : Vérifie ta clé")
    else:
        st.warning("Clé 'openweather_key' non trouvée dans Secrets")

    st.divider()

    # 2. SETUP MATÉRIEL (Ok)
    with st.expander("🎒 Setup Complet", expanded=False):
        bat = st.selectbox("Batterie", ["Bluetti EB3A (268Wh)", "Ecoflow River 2 (256Wh)", "100Ah (1280Wh)"])
        ordi = st.selectbox("Ordinateur", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC (NINA)", "Laptop"])
        cam_p = st.selectbox("Caméra Principale", ["ASI 183MC Pro", "ASI 2600MC Pro", "ASI 533MC Pro"])
        cam_g = st.selectbox("Caméra Guidage", ["ASI 120MM Mini", "ASI 290MM Mini"])
        efw = st.toggle("Roue à Filtres (EFW)", value=True)
        eaf = st.toggle("Auto Focuser (EAF)", value=True)
        bandes = st.number_input("Bandes chauffantes", 0, 4, 1)

    # 3. BOUSSOLE (Ok)
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

# --- CALCULS ---
wh = 268 if "EB3A" in bat else (256 if "River" in bat else 1280)
conso = (15 if "Plus" in ordi else 10) + 18 + (bandes * 7) + 8
autonomie = wh / conso

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

col_left, col_right = st.columns([2, 1])

with col_left:
    # 4. CATALOGUES
    c_cat, c_obj = st.columns(2)
    cat_sel = c_cat.selectbox("📁 Catalogue", list(CATALOGUES.keys()))
    obj_sel = c_obj.selectbox(f"🎯 Objet dans {cat_sel}", CATALOGUES[cat_sel])
    
    h_sim = st.select_slider("🕒 Heure de simulation", options=[f"{h}h" for h in [18,19,20,21,22,23,0,1,2,3,4,5,6]], value="23h")

    st.markdown(f"""
        <div style="background: #1e2130; padding: 30px; border-radius: 15px; border: 2px solid #00ffd0; text-align: center;">
            <h1 style="color: white; margin: 0;">🔋 Autonomie : {autonomie:.1f} Heures</h1>
            <p style="color: #00ffd0; margin: 0;">Position Romont : 46.69 N, 6.91 E | Conso : {conso} Watts</p>
        </div>
    """, unsafe_allow_html=True)

with col_right:
    st.write("**Vignette de confirmation (NASA SkyView)**")
    # Image stable via NASA SkyView
    clean_name = obj_sel.replace(' ', '')
    img_url = f"https://skyview.gsfc.nasa.gov/cgi-bin/images?survey=dss&object={clean_name}&size=0.25&pixels=300"
    
    st.markdown(f"""
        <div style="border: 2px solid #444; border-radius: 10px; overflow: hidden; background: black; text-align: center;">
            <img src="{img_url}" style="width: 100%; display: block;" 
                 onerror="this.src='https://via.placeholder.com/300/1e2130/ffffff?text={obj_sel}';">
        </div>
    """, unsafe_allow_html=True)

st.divider()
st.subheader("📋 État du Setup")
st.write(f"✅ {ordi} + {cam_p} + {cam_g} | ⚙️ EAF: {'Oui' if eaf else 'Non'} | EFW: {'Oui' if efw else 'Non'} | 🔥 {bandes} bande(s)")

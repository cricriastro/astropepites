import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Romont", layout="wide")

# Clé météo sécurisée
try:
    WEATHER_API_KEY = st.secrets["openweather_key"]
except:
    WEATHER_API_KEY = None

# --- DONNÉES ---
CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": ["NGC 7000", "NGC 6960", "NGC 2237", "NGC 891", "NGC 4565"],
    "Sharpless": [f"Sh2-{i}" for i in [129, 101, 155, 190, 240]],
    "Arp / Abell": ["Arp 244", "Arp 273", "Abell 21", "Abell 33"]
}

# --- SIDEBAR : LE SETUP COMPLET ---
with st.sidebar:
    st.title("🛰️ Configuration")
    
    # 1. MÉTÉO EN DIRECT
    if WEATHER_API_KEY:
        try:
            r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat=46.69&lon=6.91&appid={WEATHER_API_KEY}&units=metric&lang=fr").json()
            st.metric("Météo Romont", f"{r['main']['temp']}°C", f"{r['clouds']['all']}% nuages")
            if r['main']['humidity'] > 80: st.error(f"💧 Rosée : {r['main']['humidity']}%")
        except: st.warning("Météo indisponible")

    # 2. INVENTAIRE MATÉRIEL (Tout y est !)
    with st.expander("🎒 Matériel Complet", expanded=True):
        bat = st.selectbox("Batterie", ["Bluetti EB3A (268Wh)", "Ecoflow River 2 (256Wh)", "100Ah (1280Wh)"])
        ordi = st.selectbox("Ordinateur", ["ASI AIR Plus", "ASI AIR Mini", "Mini PC (NINA)", "Laptop"])
        cam_p = st.selectbox("Caméra Principale", ["ASI 183MC Pro", "ASI 2600MC Pro", "ASI 533MC Pro"])
        cam_g = st.selectbox("Caméra Guidage", ["ASI 120MM Mini", "ASI 290MM Mini", "ASI 174MM Mini"])
        st.divider()
        efw = st.toggle("Roue à Filtres (EFW)", value=True)
        eaf = st.toggle("Auto Focuser (EAF)", value=True)
        bandes = st.number_input("Bandes chauffantes", 0, 4, 1)
        monture = st.selectbox("Monture", ["AM5", "AM3", "GTi", "EQ6-R"])

    # 3. BOUSSOLE (VERTE/ROUGE)
    with st.expander("🧭 Horizon (Réglages)", expanded=True):
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        obs = [st.slider(d, 0, 90, 15, key=f"b_{d}") for d in dirs]
        
        # Dessin rapide
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(2.5, 2.5))
        angles = np.linspace(0, 2*np.pi, 9)
        ax.fill(angles, [90]*9, color='#2ecc71', alpha=0.3) # Vert
        ax.fill(angles, obs + [obs[0]], color='#e74c3c', alpha=0.8) # Rouge
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_facecolor('#0e1117'); fig.patch.set_facecolor('#0e1117')
        ax.axis('off')
        st.pyplot(fig)

# --- CALCULS ---
wh = 268 if "EB3A" in bat else (256 if "River" in bat else 1280)
conso = (15 if "Plus" in ordi else 10) + 18 + (bandes * 7) + 8 # Estimation moyenne
autonomie = wh / conso

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session")

col_sel, col_img = st.columns([2, 1])

with col_sel:
    # 4. CHOIX CATALOGUE ET CIBLE
    c_cat, c_obj = st.columns(2)
    cat_sel = c_cat.selectbox("📁 Choisir Catalogue", list(CATALOGUES.keys()))
    obj_sel = c_obj.selectbox(f"🎯 Objet {cat_sel}", CATALOGUES[cat_sel])
    
    # Horloge simulation nuit
    h_sim = st.select_slider("🕒 Heure de simulation", options=[f"{h}h" for h in [18,19,20,21,22,23,0,1,2,3,4,5,6]], value="23h")

    st.markdown(f"""
        <div style="background: #1e2130; padding: 20px; border-radius: 15px; border: 2px solid #00ffd0; text-align: center;">
            <h2 style="color: white; margin: 0;">🔋 Autonomie : {autonomie:.1f} Heures</h2>
            <p style="color: #aaa; margin: 0;">GPS Romont : 46.69, 6.91 | Coût charge : ~0.08 CHF</p>
        </div>
    """, unsafe_allow_html=True)

with col_img:
    st.write("**Aperçu Cible**")
    # Chargement d'image optimisé via Aladin
    img_id = obj_sel.replace(' ', '').replace('-', '')
    url = f"https://aladin.u-strasbg.fr/java/nph-aladin.pl?Object={img_id}&Size=15&Output=JPEG"
    
    st.markdown(f"""
        <div style="border: 2px solid #444; border-radius: 10px; overflow: hidden; background: black; height: 250px;">
            <img src="{url}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='https://via.placeholder.com/300?text={obj_sel}';">
        </div>
    """, unsafe_allow_html=True)

st.divider()
st.subheader("📋 État du Setup")
st.write(f"✅ {ordi} + {cam_p} + {cam_g} | ⚙️ EAF: {'Oui' if eaf else 'Non'} | EFW: {'Oui' if efw else 'Non'} | 🔥 {bandes} bande(s)")

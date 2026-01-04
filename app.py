import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Mode Camp", layout="wide")
WEATHER_API_KEY = st.secrets["openweather_key"]

# --- INITIALISATION DE LA MÉMOIRE (Pour garder les réglages boussole) ---
if 'horizon_data' not in st.session_state:
    st.session_state.horizon_data = [15] * 8  # Valeur par défaut 15° pour les 8 directions

# --- FONCTION MÉTÉO ---
def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=fr"
    try:
        r = requests.get(url).json()
        return {"temp": r['main']['temp'], "clouds": r['clouds']['all'], "hum": r['main']['humidity']}
    except: return None

# --- DATA MATÉRIEL ---
ORDIS = {"ASI AIR Plus": 10, "ASI AIR Mini": 7, "Mini PC (NINA)": 15, "Laptop": 35}
CAMS = {"ZWO ASI183MC Pro": 18, "ZWO ASI2600MC Pro": 20, "ZWO ASI533MC Pro": 15}
BATTERIES = {"Bluetti EB3A (268Wh)": 268, "Ecoflow River 2 (256Wh)": 256, "Batterie 100Ah": 1280}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🛰️ Poste de Pilotage")
    
    # MÉTÉO LIVE
    w = get_weather(46.69, 6.91)
    if w:
        st.metric("Temp / Nuages", f"{w['temp']}°C / {w['clouds']}%")
        if w['hum'] > 80: st.error(f"💧 Rosée élevée ({w['hum']}%)")

    # BOUSSOLE (Enregistrement persistant)
    with st.expander("🧭 Horizon & Obstacles", expanded=True):
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        new_obs = []
        for i, d in enumerate(dirs):
            val = st.slider(f"{d}", 0, 90, st.session_state.horizon_data[i])
            new_obs.append(val)
        st.session_state.horizon_data = new_obs # On sauvegarde

        # Dessin Vert/Rouge
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
        angles = np.linspace(0, 2*np.pi, 9)
        ax.fill(angles, [90]*9, color='#2ecc71', alpha=0.3)
        ax.fill(angles, st.session_state.horizon_data + [st.session_state.horizon_data[0]], color='#e74c3c', alpha=0.8)
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.set_ylim(0, 90)
        ax.set_facecolor('#0e1117'); fig.patch.set_facecolor('#0e1117')
        ax.tick_params(colors='white', labelsize=7)
        st.pyplot(fig)

    # COÛT ÉLECTRIQUE
    with st.expander("💰 Coût de la recharge", expanded=False):
        prix_kwh = st.number_input("Prix kWh (CHF/€)", value=0.25)
        capa_wh = BATTERIES[st.session_state.get('bat_choice', "Bluetti EB3A (268Wh)")]
        cout = (capa_wh / 1000) * prix_kwh
        st.write(f"Coût plein : **{cout:.2f} CHF**")

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Session Multi-Nuits")

c1, c2 = st.columns([2, 1])

with c1:
    h_sim = st.select_slider("🕒 Heure de simulation", options=[f"{h}h" for h in [18,19,20,21,22,23,0,1,2,3,4,5,6]], value="23h")
    
    bat_choice = st.selectbox("Batterie utilisée", list(BATTERIES.keys()), key='bat_choice')
    ordi = st.selectbox("Ordinateur", list(ORDIS.keys()))
    cam = st.selectbox("Caméra", list(CAMS.keys()))
    bandes = st.number_input("Bandes chauffantes", 0, 4, 1)
    
    # Calcul autonomie
    conso = ORDIS[ordi] + CAMS[cam] + (bandes * 7) + 10 # 10W pour guidage/monture/accessoires
    autonomie = BATTERIES[bat_choice] / conso
    
    st.markdown(f"""
        <div style="background: #1e2130; padding: 25px; border-radius: 15px; border: 2px solid #00ffd0; text-align: center;">
            <h1 style="color: white; margin: 0;">🔋 Autonomie : {autonomie:.1f} Heures</h1>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.write("**Aperçu Cible**")
    # Pour l'exemple, on fixe une cible pour tester l'image
    obj_name = st.text_input("Rechercher un objet (ex: M31, NGC7000)", "M31")
    img_id = obj_name.replace(' ', '')
    img_url = f"https://aladin.u-strasbg.fr/java/nph-aladin.pl?Object={img_id}&Size=15&Output=JPEG"
    
    st.markdown(f"""
        <div style="border: 2px solid #444; border-radius: 10px; overflow: hidden; background: black;">
            <img src="{img_url}" style="width: 100%;" onerror="this.src='https://via.placeholder.com/300?text={obj_name}';">
        </div>
    """, unsafe_allow_html=True)

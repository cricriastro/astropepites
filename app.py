import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime
from tzlocal import get_localzone
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy import units as u
from astropy.time import Time

# ==========================================
# 1. CONFIGURATION & BASES DE DONNÉES
# ==========================================
st.set_page_config(page_title="AstroPépites Pro", layout="wide", page_icon="🔭")

# Catalogues d'objets (Classiques + Rares/Exotiques)
OBJECTS_DATABASE = [
    # Messier & NGC (Classiques)
    {"name": "M31 - Galaxie d'Andromède", "ra": "00h42m44s", "dec": "+41d16m09s", "cat": "Messier", "size": 190, "desc": "La grande voisine, facile mais exigeante en dynamique."},
    {"name": "M42 - Nébuleuse d'Orion", "ra": "05h35m17s", "dec": "-05d23m28s", "cat": "Messier", "size": 65, "desc": "Cible iconique, attention à ne pas cramer le cœur."},
    {"name": "NGC 6960 - Grande Dentelle", "ra": "20h45m42s", "dec": "+30d42m30s", "cat": "NGC/IC", "size": 70, "desc": "Rémanent de supernova, superbe en HOO."},
    
    # OBJETS RARES (Pour se démarquer)
    {"name": "Arp 273 - La Rose de Galaxies", "ra": "02h21m28s", "dec": "+39d22m32s", "cat": "Rare (Arp)", "size": 1.5, "desc": "Galaxies en interaction. Très esthétique, demande de la focale."},
    {"name": "Arp 240 - Galaxies Spirales", "ra": "09h02m25s", "dec": "+30d44m41s", "cat": "Rare (Arp)", "size": 2.0, "desc": "Pont de matière entre deux spirales. Très peu imagé."},
    {"name": "Sh2-132 - Lion Nebula", "ra": "22h18m42s", "dec": "+56d07m24s", "cat": "Rare (Sharpless)", "size": 90, "desc": "Nébuleuse en émission faible. Magnifique en SHO."},
    {"name": "Abell 39 - La Bulle Bleue", "ra": "16h27m33s", "dec": "+27d54m33s", "cat": "Rare (Abell)", "size": 2.5, "desc": "Nébuleuse planétaire parfaitement sphérique. Très difficile."},
    {"name": "Jones-Emberson 1 (PK 164+31.1)", "ra": "07h57m51s", "dec": "+53d25m17s", "cat": "Rare (Abell)", "size": 6.0, "desc": "Une 'oreille' de gaz très faible, défi pour ciel pur."},
]

TELESCOPES_DB = {
    "SW Evolux 62 ED (f/5.5)": {"focal": 340, "aperture": 62},
    "C8 avec Réducteur (f/6.3)": {"focal": 1280, "aperture": 203},
    "Newton 200/800 (f/4)": {"focal": 800, "aperture": 200}
}

CAMERAS_DB = {
    "ZWO ASI 183 MC Pro": {"w_mm": 13.2, "h_mm": 8.8, "pixel": 2.4},
    "ZWO ASI 2600 MM Pro": {"w_mm": 23.5, "h_mm": 15.7, "pixel": 3.76},
    "Canon EOS 6D (Full Frame)": {"w_mm": 36.0, "h_mm": 24.0, "pixel": 6.54}
}

# ==========================================
# 2. FONCTIONS UTILES
# ==========================================
def calculate_fov(focal, sensor_dim):
    return (sensor_dim / focal) * (180 / np.pi)

def get_nasa_image(target):
    url = "https://images-api.nasa.gov/search"
    params = {'q': target, 'media_type': 'image'}
    try:
        r = requests.get(url, params=params, timeout=5).json()
        if r['collection']['items']:
            return r['collection']['items'][0]['links'][0]['href']
    except: return None

def get_weather(lat, lon):
    api_key = st.secrets.get("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=fr"
    try:
        r = requests.get(url, timeout=5).json()
        return r if r.get("cod") == 200 else None
    except: return None

# ==========================================
# 3. SIDEBAR (Localisation & Horizon)
# ==========================================
st.sidebar.title("🛠 Configuration")
lat = st.sidebar.number_input("Latitude", value=48.85, format="%.2f")
lon = st.sidebar.number_input("Longitude", value=2.35, format="%.2f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()
local_tz = get_localzone()

st.sidebar.markdown("---")
st.sidebar.subheader("🌲 Masque d'Horizon")
m_vals = [st.sidebar.slider(d, 0, 60, 15) for d in ["Nord", "Est", "Sud", "Ouest"]]
# Interpolation simplifiée pour le graph
def get_limit(az):
    if az < 90: return m_vals[0] + (m_vals[1]-m_vals[0])*(az/90)
    if az < 180: return m_vals[1] + (m_vals[2]-m_vals[1])*((az-90)/90)
    if az < 270: return m_vals[2] + (m_vals[3]-m_vals[2])*((az-180)/90)
    return m_vals[3] + (m_vals[0]-m_vals[3])*((az-270)/90)

# ==========================================
# 4. INTERFACE PRINCIPALE
# ==========================================
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Cibles", "📸 Setup & FOV", "☁️ Météo & Seeing", "🗓 Événements"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        cat_choice = st.selectbox("Catalogue", ["Tous", "Messier", "NGC/IC", "Rare (Arp)", "Rare (Sharpless)", "Rare (Abell)"])
        filtered = [o for o in OBJECTS_DATABASE if cat_choice == "Tous" or o['cat'] == cat_choice]
        target_name = st.selectbox("Choisir l'objet", [o['name'] for o in filtered])
        obj = next(o for o in OBJECTS_DATABASE if o['name'] == target_name)
        
        coord = SkyCoord(obj["ra"], obj["dec"], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=location))
        
        st.metric("Altitude Actuelle", f"{altaz.alt.deg:.1f}°")
        limit = get_limit(altaz.az.deg)
        if altaz.alt.deg > limit:
            st.success("✅ Objet visible au-dessus de l'horizon")
        else:
            st.error("❌ Objet masqué par l'horizon")
        
        st.info(f"**Note :** {obj['desc']}")

    with col2:
        st.subheader("Trajectoire (Prochaines 12h)")
        times = now + np.linspace(0, 12, 50)*u.hour
        frame = AltAz(obstime=times, location=location)
        traj = coord.transform_to(frame)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(np.linspace(0, 12, 50), traj.alt.deg, color="#00ffcc", lw=2)
        ax.axhline(limit, color="red", linestyle="--", label="Votre Horizon")
        ax.set_facecolor("#121212")
        fig.patch.set_facecolor("#121212")
        ax.tick_params(colors='white')
        ax.set_xlabel("Heures à partir de maintenant", color="white")
        ax.set_ylabel("Altitude (°)", color="white")
        st.pyplot(fig)

with tab2:
    st.subheader("Simulateur de Champ (FOV)")
    c_scope, c_cam = st.columns(2)
    scope = c_scope.selectbox("Télescope", list(TELESCOPES_DB.keys()))
    camera = c_cam.selectbox("Caméra", list(CAMERAS_DB.keys()))
    
    focal = TELESCOPES_DB[scope]["focal"]
    sensor = CAMERAS_DB[camera]
    
    fov_w = calculate_fov(focal, sensor["w_mm"])
    fov_h = calculate_fov(focal, sensor["h_mm"])
    
    st.write(f"**Champ résultant :** {fov_w:.2f}° x {fov_h:.2f}°")
    
    obj_size_deg = obj["size"] / 60
    if obj_size_deg > fov_w * 0.8:
        st.warning(f"⚠️ L'objet ({obj_size_deg:.2f}°) est trop grand pour votre champ. Prévoyez une mosaïque !")
    else:
        st.success("✅ L'objet rentre parfaitement dans le capteur.")
    
    img_url = get_nasa_image(obj["name"].split('-')[-1].strip())
    if img_url:
        st.image(img_url, caption=f"Référence NASA pour {obj['name']}", width=500)

with tab3:
    st.subheader("Conditions Locales")
    weather = get_weather(lat, lon)
    if weather:
        m1, m2, m3 = st.columns(3)
        m1.metric("Température", f"{weather['main']['temp']}°C")
        m2.metric("Humidité", f"{weather['main']['humidity']}%")
        m3.metric("Vent", f"{weather['wind']['speed']} m/s")
        
        # Calcul point de rosée
        t, h = weather['main']['temp'], weather['main']['humidity']
        dew = t - ((100 - h) / 5)
        st.warning(f"💦 Risque de buée : Prévoyez vos résistances chauffantes si votre tube descend sous {dew:.1f}°C")
    else:
        st.error("Configurez votre clé OpenWeather dans les secrets pour voir la météo.")

with tab4:
    st.subheader("Événements Spéciaux")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### ☄️ Comètes")
        st.write("- **C/2023 A3 (Tsuchinshan-ATLAS)** : Visible au crépuscule (Mag ~5).")
        st.write("- **12P/Pons-Brooks** : Période orbitale terminée, rdv dans 71 ans.")
    with col_b:
        st.markdown("### 🌑 Éclipses")
        st.write("- **14 Mars 2025** : Éclipse Lunaire Totale.")
        st.write("- **12 Août 2026** : Éclipse Solaire Totale (Visible Nord Espagne/France).")

st.markdown("---")
st.caption("AstroPépites Pro - Pour des images que les autres n'ont pas.")

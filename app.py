import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun, get_body
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Master Pro", layout="wide")

# Clé API OpenWeather
OW_API_KEY = "16f68f1e07fea20e39f52de079037925"

# --- CATALOGUE EXPERT ---
# Note : shoot_min est en heures
CATALOG = [
    {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "mag": 4.0, "shoot_min": 3, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg/600px-Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg"},
    {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "mag": 3.4, "shoot_min": 5, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/M31_09-01-2011.jpg/600px-M31_09-01-2011.jpg"},
    {"name": "NGC 6960 (Dentelles)", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse", "mag": 7.0, "shoot_min": 8, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/The_Witch%27s_Broom_Nebula.jpg/600px-The_Witch%27s_Broom_Nebula.jpg"},
    {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "mag": 13.0, "shoot_min": 12, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/600px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg"},
    {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P.", "mag": 12.2, "shoot_min": 15, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/600px-Abell_31_nebula.jpg"},
    {"name": "C/2023 A3 (Comète)", "ra": "18h40m00s", "dec": "+05h00m00s", "type": "Comète", "mag": 5.0, "shoot_min": 1, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Comet_C2023_A3_2024-10-14.jpg/600px-Comet_C2023_A3_2024-10-14.jpg"}
]

# --- FONCTION MÉTÉO ---
def get_weather_report(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OW_API_KEY}&units=metric"
        r = requests.get(url).json()
        return {"clouds": r['clouds']['all'], "hum": r['main']['humidity'], "wind": r['wind']['speed']*3.6}
    except: return None

# --- SIDEBAR : CONFIGURATION MATÉRIEL ET LIEU ---
st.sidebar.title("🛠️ CONFIGURATION")

with st.sidebar.expander("📍 Lieu & Météo", expanded=True):
    lat = st.number_input("Lat", value=46.65) # Romont
    lon = st.number_input("Lon", value=6.91)
    loc = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
    w = get_weather_report(lat, lon)
    if w:
        st.write(f"☁️ Nuages : {w['clouds']}% | 💧 Hum : {w['hum']}%")
        if w['clouds'] > 40: st.error("⚠️ CIEL COUVERT")
        elif w['hum'] > 85: st.warning("⚠️ RISQUE DE BUÉE")
        else: st.success("🌌 CIEL DÉGAGÉ")

with st.sidebar.expander("🧭 Boussole d'Horizon", expanded=True):
    h = {
        "N": st.slider("Nord (0°)", 0, 80, 20), "NE": st.slider("NE (45°)", 0, 80, 15),
        "E": st.slider("Est (90°)", 0, 80, 25), "SE": st.slider("SE (135°)", 0, 80, 10),
        "S": st.slider("Sud (180°)", 0, 80, 5), "SO": st.slider("SO (225°)", 0, 80, 20),
        "O": st.slider("Ouest (270°)", 0, 80, 30), "NO": st.slider("NO (315°)", 0, 80, 15)
    }

with st.sidebar.expander("🔋 Énergie Bluetti", expanded=False):
    capa = st.number_input("Batterie (Wh)", value=268)
    conso = st.slider("Consommation (W)", 10, 80, 25)
    st.write(f"⏳ Autonomie : **{capa/conso:.1f}h**")

# --- CALCUL VISIBILITÉ ---
def get_obstacle_height(az):
    if az < 22.5 or az >= 337.5: return h["N"]
    if 22.5 <= az < 67.5: return h["NE"]
    if 67.5 <= az < 112.5: return h["E"]
    if 112.5 <= az < 157.5: return h["SE"]
    if 157.5 <= az < 202.5: return h["S"]
    if 202.5 <= az < 247.5: return h["SO"]
    if 247.5 <= az < 292.5: return h["O"]
    return h["NO"]

now = Time.now()
visibles = []
for obj in CATALOG:
    altaz = SkyCoord(obj["ra"], obj["dec"]).transform_to(AltAz(obstime=now, location=loc))
    if altaz.alt.deg > get_obstacle_height(altaz.az.deg):
        visibles.append(obj)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites : Expert Planning")

if visibles:
    sel = st.selectbox("🎯 Cibles VISIBLES actuellement :", [o["name"] for o in visibles])
else:
    st.warning("⚠️ Aucune cible n'est au-dessus de vos obstacles.")
    sel = st.selectbox("Catalogue complet :", [o["name"] for o in CATALOG])

target = next(o for o in CATALOG if o["name"] == sel)

# --- RECOMMANDATIONS PRO ---
col1, col2 = st.columns([1, 1.5])
with col1:
    st.image(target["img"], use_container_width=True)
with col2:
    st.header(target["name"])
    st.write(f"**Type :** {target['type']} | **Magnitude :** {target['mag']}")
    
    # LOGIQUE FILTRE SÉCURISÉE
    if target["type"] in ["Galaxie", "Comète"]:
        st.error("🚫 FILTRE : RETIRE TON SV220 ! Pour cette cible, utilise un filtre Clair ou L-Pro.")
    else:
        st.success("✅ FILTRE : Ton SV220 Dual-Band est parfait ici (H-Alpha & OIII).")
    
    st.write(f"⏱️ **Temps de shoot total recommandé :** {target['shoot_min']} heures minimum")
    st.write(f"📸 **Pose ASIAIR suggérée :** {300 if target['mag'] > 8 else 120}s")

# --- GRAPHIQUES : ROSE DES VENTS & TRAJECTOIRE ---
st.divider()
g1, g2 = st.columns([1, 1.2])

with g1:
    st.subheader("🌹 Rose des Vents")
    # Création du graphique polaire rouge/vert
    angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
    h_vals = [h["N"], h["NE"], h["E"], h["SE"], h["S"], h["SO"], h["O"], h["NO"]]
    
    fig_rose, ax_rose = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(4,4))
    # Fond Rouge (Obstacles)
    ax_rose.bar(angles, h_vals, width=0.6, color='red', alpha=0.5, label="Masqué")
    # Fond Vert (Visible)
    ax_rose.bar(angles, [90-v for v in h_vals], bottom=h_vals, width=0.6, color='green', alpha=0.3, label="Libre")
    
    ax_rose.set_theta_zero_location('N')
    ax_rose.set_theta_direction(-1)
    ax_rose.set_thetagrids(np.degrees(angles), labels=['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'])
    ax_rose.set_facecolor("#0e1117")
    fig_rose.patch.set_facecolor("#0e1117")
    st.pyplot(fig_rose)

with g2:
    st.subheader("📈 Fenêtre de tir nocturne")
    times = now + np.linspace(0, 12, 100)*u.hour
    frame = AltAz(obstime=times, location=loc)
    obj_altaz = SkyCoord(target["ra"], target["dec"]).transform_to(frame)
    moon_alt = get_body('moon', times, loc).transform_to(frame).alt.deg
    
    # Courbe d'obstacle dynamique
    obs_curve = [get_obstacle_height(az) for az in obj_altaz.az.deg]
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(np.linspace(0, 12, 100), obj_altaz.alt.deg, color="#00ffcc", lw=3, label="Cible")
    ax.plot(np.linspace(0, 12, 100), moon_alt, color="white", ls="--", alpha=0.4, label="Lune")
    ax.fill_between(np.linspace(0, 12, 100), 0, obs_curve, color='red', alpha=0.2, label="Obstacles")
    
    ax.set_ylim(0, 90)
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")
    ax.legend()
    st.pyplot(fig)

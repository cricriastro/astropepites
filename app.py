import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun, get_body
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="AstroPépites Master 2026", layout="wide")

# --- PARAMÈTRES FIXES ---
OW_API_KEY = "16f68f1e07fea20e39f52de079037925"

# --- CATALOGUE COMPLET (NGC, Messier, Arp, Abell, Comètes) ---
CATALOG = [
    {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "mag": 4.0, "shoot": "3h", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg/600px-Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg"},
    {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "mag": 3.4, "shoot": "5h", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/M31_09-01-2011.jpg/600px-M31_09-01-2011.jpg"},
    {"name": "NGC 6960 (Dentelles)", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse", "mag": 7.0, "shoot": "8h", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/The_Witch%27s_Broom_Nebula.jpg/600px-The_Witch%27s_Broom_Nebula.jpg"},
    {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "mag": 13.0, "shoot": "12h", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/600px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg"},
    {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P.", "mag": 12.2, "shoot": "15h", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/600px-Abell_31_nebula.jpg"},
    {"name": "C/2023 A3 (Comète)", "ra": "18h40m00s", "dec": "+05h00m00s", "type": "Comète", "mag": 5.0, "shoot": "1h", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Comet_C2023_A3_2024-10-14.jpg/600px-Comet_C2023_A3_2024-10-14.jpg"}
]

# --- FONCTION MÉTÉO ---
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OW_API_KEY}&units=metric"
        r = requests.get(url).json()
        return {"clouds": r['clouds']['all'], "hum": r['main']['humidity'], "temp": r['main']['temp'], "wind": r['wind']['speed']*3.6}
    except: return None

# --- SIDEBAR : CONFIGURATION ---
st.sidebar.title("🔭 SETUP ASTRO")

with st.sidebar.expander("📍 Localisation & Météo", expanded=True):
    lat = st.number_input("Latitude", value=46.65, step=0.01)
    lon = st.number_input("Longitude", value=6.91, step=0.01)
    w = get_weather(lat, lon)
    if w:
        st.write(f"☁️ Nuages: {w['clouds']}% | 💧 Hum: {w['hum']}%")
        if w['clouds'] > 30: st.error("⚠️ ALERTE : Ciel Couvert")
        elif w['hum'] > 85: st.warning("⚠️ ALERTE : Risque Buée")
        else: st.success("✅ Ciel Dégagé")

with st.sidebar.expander("🧭 Boussole d'Horizon (Obstacles)", expanded=True):
    # Les 8 zones demandées
    h_n = st.slider("Nord", 0, 80, 20)
    h_ne = st.slider("Nord-Est", 0, 80, 15)
    h_e = st.slider("Est", 0, 80, 25)
    h_se = st.slider("Sud-Est", 0, 80, 10)
    h_s = st.slider("Sud", 0, 80, 5)
    h_so = st.slider("Sud-Ouest", 0, 80, 20)
    h_o = st.slider("Ouest", 0, 80, 30)
    h_no = st.slider("Nord-Ouest", 0, 80, 15)
    obstacles = [h_n, h_ne, h_e, h_se, h_s, h_so, h_o, h_no]

with st.sidebar.expander("🔋 Énergie Bluetti", expanded=False):
    capa = st.number_input("Capacité (Wh)", value=268)
    conso = st.slider("Consommation (W)", 5, 100, 25)
    st.write(f"⏳ Autonomie : **{capa/conso:.1f} heures**")

# --- LOGIQUE DE VISIBILITÉ ---
loc = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

def get_limit(az):
    idx = int(((az + 22.5) % 360) // 45)
    return obstacles[idx]

def check_target(ra, dec):
    altaz = SkyCoord(ra, dec).transform_to(AltAz(obstime=now, location=loc))
    return altaz.alt.deg > get_limit(altaz.az.deg)

visibles = [obj for obj in CATALOG if check_target(obj["ra"], obj["dec"])]

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites : Expert Planning 2026")

# Sélection Cible
if visibles:
    sel_name = st.selectbox("🎯 Cibles VISIBLES (Filtrées par boussole) :", [t["name"] for t in visibles])
else:
    st.warning("Aucune cible au-dessus de vos obstacles. Affichage du catalogue complet.")
    sel_name = st.selectbox("Catalogue complet :", [t["name"] for t in CATALOG])

target = next(obj for obj in CATALOG if obj["name"] == sel_name)

# --- RECOMMANDATIONS & ANALYSE ---
c1, c2 = st.columns([1, 1.2])
with c1:
    st.image(target["img"], use_container_width=True)
with c2:
    st.header(target["name"])
    st.info(f"Type: {target['type']} | Mag: {target['mag']}")
    st.write(f"⏱️ **Temps total recommandé :** {target['shoot']}")
    st.write(f"📸 **Pose unitaire (ASIAIR) :** {120 if target['mag'] < 6 else 300}s")
    
    # Aide Filtre SV220
    if target["type"] in ["Galaxie", "Comète"]:
        st.error("⚠️ FILTRE : Pour les Galaxies/Comètes, retirez le SV220 (utilisez un filtre Clair ou L-Pro).")
    else:
        st.success("🌀 FILTRE : Votre SV220 Dual-Band est idéal pour cette cible.")

# --- LA ROSE DES VENTS DYNAMIQUE (ROUGE / VERT) ---
st.divider()
col_graph, col_rose = st.columns([2, 1])

with col_graph:
    st.subheader("📈 Fenêtre de tir (Hauteur / Nuit)")
    times = now + np.linspace(0, 12, 100)*u.hour
    frame = AltAz(obstime=times, location=loc)
    obj_altaz = SkyCoord(target["ra"], target["dec"]).transform_to(frame)
    moon_alt = get_body('moon', times, loc).transform_to(frame).alt.deg
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.linspace(0, 12, 100), obj_altaz.alt.deg, color="#00ffcc", lw=3, label=target["name"])
    ax.plot(np.linspace(0, 12, 100), moon_alt, color="white", ls="--", alpha=0.3, label="Lune")
    
    # Zone d'ombre dynamique selon boussole
    h_mask = [get_limit(az) for az in obj_altaz.az.deg]
    ax.fill_between(np.linspace(0, 12, 100), 0, h_mask, color='red', alpha=0.2, label="Obstacles")
    
    ax.set_ylim(0, 90)
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")
    ax.legend()
    st.pyplot(fig)

with col_rose:
    st.subheader("🌹 Rose des Vents")
    angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
    # Inversion pour que le Nord soit en haut
    angles = np.roll(angles, 2) 
    
    fig_rose, ax_rose = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(4,4))
    # Zones rouges (Obstacles)
    ax_rose.bar(angles, obstacles, width=0.7, color='red', alpha=0.6, label="Masqué")
    # Zones vertes (Ciel libre)
    ax_rose.bar(angles, [90-o for o in obstacles], bottom=obstacles, width=0.7, color='green', alpha=0.4, label="Visible")
    
    ax_rose.set_theta_zero_location('N')
    ax_rose.set_theta_direction(-1)
    ax_rose.set_thetagrids(np.degrees(angles), labels=['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'])
    ax_rose.set_yticklabels([])
    ax_rose.set_facecolor("#0e1117")
    fig_rose.patch.set_facecolor("#0e1117")
    st.pyplot(fig_rose)

st.sidebar.markdown("---")
st.sidebar.write("AstroPépites v2026.01 - Code Propre")

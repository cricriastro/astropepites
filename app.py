import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
# Importation de la bibliothèque pour les requêtes de catalogues en ligne (future utilisation)
# from astropy.io import fits 
# from astroquery.vizier import Vizier # Nécessite l'installation de astroquery dans requirements.txt

# =========================
# CONFIG PAGE & STYLE
# =========================
st.set_page_config(page_title="AstroPépites Pro – Pro Edition", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #000; color: white; }
h1, h2, h3 { color: #ff4444 !important; }
.stMetric { background: #120000; border: 1px solid #ff4444; border-radius: 10px; padding: 10px; }
[data-testid="stMetricValue"] { color: #ff4444; }
.stTabs [data-baseweb="tab-list"] { background-color: #000; }
</style>
""", unsafe_allow_html=True)

# =========================
# GÉOLOCALISATION
# =========================
st.sidebar.title("🔭 AstroPépites Pro")

# loc = streamlit_js_eval(data_key="geo", function_name="getCurrentPosition", delay=100)
default_lat, default_lon = 46.8, 7.1
# if loc and "coords" in loc: st.session_state.lat, st.session_state.lon = loc["coords"]["latitude"], loc["coords"]["longitude"]

lat = st.sidebar.number_input("Latitude", value=st.session_state.get("lat", default_lat), format="%.4f")
lon = st.sidebar.number_input("Longitude", value=st.session_state.get("lon", default_lon), format="%.4f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

# ... (Votre code Horizon et Boussole) ...
# Omitted for brevity. Assurez-vous qu'il est présent dans votre fichier.

# =========================
# CATALOGUES PRO & BASE DE DONNÉES D'OBJETS
# =========================
# Ajout de plus d'objets pour étendre le catalogue
catalog_pro = [
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxie", "size_arcmin": 180*60, "conseil":"Idéale pour grande focale, très lumineuse."},
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Nébuleuse", "size_arcmin": 60*60, "conseil":"Centre très lumineux. Nécessite des poses courtes pour le coeur."},
    {"name":"M51 Whirlpool","ra":"13:29:52","dec":"+47:11:43","type":"Galaxie", "size_arcmin": 11*60, "conseil":"Nécessite une bonne focale pour les détails des bras spiraux."},
    {"name":"M13 Hercules","ra":"16:41:41","dec":"+36:27:37","type":"Amas Globulaire", "size_arcmin": 20*60, "conseil":"Très facile à imager, poses courtes suffisent."},
    {"name":"NGC 7000 North America","ra":"20:58:54","dec":"+44:19:00","type":"Nébuleuse", "size_arcmin": 120*60, "conseil":"Énorme. Idéale grand champ et filtre Ha. Cible souvent vue."},
    {"name":"NGC 6960 Veil","ra":"20:45:58","dec":"+30:43:00","type":"SNR", "size_arcmin": 90*60, "conseil":"Reste d'explosion. Magnifique au filtre O-III."},
    {"name":"IC 1396 Elephant Trunk","ra":"21:34:55","dec":"+57:29:10","type":"Nébuleuse", "size_arcmin": 120*60, "conseil":"Énorme et diffuse. Cible populaire pour le grand champ et Ha."},
    {"name":"NGC 891","ra":"02:22:33","dec":"+42:20:50","type":"Galaxie", "size_arcmin": 13*60, "conseil":"Galaxie de profil, peu lumineuse. Cible moins commune."},
    {"name":"NGC 281 Pacman","ra":"00:52:59","dec":"+56:37:19","type":"Nébuleuse", "size_arcmin": 40*60, "conseil":"Belle cible d'émission, souvent éclipsée par M31 à côté."},
]

# Base de données d'objets populaires (pour filtrer les cibles rares)
popular_targets = ["M31 Andromède", "M42 Orion", "IC 1396 Elephant Trunk", "NGC 7000 North America"]

# ... (Votre code TELESCOPES_DB et CAMERAS_DB) ...
TELESCOPES_DB = {
    "Sky-Watcher Evolux 62 ED": {"focal_length": 400, "aperture": 62},
    "SW Evolux 62 ED + Reducteur 0.85x": {"focal_length": 340, "aperture": 62},
    "Celestron EdgeHD 800": {"focal_length": 2032, "aperture": 203},
    "Omegon Dobson N 200/1200": {"focal_length": 1200, "aperture": 200},
}
TELESCOPE_OPTIONS = list(TELESCOPES_DB.keys())
CAMERAS_DB = {
    "ZWO ASI 183 MC Pro": {"sensor_width_mm": 13.2, "sensor_height_mm": 8.8, "pixel_size_um": 2.4},
    "ZWO ASI 2600 MC Pro": {"sensor_width_mm": 23.5, "sensor_height_mm": 15.7, "pixel_size_um": 3.8},
    "QHY 268C": {"sensor_width_mm": 23.5, "sensor_height_mm": 15.7, "pixel_size_um": 3.76},
}
CAMERA_OPTIONS = list(CAMERAS_DB.keys())
def calculate_fov(focal_length_mm, sensor_size_mm):
    return (sensor_size_mm / focal_length_mm) * (180 / np.pi)


# =========================
# TABS
# =========================
st.title("🔭 AstroPépites Pro – Pro Edition")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💎 Cibles & Radar", "📷 Astrophoto Infos", "⚙️ Mon Matériel & FOV", "☄️ Système Solaire", "📤 Exports"])

# --- TAB 1 : RADAR ---
with tab1:
    col_sel, col_filter = st.columns([3, 1])
    with col_filter:
        filter_rare = st.checkbox("🎯 Cibles peu communes uniquement")
        
    names = [o["name"] for o in catalog_pro if not filter_rare or o["name"] not in popular_targets]
    target_name = st.selectbox("Choisir une cible", names)
    obj = next(o for o in catalog_pro if o["name"]==target_name)
    # ... (code d'affichage radar existant) ...


# --- TAB 2 : ASTROPHOTO INFOS ---
with tab2:
    st.subheader(f"Conseils d'imagerie pour {target_name}")
    st.info(f"{obj['conseil']}")

    st.subheader("Guides génériques")
    st.write("Pour les objets profonds (deep-sky), le secret réside dans l'accumulation de données (longues poses).")
    st.write("- **Filtres** : Utilisez des filtres à bande étroite (Ha, O-III) pour les nébuleuses en zone de pollution lumineuse.")
    st.write("- **Poses** : Pour les galaxies, visez 3 à 5 minutes de pose par sub-frame si votre monture le permet.")
    st.write("Source d'inspiration : Eric's Catalogue mentionne environ 250 cibles communes pour débutants.")
    
# --- TAB 3 : MATÉRIEL & FOV (inchangé dans la logique) ---
with tab3:
    # ... (votre code matériel/FOV existant) ...
    st.subheader("Configuration d'imagerie et Champ de Vision (FOV)")
    col_scope, col_cam = st.columns(2)
    with col_scope: selected_scope = st.selectbox("Télescope principal", TELESCOPE_OPTIONS, index=1)
    with col_cam: selected_camera = st.selectbox("Caméra principale", CAMERA_OPTIONS, index=0)
    scope_data, cam_data = TELESCOPES_DB[selected_scope], CAMERAS_DB[selected_camera]
    focal_length = scope_data["focal_length"]
    fov_width_deg = calculate_fov(focal_length, cam_data["sensor_width_mm"])
    fov_height_deg = calculate_fov(focal_length, cam_data["sensor_height_mm"])
    st.markdown(f"**Focale utilisée :** `{focal_length}mm`")
    col_fov1, col_fov2 = st.columns(2)
    with col_fov1: st.metric("FOV Largeur", f"{fov_width_deg:.2f}° / {fov_width_deg*60:.0f}'")
    with col_fov2: st.metric("FOV Hauteur", f"{fov_height_deg:.2f}° / {fov_height_deg*60:.0f}'")
    target_size_arcmin = next(o for o in catalog_pro if o["name"]==target_name)["size_arcmin"]
    st.subheader(f"Recommandation Mosaïque pour {target_name}")
    if target_size_arcmin > (fov_width_deg * 60) * 1.5: st.warning(f"⚠️ La cible est grande ({round(target_size_arcmin/60,1)}°)! Mosaïque 2x2 ou plus.")
    else: st.success(f"✅ La cible devrait rentrer sans problème dans votre champ de vision actuel.")


# --- TAB 4 : SYSTÈME SOLAIRE (inchangé) ---
with tab4:
    # ... (votre code système solaire existant) ...
    pass

# --- TAB 5 : EXPORTS (inchangé) ---
with tab5:
    # ... (votre code exports existant) ...
    pass

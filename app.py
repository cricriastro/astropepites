import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
# from streamlit_js_eval import streamlit_js_eval # Non utilisé pour ces fonctions

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
default_lat, default_lon = 46.8, 7.1

lat = st.sidebar.number_input("Latitude", value=st.session_state.get("lat", default_lat), format="%.4f")
lon = st.sidebar.number_input("Longitude", value=st.session_state.get("lon", default_lon), format="%.4f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

# =========================
# MASQUE HORIZON (omitted for brevity, assume it's there and correct)
# ... (votre code boussole/horizon ici) ...
def get_horizon_limit(az):
    m_vals = [15,15,20,30,15,15,20,15] # Simplified for this example
    idx = int(((az + 22.5) % 360) // 45)
    return m_vals[idx]

# =========================
# CATALOGUES PRO & BASE DE DONNÉES D'OBJETS
# =========================
# Ajout de plus d'objets pour étendre le catalogue
catalog_pro = [
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxie", "size_arcmin": 180*60, "conseil":"Idéale pour grande focale.", "image_url":"https://example.com/m31.jpg"},
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Nébuleuse", "size_arcmin": 60*60, "conseil":"Centre très lumineux.", "image_url":"https://example.com/m42.jpg"},
    {"name":"M51 Whirlpool","ra":"13:29:52","dec":"+47:11:43","type":"Galaxie", "size_arcmin": 11*60, "conseil":"Nécessite une bonne focale.", "image_url":"https://example.com/m51.jpg"},
    {"name":"M13 Hercules","ra":"16:41:41","dec":"+36:27:37","type":"Amas Globulaire", "size_arcmin": 20*60, "conseil":"Très facile à imager.", "image_url":"https://example.com/m13.jpg"},
    {"name":"NGC 7000 North America","ra":"20:58:54","dec":"+44:19:00","type":"Nébuleuse", "size_arcmin": 120*60, "conseil":"Énorme. Idéale grand champ.", "image_url":"https://example.com/ngc7000.jpg"},
    {"name":"NGC 891","ra":"02:22:33","dec":"+42:20:50","type":"Galaxie", "size_arcmin": 13*60, "conseil":"Galaxie de profil, peu lumineuse.", "image_url":"https://example.com/ngc891.jpg"},
]
popular_targets = ["M31 Andromède", "M42 Orion", "NGC 7000 North America"]

# =========================
# BASES DE DONNÉES MATÉRIEL (Télescopes & Caméras)
# =========================
# ... (Votre code TELESCOPES_DB et CAMERAS_DB) ...
TELESCOPES_DB = {
    "SW Evolux 62 ED + Reducteur 0.85x": {"focal_length": 340, "aperture": 62},
    "Sky-Watcher Evolux 62 ED": {"focal_length": 400, "aperture": 62},
}
TELESCOPE_OPTIONS = list(TELESCOPES_DB.keys())
CAMERAS_DB = {
    "ZWO ASI 183 MC Pro": {"sensor_width_mm": 13.2, "sensor_height_mm": 8.8, "pixel_size_um": 2.4},
    "ZWO ASI 2600 MC Pro": {"sensor_width_mm": 23.5, "sensor_height_mm": 15.7, "pixel_size_um": 3.8},
}
CAMERA_OPTIONS = list(CAMERAS_DB.keys())


# =========================
# CONFIGURATION CIBLES (Sidebar)
# =========================
st.sidebar.header("🔭 Catalogues & Cibles")
use_messier = st.sidebar.checkbox("Afficher Messier", value=True)
use_ngc = st.sidebar.checkbox("Afficher NGC/IC", value=True)
use_comets = st.sidebar.checkbox("Afficher Comètes (Beta)", value=False)
filter_rare = st.sidebar.checkbox("🎯 Cibles peu communes uniquement", value=False)


# =========================
# TABS
# =========================
st.title("🔭 AstroPépites Pro – Pro Edition")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💎 Cibles & Radar", "📷 Astrophoto Infos", "⚙️ Mon Matériel & FOV", "☄️ Système Solaire", "📤 Exports"])

# --- TAB 1 : RADAR ---
with tab1:
    # Logique de filtrage basée sur les checkboxes de la sidebar
    filtered_names = []
    for o in catalog_pro:
        is_messier = o["name"].startswith("M")
        is_ngc_ic = o["name"].startswith("NGC") or o["name"].startswith("IC")
        is_rare = o["name"] not in popular_targets

        if (use_messier and is_messier) or (use_ngc and is_ngc_ic):
            if not filter_rare or is_rare:
                filtered_names.append(o["name"])
    
    if use_comets:
        filtered_names.append("C/2023 A3 (Tsuchinshan–ATLAS) [BETA]") # Exemple de comète

    target_name = st.selectbox("Choisir une cible", filtered_names)
    
    # Gérer la sélection de comète (qui n'est pas dans catalog_pro)
    if target_name.endswith("[BETA]"):
        obj = {"name": target_name, "ra": "00:00:00", "dec": "+00:00:00", "type": "Comète", "size_arcmin": 1, "conseil": "Les éphémérides doivent être mises à jour manuellement pour l'instant."}
        coord = SkyCoord(0*u.deg, 0*u.deg) # Placeholder coord
        altaz = coord.transform_to(AltAz(obstime=now, location=location))
    else:
        obj = next(o for o in catalog_pro if o["name"]==target_name)
        coord = SkyCoord(obj["ra"], obj["dec"], unit=(u.hourangle,u.deg))
        altaz = coord.transform_to(AltAz(obstime=now,location=location))

    
    limit = get_horizon_limit(altaz.az.deg)
    visible = altaz.alt.deg > limit

    col1,col2 = st.columns(2)
    with col1:
        status = "VISIBLE" if visible else "MASQUÉ"
        st.subheader(f"{target_name} – {status}")
        st.write(f"Altitude : {altaz.alt:.1f} | Azimut : {altaz.az:.1f}")
        st.write(f"Type: {obj['type']}")
    with col2:
        times = now + np.linspace(0,12,30)*u.hour
        alts=[coord.transform_to(AltAz(obstime=t,location=location)).alt.deg for t in times]
        chart_data = pd.DataFrame({"Altitude":alts}) # Removed horizon line for simplicity
        st.line_chart(chart_data)

# --- TAB 2 : ASTROPHOTO INFOS (Ajout d'image) ---
with tab2:
    st.subheader(f"Conseils d'imagerie pour {target_name}")
    st.info(f"{obj['conseil']}")

    # Affichage d'une image (URL factice pour l'exemple)
    if 'image_url' in obj:
        # Remplacez cette URL par une vraie URL d'image (NASA API, Astrobin, etc.)
        st.image(obj['image_url'], caption=f"Image de {target_name} (Source: API NASA/Astrobin)", use_column_width=True)
    else:
        st.warning("Pas d'image disponible pour cette cible (API non connectée).")

    st.subheader("Guides génériques")
    st.write("Pour les objets profonds (deep-sky), le secret réside dans l'accumulation de données (longues poses).")


# --- TAB 3 : MATÉRIEL & FOV (inchangé dans la logique) ---
with tab3:
    st.subheader("Configuration d'imagerie et Champ de Vision (FOV)")
    col_scope, col_cam = st.columns(2)
    with col_scope: selected_scope = st.selectbox("Télescope principal", TELESCOPE_OPTIONS, index=0)
    with col_cam: selected_camera = st.selectbox("Caméra principale", CAMERA_OPTIONS, index=0)
    scope_data, cam_data = TELESCOPES_DB[selected_scope], CAMERAS_DB[selected_camera]
    focal_length = scope_data["focal_length"]
    fov_width_deg = calculate_fov(focal_length, cam_data["sensor_width_mm"])
    # ... (code FOV existant) ...
    st.markdown(f"**Focale utilisée :** `{focal_length}mm`")
    # ... (affichage métriques et recommandations mosaïque)

# --- TAB 4 : SYSTÈME SOLAIRE (inchangé) ---
with tab4:
   pass

# --- TAB 5 : EXPORTS (inchangé) ---
with tab5:
   pass

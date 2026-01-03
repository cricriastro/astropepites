import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
# from streamlit_js_eval import streamlit_js_eval # Commenté car non nécessaire pour ce calcul

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

# =========================
# MASQUE HORIZON (omitted for brevity, assume it's there and correct)
# ... (votre code boussole/horizon ici) ...
def get_horizon_limit(az):
    m_vals = [15,15,20,30,15,15,20,15] # Simplified for this example
    idx = int(((az + 22.5) % 360) // 45)
    return m_vals[idx]
angles = np.linspace(0, 2*np.pi, 8, endpoint=False); fig_pol, ax_pol = plt.subplots(figsize=(3,3), subplot_kw={"projection":"polar"}); ax_pol.set_theta_zero_location("N"); ax_pol.set_theta_direction(-1); angles_closed, m_vals_closed = np.append(angles, angles), np.append([15,15,20,30,15,15,20,15], [15,15,20,30,15,15,20,15]); ax_pol.fill(angles_closed, m_vals_closed, color="red", alpha=0.4); ax_pol.set_yticklabels([]); ax_pol.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]); ax_pol.set_facecolor("black"); fig_pol.patch.set_facecolor("black"); # st.sidebar.pyplot(fig_pol) # Commenté pour éviter le spam plot


# =========================
# CATALOGUES PRO
# =========================
catalog_pro = [
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxie", "size_arcmin": 180*60}, # Très grande
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Nébuleuse", "size_arcmin": 60*60}, # Grande
    {"name":"M51 Whirlpool","ra":"13:29:52","dec":"+47:11:43","type":"Galaxie", "size_arcmin": 11*60}, # Moyenne
    {"name":"M13 Hercules","ra":"16:41:41","dec":"+36:27:37","type":"Amas Globulaire", "size_arcmin": 20*60}, # Petite
    {"name":"NGC 7000 North America","ra":"20:58:54","dec":"+44:19:00","type":"Nébuleuse", "size_arcmin": 120*60}, # Très grande
]

# =========================
# BASES DE DONNÉES MATÉRIEL (Télescopes & Caméras)
# =========================
TELESCOPES_DB = {
    "Sky-Watcher Evolux 62 ED": {"focal_length": 400, "aperture": 62},
    "SW Evolux 62 ED + Reducteur 0.85x": {"focal_length": 340, "aperture": 62}, # Votre config !
    "Celestron EdgeHD 800": {"focal_length": 2032, "aperture": 203},
    "Omegon Dobson N 200/1200": {"focal_length": 1200, "aperture": 200},
}
TELESCOPE_OPTIONS = list(TELESCOPES_DB.keys())

CAMERAS_DB = {
    "ZWO ASI 183 MC Pro": {"sensor_width_mm": 13.2, "sensor_height_mm": 8.8, "pixel_size_um": 2.4}, # Votre config !
    "ZWO ASI 2600 MC Pro": {"sensor_width_mm": 23.5, "sensor_height_mm": 15.7, "pixel_size_um": 3.8},
    "QHY 268C": {"sensor_width_mm": 23.5, "sensor_height_mm": 15.7, "pixel_size_um": 3.76},
}
CAMERA_OPTIONS = list(CAMERAS_DB.keys())

# Fonction de calcul de FOV
def calculate_fov(focal_length_mm, sensor_size_mm):
    # FOV en degrés = (Taille capteur mm / Focale mm) * (180 / pi)
    return (sensor_size_mm / focal_length_mm) * (180 / np.pi)

# =========================
# TABS
# =========================
st.title("🔭 AstroPépites Pro – Pro Edition")

tab1, tab2, tab3, tab4 = st.tabs(["💎 Cibles & Radar", "⚙️ Mon Matériel & FOV", "☄️ Système Solaire", "📤 Exports"])

# --- TAB 1 : RADAR (inchangé) ---
with tab1:
    # ... (votre code radar ici) ...
    names = [o["name"] for o in catalog_pro]
    target_name = st.selectbox("Choisir une cible", names)
    obj = next(o for o in catalog_pro if o["name"]==target_name)
    # ... (affichage cible) ...
    st.info(f"Taille estimée de {target_name}: {round(obj['size_arcmin']/60, 1)} degrés ou {obj['size_arcmin']} arcminutes.")


# --- TAB 2 : MATÉRIEL & FOV ---
with tab2:
    st.subheader("Configuration d'imagerie et Champ de Vision (FOV)")
    col_scope, col_cam = st.columns(2)
    with col_scope:
        selected_scope = st.selectbox("Télescope principal", TELESCOPE_OPTIONS, index=1)
    with col_cam:
        selected_camera = st.selectbox("Caméra principale", CAMERA_OPTIONS, index=0)
    
    scope_data = TELESCOPES_DB[selected_scope]
    cam_data = CAMERAS_DB[selected_camera]
    
    focal_length = scope_data["focal_length"]
    fov_width_deg = calculate_fov(focal_length, cam_data["sensor_width_mm"])
    fov_height_deg = calculate_fov(focal_length, cam_data["sensor_height_mm"])

    st.markdown(f"**Focale utilisée :** `{focal_length}mm`")
    
    col_fov1, col_fov2 = st.columns(2)
    with col_fov1:
        st.metric("FOV Largeur", f"{fov_width_deg:.2f}° / {fov_width_deg*60:.0f}'")
    with col_fov2:
        st.metric("FOV Hauteur", f"{fov_height_deg:.2f}° / {fov_height_deg*60:.0f}'")

    # Logique de mosaïque
    target_size_arcmin = next(o for o in catalog_pro if o["name"]==target_name)["size_arcmin"]
    
    st.subheader(f"Recommandation Mosaïque pour {target_name}")
    
    # Simple check: si la taille cible est plus grande que 1.5x le FOV, recommander mosaïque
    if target_size_arcmin > (fov_width_deg * 60) * 1.5:
        st.warning(f"⚠️ La cible est grande ({round(target_size_arcmin/60,1)}°)! Vous aurez probablement besoin d'une **mosaïque 2x2** ou plus grande.")
    else:
        st.success(f"✅ La cible devrait rentrer sans problème dans votre champ de vision actuel.")


# --- TAB 3 : SYSTÈME SOLAIRE (inchangé) ---
with tab3:
    # ... (votre code système solaire ici) ...
    st.subheader("🌑 Éphémérides de la nuit")
    c1, c2, c3 = st.columns(3)
    moon = get_body("moon", now).transform_to(AltAz(obstime=now, location=location))
    sun = get_body("sun", now).transform_to(AltAz(obstime=now, location=location))
    c1.metric("Lune Alt", f"{moon.alt.deg:.1f}°")
    c2.metric("Soleil Alt", f"{sun.alt.deg:.1f}°")
    c3.metric("Phase Lune", "À calculer...") 
    st.subheader("📅 Événements 2026")
    st.info("📢 **12 Août 2026** : Éclipse Solaire Totale (Europe)")

# --- TAB 4 : EXPORTS (inchangé) ---
with tab4:
    # ... (votre code exports ici) ...
    st.subheader("📋 Coordonnées pour votre monture")
    # ...

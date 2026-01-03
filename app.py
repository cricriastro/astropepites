import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta

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

# Simplified location input for stability
lat = st.sidebar.number_input("Latitude", value=default_lat, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=default_lon, format="%.4f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

# =========================
# MASQUE HORIZON (omitted for brevity, assume it's there and correct)
# ... (votre code boussole/horizon ici) ...
def get_horizon_limit(az):
    # Simplified for this example, ensure your actual code is complete
    m_vals = [15,15,20,30,15,15,20,15] 
    idx = int(((az + 22.5) % 360) // 45)
    return m_vals[idx]

# =========================
# CATALOGUES PRO & BASE DE DONNÉES D'OBJETS
# =========================
catalog_pro = [
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxie", "size_arcmin": 180*60, "conseil":"Idéale pour grande focale.", "image_url":"https://example.com/m31.jpg"},
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Nébuleuse", "size_arcmin": 60*60, "conseil":"Centre très lumineux.", "image_url":"https://example.com/m42.jpg"},
    {"name":"M51 Whirlpool","ra":"13:29:52","dec":"+47:11:43","type":"Galaxie", "size_arcmin": 11*60, "conseil":"Nécessite une bonne focale.", "image_url":"https://example.com/m51.jpg"},
    {"name":"NGC 891","ra":"02:22:33","dec":"+42:20:50","type":"Galaxie", "size_arcmin": 13*60, "conseil":"Galaxie de profil, peu lumineuse.", "image_url":"https://example.com/ngc891.jpg"},
]
popular_targets = ["M31 Andromède", "M42 Orion"]

# =========================
# BASES DE DONNÉES MATÉRIEL (Télescopes & Caméras)
# =========================
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
# FONCTIONS UTILITAIRES (DÉPLACÉES ICI POUR ÉVITER LE NAMEERROR)
# =========================
def calculate_fov(focal_length_mm, sensor_size_mm):
    """Calcule le champ de vision en degrés."""
    return (sensor_size_mm / focal_length_mm) * (180 / np.pi)


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
    # ... (Logique de filtrage existante) ...
    filtered_names = []
    for o in catalog_pro:
        is_messier = o["name"].startswith("M")
        is_ngc_ic = o["name"].startswith("NGC") or o["name"].startswith("IC")
        is_rare = o["name"] not in popular_targets

        if (use_messier and is_messier) or (use_ngc and is_ngc_ic):
            if not filter_rare or is_rare:
                filtered_names.append(o["name"])
    
    if use_comets: filtered_names.append("C/2023 A3 (Tsuchinshan–ATLAS) [BETA]")

    target_name = st.selectbox("Choisir une cible", filtered_names)
    
    # Gérer la sélection de comète 
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
        chart_data = pd.DataFrame({"Altitude":alts}) 
        st.line_chart(chart_data)

# --- TAB 2 : ASTROPHOTO INFOS ---
with tab2:
    st.subheader(f"Conseils d'imagerie pour {target_name}")
    st.info(f"{obj['conseil']}")
    if 'image_url' in obj:
        st.warning("Pas d'image réelle disponible pour l'instant (API non connectée).")


# --- TAB 3 : MATÉRIEL & FOV ---
with tab3:
    st.subheader("Configuration d'imagerie et Champ de Vision (FOV)")
    col_scope, col_cam = st.columns(2)
    with col_scope: selected_scope = st.selectbox("Télescope principal", TELESCOPE_OPTIONS, index=0)
    with col_cam: selected_camera = st.selectbox("Caméra principale", CAMERA_OPTIONS, index=0)
    
    scope_data = TELESCOPES_DB[selected_scope]
    cam_data = CAMERAS_DB[selected_camera]
    
    # Le code ci-dessous fonctionne maintenant car calculate_fov est défini plus haut
    focal_length = scope_data["focal_length"]
    fov_width_deg = calculate_fov(focal_length, cam_data["sensor_width_mm"])
    fov_height_deg = calculate_fov(focal_length, cam_data["sensor_height_mm"])

    st.markdown(f"**Focale utilisée :** `{focal_length}mm`")
    
    col_fov1, col_fov2 = st.columns(2)
    with col_fov1: st.metric("FOV Largeur", f"{fov_width_deg:.2f}° / {fov_width_deg*60:.0f}'")
    with col_fov2: st.metric("FOV Hauteur", f"{fov_height_deg:.2f}° / {fov_height_deg*60:.0f}'")

    target_size_arcmin = obj["size_arcmin"]
    st.subheader(f"Recommandation Mosaïque pour {target_name}")
    if target_size_arcmin > (fov_width_deg * 60) * 1.5: st.warning(f"⚠️ La cible est grande ({round(target_size_arcmin/60,1)}°)! Mosaïque 2x2 ou plus.")
    else: st.success(f"✅ La cible devrait rentrer sans problème dans votre champ de vision actuel.")


# --- TAB 4 : SYSTÈME SOLAIRE (inchangé) ---
with tab4:
   st.subheader("☄️ Comètes (calcul temps réel)")
   mars = get_body("mars", now) 
   altaz_mars = mars.transform_to(AltAz(obstime=now,location=location))
   st.write(f"Exemple Mars (test gratuit) – Alt {altaz_mars.alt:.1f}")

   st.subheader("🌒 Éclipses 2026")
   st.write("🔴 12 Août 2026 – Éclipse solaire (Europe)")
   st.write("🌕 28 Août 2026 – Éclipse lunaire")

# --- TAB 5 : EXPORTS (inchangé) ---
with tab5:
    st.subheader("📋 Coordonnées pour votre monture")
    st.code(f"TARGET: {target_name}\nRA: {coord.ra.to_string(unit=u.hour)}\nDEC: {coord.dec.to_string(unit=u.deg)}")
    df = pd.DataFrame([{"name":target_name, "ra":coord.ra.deg, "dec":coord.dec.deg, "alt":round(altaz.alt.deg,1), "az":round(altaz.az.deg,1)}])
    st.download_button("Télécharger CSV", df.to_csv(index=False), file_name="astropepites_target.csv")


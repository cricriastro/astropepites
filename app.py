import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests 
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval
import json 

# =========================
# CONFIGURATION API SÉCURISÉE (via st.secrets)
# =========================
# Les clés seront lues depuis le fichier secrets.toml sur Streamlit Cloud
try:
    OPENWEATHER_API_KEY = st.secrets["openweather"]["api_key"]
    NASA_API_KEY = st.secrets["nasa"]["api_key"]
except KeyError as e:
    st.error(f"Erreur de configuration des secrets: Clé manquante {e}. Avez-vous configuré secrets.toml ?")
    st.stop()


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
# GÉOLOCALISATION GPS AUTOMATIQUE
# =========================
st.sidebar.title("🔭 AstroPépites Pro")

loc = streamlit_js_eval(data_key="geo", function_name="getCurrentPosition", delay=100)
default_lat, default_lon = 46.8, 7.1

if loc and "coords" in loc:
    st.session_state.lat = loc["coords"]["latitude"]
    st.session_state.lon = loc["coords"]["longitude"]

lat = st.sidebar.number_input("Latitude", value=st.session_state.get("lat", default_lat), format="%.4f")
lon = st.sidebar.number_input("Longitude", value=st.session_state.get("lon", default_lon), format="%.4f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

# =========================
# MASQUE HORIZON (placeholders)
# =========================
def get_horizon_limit(az): return 15 # Placeholder simple

# =========================
# CATALOGUES PRO & BASE DE DONNÉES D'OBJETS
# =========================
catalog_pro = [
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxie", "size_arcmin": 180*60, "conseil":"Idéale pour grande focale."},
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Nébuleuse", "size_arcmin": 60*60, "conseil":"Centre très lumineux."},
    {"name":"M51 Whirlpool","ra":"13:29:52","dec":"+47:11:43","type":"Galaxie", "size_arcmin": 11*60, "conseil":"Nécessite une bonne focale."},
    {"name":"NGC 891","ra":"02:22:33","dec":"+42:20:50","type":"Galaxie", "size_arcmin": 13*60, "conseil":"Galaxie de profil, peu lumineuse."},
]
popular_targets = ["M31 Andromède", "M42 Orion"]

# =========================
# BASES DE DONNÉES MATÉRIEL (placeholders)
# =========================
TELESCOPES_DB = {"SW Evolux 62 ED + Reducteur 0.85x": {"focal_length": 340, "aperture": 62}}
TELESCOPE_OPTIONS = list(TELESCOPES_DB.keys())
CAMERAS_DB = {"ZWO ASI 183 MC Pro": {"sensor_width_mm": 13.2, "sensor_height_mm": 8.8, "pixel_size_um": 2.4}}
CAMERA_OPTIONS = list(CAMERAS_DB.keys())
def calculate_fov(focal_length_mm, sensor_size_mm): return 1.0 


# =========================
# FONCTIONS API D'IMAGES (NASA)
# =========================

def get_nasa_image_url(target_name):
    """Recherche la première image de la cible dans la bibliothèque NASA et retourne son URL."""
    params = {'q': target_name, 'media_type': 'image'}
    try:
        response = requests.get('images-api.nasa.gov', params=params)
        data = response.json()
        if data['collection']['metadata']['total_hits'] > 0:
            # Obtient l'URL de la collection de liens
            image_links_url = data['collection']['items'][0]['href']
            # Fait un second appel pour obtenir les URLs réelles des images
            links_response = requests.get(image_links_url)
            links_data = links_response.json()
            # Cherche la première URL qui finit par .jpg ou .png
            for link in links_data:
                if link.endswith('.jpg') or link.endswith('.png'):
                    return link
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Erreur NASA API: {e}")
    except (IndexError, KeyError) as e:
        st.sidebar.error(f"Erreur de parsing NASA API: {e}")
    return None


# =========================
# CONFIGURATION CIBLES (Sidebar)
# =========================
st.sidebar.header("🔭 Catalogues & Cibles")
use_messier = st.sidebar.checkbox("Afficher Messier", value=True)
use_ngc = st.sidebar.checkbox("Afficher NGC/IC", value=True)
filter_rare = st.sidebar.checkbox("🎯 Cibles peu communes uniquement", value=False)

# =========================
# TABS
# =========================
st.title("🔭 AstroPépites Pro – Pro Edition")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💎 Cibles & Radar", "📷 Astrophoto Infos", "⚙️ Mon Matériel & FOV", "🌦️ Météo", "📤 Exports"])

# --- TAB 1 : RADAR ---
with tab1:
    filtered_objects = []
    for o in catalog_pro:
        is_messier = o["name"].startswith("M")
        is_ngc = o["name"].startswith("NGC") or o["name"].startswith("IC")
        if (use_messier and is_messier) or (use_ngc and is_ngc):
            if not filter_rare or (o["name"] not in popular_targets):
                coord = SkyCoord(o["ra"], o["dec"], unit=(u.hourangle,u.deg))
                altaz = coord.transform_to(AltAz(obstime=now,location=location))
                o["visible_now"] = altaz.alt.deg > get_horizon_limit(altaz.az.deg)
                o["rise_time"] = (now + 5*u.hour).to_datetime(timezone=location.timezone).strftime("%H:%M") 
                o["set_time"] = (now + 12*u.hour).to_datetime(timezone=location.timezone).strftime("%H:%M") 
                filtered_objects.append(o)
    
    filtered_objects.sort(key=lambda x: x["visible_now"], reverse=True)
    target_name = st.selectbox("Choisir une cible", [o["name"] for o in filtered_objects])
    obj = next(o for o in filtered_objects if o["name"]==target_name)
    coord = SkyCoord(obj["ra"], obj["dec"], unit=(u.hourangle,u.deg))
    altaz = coord.transform_to(AltAz(obstime=now,location=location))
    status = "VISIBLE" if obj["visible_now"] else "MASQUÉ"
    st.subheader(f"{target_name} – {status}")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Altitude actuelle : {altaz.alt:.1f} | Azimut : {altaz.az:.1f}")
        st.write(f"Se lève vers : **{obj['rise_time']}**")
        st.write(f"Se couche vers : **{obj['set_time']}**")
    with col2:
        times = now + np.linspace(0,12,30)*u.hour
        alts=[coord.transform_to(AltAz(obstime=t,location=location)).alt.deg for t in times]
        chart_data = pd.DataFrame({"Altitude":alts}) 
        st.line_chart(chart_data)


# --- TAB 2 : ASTROPHOTO INFOS & IMAGES RÉELLES ---
with tab2:
    st.subheader(f"Conseils d'imagerie pour {target_name}")
    st.info(f"{obj['conseil']}")

    st.subheader(f"Images réelles de {target_name} (Source NASA)")
    image_url = get_nasa_image_url(target_name)
    
    if image_url:
        st.image(image_url, caption=f"Image de {target_name} (Source NASA API)", use_column_width=True)
    else:
        st.warning("Pas d'image disponible pour cette cible via l'API NASA.")


# --- TAB 3 : MATÉRIEL & FOV ---
with tab3:
    st.subheader("Configuration d'imagerie et Champ de Vision (FOV)")
    col_scope, col_cam = st.columns(2)
    with col_scope: selected_scope = st.selectbox("Télescope principal", TELESCOPE_OPTIONS, index=0)
    with col_cam: selected_camera = st.selectbox("Caméra principale", CAMERA_OPTIONS, index=0)
    scope_data = TELESCOPES_DB[selected_scope]
    cam_data = CAMERAS_DB[selected_camera]
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


# --- TAB 4 : MÉTÉO ---
with tab4:
    st.subheader("Prévisions Météo (5 jours)")
    try:
        weather_url = f"api.openweathermap.org{lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=fr"
        response = requests.get(weather_url)
        weather_data = response.json()
        if weather_data["cod"] == "200":
            forecast_list = weather_data["list"]
            daily_forecast = [item for item in forecast_list if "12:00:00" in item["dt_txt"]]
            df_weather = pd.DataFrame([{"Date": item["dt_txt"][:10], "Temp (°C)": item["main"]["temp"], "Ciel": item["weather"]["description"].capitalize(), "Nébulosité (%)": item["clouds"]["all"]} for item in daily_forecast])
            st.dataframe(df_weather)
        else: st.error(f"Erreur API météo: {weather_data['message']}")
    except requests.exceptions.RequestException as e: st.error(f"Erreur de connexion météo: {e}")


# --- TAB 5 : EXPORTS ---
with tab5:
    st.subheader("📋 Coordonnées pour votre monture")
    st.code(f"TARGET: {target_name}\nRA: {coord.ra.to_string(unit=u.hour)}\nDEC: {coord.dec.to_string(unit=u.deg)}")
    df = pd.DataFrame([{"name":target_name, "ra":coord.ra.deg, "dec":coord.dec.deg, "alt":round(altaz.alt.deg,1), "az":round(altaz.az.deg,1)}])
    st.download_button("Télécharger CSV", df.to_csv(index=False), file_name="astropepites_target.csv")

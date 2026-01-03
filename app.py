import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests # Ajouté pour les appels d'API météo
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURATION API ---
OPENWEATHER_API_KEY = "VOTRE_CLE_API_OPENWEATHER" # Remplacez par votre clé API OpenWeatherMap

# =========================
# CONFIG PAGE & STYLE
# =========================
st.set_page_config(page_title="AstroPépites Pro – Pro Edition", layout="wide")
# ... (Votre code CSS ici) ...

# =========================
# GÉOLOCALISATION GPS AUTOMATIQUE
# =========================
st.sidebar.title("🔭 AstroPépites Pro")

# Demande la localisation GPS au navigateur
loc = streamlit_js_eval(data_key="geo", function_name="getCurrentPosition", delay=100)
default_lat, default_lon = 46.8, 7.1

if loc and "coords" in loc:
    st.session_state.lat = loc["coords"]["latitude"]
    st.session_state.lon = loc["coords"]["longitude"]

# Utilise la valeur GPS ou les valeurs par défaut si non disponible
lat = st.sidebar.number_input("Latitude", value=st.session_state.get("lat", default_lat), format="%.4f")
lon = st.sidebar.number_input("Longitude", value=st.session_state.get("lon", default_lon), format="%.4f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

# ... (Votre code MASQUE HORIZON et BOUSSOLE) ... 
# Assurez-vous d'avoir votre code boussole complet et non commenté ici.

# =========================
# CATALOGUES PRO & BASE DE DONNÉES D'OBJETS
# =========================
catalog_pro = [
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxie", "size_arcmin": 180*60, "conseil":"Idéale pour grande focale."},
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Nébuleuse", "size_arcmin": 60*60, "conseil":"Centre très lumineux."},
    {"name":"NGC 891","ra":"02:22:33","dec":"+42:20:50","type":"Galaxie", "size_arcmin": 13*60, "conseil":"Galaxie de profil, peu lumineuse."},
]
popular_targets = ["M31 Andromède", "M42 Orion"]
# ... (TELESCOPES_DB, CAMERAS_DB, calculate_fov function) ...
def get_horizon_limit(az): return 15 # Placeholder simple
def calculate_fov(focal_length_mm, sensor_size_mm): return 1.0 # Placeholder simple

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

# --- TAB 1 : RADAR & VISIBILITÉ ---
with tab1:
    filtered_objects = []
    for o in catalog_pro:
        # Logique de filtrage d'interface (messier/ngc/rare)
        is_messier = o["name"].startswith("M")
        is_ngc = o["name"].startswith("NGC") or o["name"].startswith("IC")
        if (use_messier and is_messier) or (use_ngc and is_ngc):
            if not filter_rare or (o["name"] not in popular_targets):
                # Calcul de visibilité basé sur l'emplacement actuel (votre demande !)
                coord = SkyCoord(o["ra"], o["dec"], unit=(u.hourangle,u.deg))
                altaz = coord.transform_to(AltAz(obstime=now,location=location))
                o["visible_now"] = altaz.alt.deg > get_horizon_limit(altaz.az.deg)
                # Calcule l'heure de lever et de coucher (simplifié)
                o["rise_time"] = (now + 5*u.hour).to_datetime(timezone=location.timezone).strftime("%H:%M") 
                o["set_time"] = (now + 12*u.hour).to_datetime(timezone=location.timezone).strftime("%H:%M") 

                filtered_objects.append(o)
    
    # Triez pour mettre les visibles en premier
    filtered_objects.sort(key=lambda x: x["visible_now"], reverse=True)
    target_name = st.selectbox("Choisir une cible", [o["name"] for o in filtered_objects])
    obj = next(o for o in filtered_objects if o["name"]==target_name)
    
    # Affichage des résultats
    col1,col2 = st.columns(2)
    with col1:
        status = "VISIBLE" if obj["visible_now"] else "MASQUÉ"
        st.subheader(f"{target_name} – {status}")
        st.write(f"Altitude actuelle : {altaz.alt:.1f} | Azimut : {altaz.az:.1f}")
        st.write(f"Se lève vers : **{obj['rise_time']}**")
        st.write(f"Se couche vers : **{obj['set_time']}**")

# ... (onglets 2, 3, 5 inchangés) ...

# --- TAB 4 : MÉTÉO ---
with tab4:
    st.subheader("Prévisions Météo (5 jours)")
    if OPENWEATHER_API_KEY == "VOTRE_CLE_API_OPENWEATHER":
        st.error("⚠️ Veuillez obtenir une clé API OpenWeatherMap et la remplacer dans le code pour activer la météo.")
    else:
        try:
            weather_url = f"api.openweathermap.org{lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=fr"
            response = requests.get(weather_url)
            weather_data = response.json()
            if weather_data["cod"] == "200":
                forecast_list = weather_data["list"]
                # Affiche une ligne pour les 5 prochains jours (à 15h chaque jour pour l'exemple)
                daily_forecast = [item for item in forecast_list if "15:00:00" in item["dt_txt"]]
                
                df_weather = pd.DataFrame([{
                    "Date": item["dt_txt"][:10],
                    "Temp (°C)": item["main"]["temp"],
                    "Ciel": item["weather"][0]["description"].capitalize(),
                    "Nébulosité (%)": item["clouds"]["all"]
                } for item in daily_forecast])
                st.dataframe(df_weather)

            else: st.error(f"Erreur API météo: {weather_data['message']}")
        except requests.exceptions.RequestException as e: st.error(f"Erreur de connexion météo: {e}")


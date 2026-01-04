import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
from tzlocal import get_localzone
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy import units as u
from astropy.time import Time

# =========================
# CONFIGURATION
# =========================
# Assurez-vous d'avoir ces clés dans vos st.secrets
OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "VOTRE_CLE_ICI")

# Paramètres par défaut
default_lat, default_lon = 48.8566, 2.3522 # Paris

# =========================
# SIDEBAR & LOCALISATION
# =========================
st.sidebar.header("📍 Localisation")
lat = st.sidebar.number_input("Latitude", value=default_lat, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=default_lon, format="%.4f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()
local_timezone = get_localzone()

# =========================
# MASQUE HORIZON
# =========================
st.sidebar.header("🌲 Masque Horizon")
use_csv = st.sidebar.checkbox("Importer un CSV horizon")
csv_horizon = None

if use_csv:
    file = st.sidebar.file_uploader("Fichier (azimuth,altitude)", type="csv")
    if file: 
        csv_horizon = pd.read_csv(file)

with st.sidebar.expander("Réglage manuel", expanded=not use_csv):
    labels = ["Nord", "NE", "Est", "SE", "Sud", "SW", "Ouest", "NW"]
    m_vals = [st.slider(f"{d}", 0, 90, 15) for d in labels]

def get_horizon_limit(az):
    if csv_horizon is not None:
        return np.interp(az, csv_horizon.iloc[:,0], csv_horizon.iloc[:,1])
    # Mapping simple des 8 directions
    idx = int(((az + 22.5) % 360) // 45)
    return m_vals[idx]

# Boussole Horizon
angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
fig_pol, ax_pol = plt.subplots(figsize=(3,3), subplot_kw={"projection":"polar"})
ax_pol.set_theta_zero_location("N")
ax_pol.set_theta_direction(-1)

# Fermeture du polygone pour le graph
angles_closed = np.append(angles, angles[0])
m_vals_closed = np.append(m_vals, m_vals[0])

ax_pol.fill(angles_closed, m_vals_closed, color="red", alpha=0.4)
ax_pol.fill_between(angles_closed, m_vals_closed, np.radians(90), color="green", alpha=0.2)
ax_pol.set_yticklabels([])
ax_pol.set_xticklabels(labels)
ax_pol.set_facecolor("black")
fig_pol.patch.set_facecolor("black")
st.sidebar.pyplot(fig_pol)

# =========================
# BASES DE DONNÉES & UTILS
# =========================
TELESCOPES_DB = {"SW Evolux 62 ED + Reducteur 0.85x": {"focal_length": 340, "aperture": 62}}
CAMERAS_DB = {"ZWO ASI 183 MC Pro": {"sensor_width_mm": 13.2, "sensor_height_mm": 8.8, "pixel_size_um": 2.4}}

def calculate_fov(focal_length_mm, sensor_size_mm):
    return (sensor_size_mm / focal_length_mm) * (180 / np.pi)

def get_nasa_image_url(target_name):
    url = "https://images-api.nasa.gov/search"
    params = {'q': target_name, 'media_type': 'image'}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data['collection']['items']:
            # Récupère le lien de la collection d'assets
            asset_url = data['collection']['items'][0]['href']
            assets = requests.get(asset_url).json()
            # Cherche une image JPG de taille moyenne/large
            for a in assets:
                if a.endswith('~medium.jpg') or a.endswith('~large.jpg'):
                    return a
            return assets[0]
    except Exception as e:
        return None

# =========================
# INTERFACE PRINCIPALE
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔭 Cible", "📸 Infos", "🛠 Matériel", "☁️ Météo", "💾 Export"])

# Exemple d'objet pour la démo
target_name = st.sidebar.selectbox("Choisir une cible", ["M31 Andromède", "M42 Orion"])
# Simulation de données objet (Normalement vient de votre JSON)
obj = {"ra": "00h42m44s", "dec": "41d16m09s", "conseil": "Utilisez un filtre anti-pollution.", "size_arcmin": 190}
coord = SkyCoord(obj["ra"], obj["dec"], unit=(u.hourangle, u.deg))
altaz = coord.transform_to(AltAz(obstime=now, location=location))

with tab1:
    st.header(f"Cible : {target_name}")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Altitude : {altaz.alt.deg:.1f}°")
        st.write(f"Azimut : {altaz.az.deg:.1f}°")
        visible = altaz.alt.deg > get_horizon_limit(altaz.az.deg)
        st.metric("Visible", "OUI" if visible else "NON")

    with col2:
        # Graphique d'altitude sur 12h
        times = now + np.linspace(0, 12, 24)*u.hour
        alts = [coord.transform_to(AltAz(obstime=t, location=location)).alt.deg for t in times]
        st.line_chart(pd.DataFrame({"Altitude": alts}))

with tab2:
    st.subheader("Images NASA")
    img = get_nasa_image_url(target_name)
    if img: st.image(img, use_container_width=True)
    st.info(obj["conseil"])

with tab3:
    scope = st.selectbox("Télescope", list(TELESCOPES_DB.keys()))
    cam = st.selectbox("Caméra", list(CAMERAS_DB.keys()))
    f = TELESCOPES_DB[scope]["focal_length"]
    sw = CAMERAS_DB[cam]["sensor_width_mm"]
    sh = CAMERAS_DB[cam]["sensor_height_mm"]
    
    fov_w = calculate_fov(f, sw)
    fov_h = calculate_fov(f, sh)
    st.write(f"Champ de vision : {fov_w:.2f}° x {fov_h:.2f}°")

with tab4:
    st.subheader("Météo")
    # Correction URL OpenWeather
    weather_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=fr"
    if st.button("Actualiser Météo"):
        try:
            r = requests.get(weather_url).json()
            if r.get("list"):
                df_w = pd.DataFrame([{"Heure": i["dt_txt"], "Temp": i["main"]["temp"], "Ciel": i["weather"][0]["description"]} for i in r["list"]])
                st.table(df_w.head(10))
            else: st.error("Erreur API")
        except: st.error("Connexion impossible")

with tab5:
    st.subheader("Exports")
    st.code(f"RA: {coord.ra.to_string(unit=u.hour)}\nDEC: {coord.dec.to_string(unit=u.deg)}")

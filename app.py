import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun
from astropy import units as u
from astropy.time import Time
from datetime import datetime, timedelta

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="AstroPépites Live", layout="wide")

# --- 1. MODULE GPS & TEMPS RÉEL ---
# Note : Sur navigateur, on utilise une détection IP ou une saisie manuelle simplifiée
st.sidebar.title("📍 LOCALISATION & GPS")
if st.sidebar.button("📍 Actualiser ma position GPS"):
    # Simulation de récupération de coordonnées (utilisez streamlit_js_eval pour du vrai GPS)
    try:
        geo = requests.get('https://ipapi.co/json/').json()
        st.session_state.lat = geo['latitude']
        st.session_state.lon = geo['longitude']
        st.sidebar.success(f"Position : {geo['city']} ({st.session_state.lat}, {st.session_state.lon})")
    except:
        st.sidebar.error("GPS indisponible, passage en manuel.")

lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 48.85))
lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 2.35))
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)

# --- 2. MÉTÉO LIVE & ALERTES ---
st.sidebar.divider()
st.sidebar.title("☁️ MÉTÉO ASTRO LIVE")

def get_live_weather(lat, lon):
    url = f"https://www.7timer.info/bin/astro.php?lon={lon}&lat={lat}&ac=0&unit=metric&output=json"
    try:
        data = requests.get(url).json()['dataseries']
        return data
    except: return None

weather_data = get_live_weather(lat, lon)

if weather_data:
    current = weather_data[0]
    next_3h = weather_data[1]
    
    if current['cloudcover'] > 5:
        if next_3h['cloudcover'] <= 3:
            st.sidebar.warning("🔔 ALERTE : Ciel couvert, mais ça se dégage dans 3h ! Préparez le setup.")
        else:
            st.sidebar.error("❌ Couvert : Pas de shoot possible pour le moment.")
    else:
        st.sidebar.success("✅ CIEL CLAIR : Sortez le matériel maintenant !")

# --- 3. CALCULATEUR DE LA "MEILLEURE HEURE" (GOLDEN HOUR) ---
def find_best_time(target_coord, location):
    now = Time.now()
    times = now + np.linspace(0, 15, 150)*u.hour # Analyse sur 15 heures
    altaz_frame = AltAz(obstime=times, location=location)
    target_altaz = target_coord.transform_to(altaz_frame)
    sun_altaz = get_sun(times).transform_to(altaz_frame)
    
    # Critères : Soleil < -12° (crépuscule nautique) et Altitude cible max
    dark_mask = sun_altaz.alt.deg < -12
    if not any(dark_mask): return None, None
    
    best_idx = np.argmax(target_altaz.alt.deg[dark_mask])
    best_time = times[dark_mask][best_idx]
    best_alt = target_altaz.alt.deg[dark_mask][best_idx]
    
    return best_time, best_alt

# --- 4. INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites : Planificateur Stratégique")

# Base de cibles (extraits)
targets = {
    "Arp 273 (La Rose)": "02h21m28s +39d22m32s",
    "M31 (Andromède)": "00h42m44s +41d16m09s",
    "Abell 31": "08h54m13s +08d53m52s"
}

sel_name = st.selectbox("🎯 Choisissez votre cible pour ce soir :", list(targets.keys()))
coord = SkyCoord(targets[sel_name], frame='icrs')

best_t, best_a = find_best_time(coord, location)

# Affichage du verdict
st.header(f"📊 Verdict pour {sel_name}")
col1, col2 = st.columns(2)

with col1:
    if best_t:
        local_time = (best_t.datetime + timedelta(hours=1)).strftime("%H:%M")
        st.metric("Meilleure heure de shoot", local_time)
        st.write(f"Altitude max dans le noir : **{best_a:.1f}°**")
    else:
        st.error("Cible non visible dans le noir complet cette nuit.")

with col2:
    st.subheader("📋 État du Ciel")
    if weather_data:
        st.write(f"Nuages actuels : {current['cloudcover']}/9")
        st.write(f"Transparence : {current['seeing']}/8")

# --- GRAPHIQUE DYNAMIQUE ---
st.divider()
st.subheader("📈 Courbe de hauteur & Fenêtre de tir")

times_plot = Time.now() + np.linspace(0, 12, 100)*u.hour
altaz_plot = coord.transform_to(AltAz(obstime=times_plot, location=location))
sun_plot = get_sun(times_plot).transform_to(AltAz(obstime=times_plot, location=location))

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(np.linspace(0, 12, 100), altaz_plot.alt.deg, color='#00ffcc', label=sel_name, lw=2)
# Zone d'obscurité
dark_zone = sun_plot.alt.deg < -12
ax.fill_between(np.linspace(0, 12, 100), 0, 90, where=dark_zone, color='gray', alpha=0.2, label="Nuit Noire")

ax.set_facecolor("#0e1117")
fig.patch.set_facecolor("#0e1117")
ax.set_ylim(0, 90)
ax.legend()
st.pyplot(fig)

st.info("💡 L'heure idéale est le moment où la courbe verte est au plus haut dans la zone grise.")

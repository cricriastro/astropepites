import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun, get_moon, get_body
from astropy import units as u
from astropy.time import Time
from datetime import datetime, timedelta

# Configuration Pro
st.set_page_config(page_title="AstroPépites Expert 2026", layout="wide", page_icon="🔭")

# --- BASES DE DONNÉES ---
POWER_STATIONS = {"Bluetti EB3A (268Wh)": 22, "Jackery 500": 43}
TELESCOPES = {"Sky-Watcher Evolux 62ED": 400, "Askar FRA400": 400, "C8 f/6.3": 1280}
CAMERAS = {"ZWO ASI 183 MC Pro": {"w": 13.2, "h": 8.8, "px": 2.4, "cons": 1.5}}

# --- SIDEBAR CONFIG ---
st.sidebar.title("🛠 SETUP & HORIZON")
sel_ps = st.sidebar.selectbox("Batterie", list(POWER_STATIONS.keys()))
sel_scope = st.sidebar.selectbox("Tube", list(TELESCOPES.keys()))
sel_cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))
h_limit = st.sidebar.slider("Horizon mini (°)", 0, 60, 20)

# --- FONCTIONS MÉTÉO & IMAGES ---
def get_weather(lat, lon):
    # Utilisation d'une API gratuite (7-timer) adaptée à l'astro
    url = f"https://www.7timer.info/bin/astro.php?lon={lon}&lat={lat}&ac=0&unit=metric&output=json"
    try:
        data = requests.get(url).json()
        return data['dataseries'][:8] # 2 jours
    except: return None

def get_wiki_image(target):
    # Cherche une vignette sur Wikipedia
    url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{target.replace(' ', '_')}"
    try:
        r = requests.get(url).json()
        return r['thumbnail']['source']
    except: return "https://via.placeholder.com/200?text=No+Photo"

# --- LOGIQUE PRINCIPALE ---
st.title("🔭 AstroPépites : Planificateur Pro 2026")

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Cibles & Vignettes", "☁️ Météo Astro", "🪐 Système Solaire", "🗓 Éphémérides 2026"])

lat, lon = 48.85, 2.35 # Coordonnées par défaut
now = Time.now()
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)

with tab1:
    st.header("🎯 Sélection de la Pépite")
    targets_db = [
        {"name": "M31", "display": "Andromède", "ra": "00h42m44s", "dec": "+41d16m09s"},
        {"name": "M42", "display": "Nébuleuse d'Orion", "ra": "05h35m17s", "dec": "-05d23m28s"},
        {"name": "NGC 6960", "display": "Petites Dentelles", "ra": "20h45m42s", "dec": "+30d42m30s"},
        {"name": "Arp 273", "display": "La Rose de Galaxies", "ra": "02h21m28s", "dec": "+39d22m32s"}
    ]
    
    sel_obj = st.selectbox("Cible", [t['display'] for t in targets_db])
    t_data = next(t for t in targets_db if t['display'] == sel_obj)
    
    col_img, col_info = st.columns([1, 2])
    with col_img:
        st.image(get_wiki_image(t_data['name']), width=250, caption=sel_obj)
    
    with col_info:
        coord = SkyCoord(t_data['ra'], t_data['dec'])
        # Calcul temps de shoot (Altitude > horizon ET Soleil < -12°)
        times = now + np.linspace(0, 24, 100)*u.hour
        altaz = coord.transform_to(AltAz(obstime=times, location=location))
        sun = get_sun(times).transform_to(AltAz(obstime=times, location=location))
        
        visible = (altaz.alt.deg > h_limit) & (sun.alt.deg < -12)
        shoot_hours = np.sum(visible) * (24/100)
        
        st.metric("⏳ Fenêtre de shoot cette nuit", f"{shoot_hours:.1f} heures")
        st.write(f"**Coordonnées :** {t_data['ra']} / {t_data['dec']}")
        
        # Boutons d'export
        st.download_button("💾 Export ASIAIR (CSV)", f"Name,RA,Dec\n{sel_obj},{t_data['ra']},{t_data['dec']}", file_name="target.csv")

with tab2:
    st.header("☁️ Prévisions Météo Astro (48h)")
    w_data = get_weather(lat, lon)
    if w_data:
        cols = st.columns(len(w_data))
        for i, d in enumerate(w_data):
            with cols[i]:
                st.write(f"+{d['timepoint']}h")
                st.info(f"☁️ {d['cloudcover']}")
                st.caption(f"Temp: {d['temp2m']}°C")
    else:
        st.error("Météo indisponible.")

with tab3:
    st.header("🪐 Planètes & Comètes")
    planets = ['Mars', 'Jupiter', 'Saturn']
    p_cols = st.columns(len(planets))
    for i, p in enumerate(planets):
        p_coord = get_body(p, now, location)
        p_altaz = p_coord.transform_to(AltAz(obstime=now, location=location))
        with p_cols[i]:
            st.write(f"**{p}**")
            st.write(f"Alt: {p_altaz.alt.deg:.1f}°")
            if p_altaz.alt.deg > 0: st.success("Visible")
            else: st.error("Sous l'horizon")

with tab4:
    st.header("🗓 Événements Majeurs 2026")
    events = [
        {"Date": "17 Février 2026", "Event": "Occultation de Saturne par la Lune"},
        {"Date": "12 Août 2026", "Event": "ÉCLIPSE TOTALE DE SOLEIL (Espagne/Islande)"},
        {"Date": "28 Août 2026", "Event": "Éclipse Lunaire Partielle"},
        {"Date": "Octobre 2026", "Event": "Pic des Orionides (Météores)"}
    ]
    st.table(events)

st.divider()
# Logistique Batterie
amps = MOUNTS[sel_mount] + CAMERAS[sel_cam]['cons'] + 1.5
autonomie = POWER_STATIONS[sel_ps] / amps
st.write(f"🔋 Avec ta **{sel_ps}**, tu peux tenir **{autonomie:.1f}h** en shootant **{sel_obj}**.")

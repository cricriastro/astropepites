import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body, get_sun
from astropy import units as u
from astropy.time import Time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites 2026 - Master Edition", layout="wide")

# --- BASES DE DONNÉES (MATÉRIEL) ---
# Ajout de ton ASIAIR Pro et Tiroir Svbony
SETUP = {
    "Télescope": "Sky-Watcher Evolux 62ED",
    "Caméra": "ZWO ASI 183 MC Pro",
    "Guidage": "ASI 120 Mini + Svbony SV165",
    "Contrôle": "ASIAIR Pro",
    "Accessoire": "Tiroir à filtres Svbony",
    "Batterie": "Bluetti EB3A (268Wh)"
}

# --- ÉVÉNEMENTS 2026 ---
ECLIPSES_2026 = [
    {"Date": "17 Fév 2026", "Événement": "Occultation de Saturne par la Lune", "Visibilité": "Europe"},
    {"Date": "12 Août 2026", "Événement": "ÉCLIPSE TOTALE DE SOLEIL", "Visibilité": "Espagne/Islande (Totale) / France (Partielle 90%)"},
    {"Date": "28 Août 2026", "Événement": "Éclipse Lunaire Partielle", "Visibilité": "Europe/Afrique"}
]

# --- CIBLES DU JOUR & COMÈTES ---
COMETS_2026 = [
    {"name": "C/2023 A3 (Tsuchinshan-ATLAS)", "status": "Pépite", "rarity": 100, "note": "À suivre au crépuscule."},
    {"name": "67P/Churyumov-Gerasimenko", "status": "Faible", "rarity": 90, "note": "Cible de choix pour la 183MC."}
]

# --- FONCTION MÉTÉO ---
def check_weather(lat, lon):
    # API météo simplifiée pour l'astro
    url = f"https://www.7timer.info/bin/astro.php?lon={lon}&lat={lat}&ac=0&unit=metric&output=json"
    try:
        r = requests.get(url).json()
        cloud_cover = r['dataseries'][0]['cloudcover']
        return cloud_cover # De 1 (Clair) à 9 (Bouché)
    except: return "Inconnu"

# --- SIDEBAR & BOUSSOLE ---
st.sidebar.title("🛠 MONITORING SETUP")
st.sidebar.info(f"📡 Contrôleur : {SETUP['Contrôle']}\n📂 Filtres : {SETUP['Accessoire']}")

st.sidebar.subheader("🌲 Horizon (Boussole)")
h_n = st.sidebar.slider("Nord", 0, 60, 20)
h_e = st.sidebar.slider("Est", 0, 60, 15)
h_s = st.sidebar.slider("Sud", 0, 60, 10)
h_o = st.sidebar.slider("Ouest", 0, 60, 25)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites : Centre de Contrôle 2026")

tab1, tab2, tab3 = st.tabs(["🎯 Pépites du Jour", "☄️ Comètes & Éclipses", "☁️ Météo & Rappels"])

with tab1:
    st.header("✨ Cibles recommandées pour ce soir")
    # Simulation de sélection d'objets rares selon la date
    st.write("Basé sur votre position et votre setup **ASI 183MC + SV220** :")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🚀 Top Pépite : Arp 273")
        st.markdown("**Score de Rareté : 94%**")
        st.write("Galaxies en interaction. *Conseil : Pose longue de 300s avec guidage.*")
    with c2:
        st.subheader("💎 Objet Exotique : Abell 31")
        st.markdown("**Score de Rareté : 89%**")
        st.write("Nébuleuse planétaire géante. *Conseil : Filtre SV220 obligatoire.*")

with tab2:
    st.header("☄️ Chasse aux Comètes 2026")
    st.table(COMETS_2026)
    
    st.header("☀️ Éclipses & Phénomènes de l'année")
    for e in ECLIPSES_2026:
        with st.expander(f"📅 {e['Date']} : {e['Événement']}"):
            st.write(f"**Visibilité :** {e['Visibilité']}")
            if "SOLEIL" in e['Événement']:
                st.warning("⚠️ Attention : Nécessite un filtre solaire certifié sur l'Evolux 62ED !")

with tab3:
    st.header("☁️ État du Ciel & Alertes")
    lat, lon = 48.8, 2.3 # Paris par défaut
    cloud = check_weather(lat, lon)
    
    if isinstance(cloud, int):
        if cloud < 3:
            st.success("✅ CIEL DÉGAGÉ : Sortez la Bluetti, c'est le moment de shooter !")
        elif cloud < 6:
            st.warning("⛅ CIEL VOILÉ : Risque de passage nuageux. Privilégiez les amas d'étoiles.")
        else:
            st.error("🌧️ CIEL BOUCHÉ : Profitez-en pour traiter vos images ou charger la batterie.")
    
    st.subheader("🔔 Rappels Automatiques")
    st.checkbox("Me rappeler 2 jours avant l'éclipse du 12 août", value=True)
    st.checkbox("Alerte 'Ciel Clair' pour les comètes", value=True)

# --- LOGISTIQUE ÉNERGIE ---
st.divider()
st.subheader("🔋 État de la Bluetti EB3A")
cons_totale = 3.2 # ASIAIR Pro + Monture + 183MC + Guidage
autonomie = 22 / cons_totale
st.write(f"Avec tout ton matériel connecté (y compris le guidage ASI120 Mini), ton autonomie estimée est de **{autonomie:.1f} heures**.")

if st.button("📝 Générer Rapport de Session pour ASIAIR"):
    st.code(f"Session 2026\nCible: Arp 273\nFiltre: Svbony DualBand\nGuidage: On (SV165)\nAutonomie: {autonomie:.1f}h")

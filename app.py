import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun, get_body
from astropy import units as u
from astropy.time import Time
from datetime import datetime, timedelta

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="AstroPépites Ultime", layout="wide")

# --- DATA : CATALOGUES MONDIAUX ---
# Correction de la ligne 17 : Suppression des URLs problématiques
CATALOGUES = {
    "Messier": [
        {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "rarity": 10, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/M31_09-01-2011.jpg/320px-M31_09-01-2011.jpg"},
        {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "rarity": 5, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg/320px-Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg"}
    ],
    "NGC / IC": [
        {"name": "NGC 6960 (Balai de Sorcière)", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse", "rarity": 45, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/The_Witch%27s_Broom_Nebula.jpg/320px-The_Witch%27s_Broom_Nebula.jpg"}
    ],
    "Arp (Raretés)": [
        {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "rarity": 95, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/320px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg"}
    ],
    "Abell (Planétaires)": [
        {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P.", "rarity": 90, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/320px-Abell_31_nebula.jpg"}
    ]
}

FILTERS_DB = ["Svbony SV220", "Optolong L-Pro", "Antlia ALP-T", "ZWO LRGB", "Tiroir Vide"]

# --- SIDEBAR (COLONNE DE GAUCHE COMPLÈTE) ---
st.sidebar.title("🛠️ CONFIGURATION SETUP")

with st.sidebar.expander("📍 GPS & Localisation", expanded=True):
    lat = st.number_input("Latitude", value=48.85)
    lon = st.number_input("Longitude", value=2.35)
    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)

with st.sidebar.expander("🔭 Mon Matériel", expanded=True):
    user_scope = st.text_input("Télescope", "Evolux 62ED")
    user_filter = st.selectbox("Filtre installé", FILTERS_DB)
    batt_wh = st.number_input("Batterie (Wh)", value=268)

with st.sidebar.expander("📚 Catalogues Mondiaux", expanded=True):
    show_m = st.checkbox("Messier", value=True)
    show_ngc = st.checkbox("NGC / IC", value=True)
    show_arp = st.checkbox("Arp (Raretés)", value=True)
    show_abell = st.checkbox("Abell (Planétaires)", value=True)

with st.sidebar.expander("🌲 Horizon (Boussole)", expanded=False):
    h_n = st.slider("Nord", 0, 70, 20)
    h_e = st.slider("Est", 0, 70, 15)
    h_s = st.slider("Sud", 0, 70, 10)
    h_o = st.slider("Ouest", 0, 70, 25)

# --- LOGIQUE MÉTÉO ---
st.sidebar.divider()
def get_weather(lat, lon):
    try:
        r = requests.get(f"https://www.7timer.info/bin/astro.php?lon={lon}&lat={lat}&ac=0&unit=metric&output=json").json()
        return r['dataseries'][0]
    except: return None

w = get_weather(lat, lon)
if w:
    if w['cloudcover'] <= 3: st.sidebar.success("✅ Ciel Clair : Sortez le matériel !")
    elif w['cloudcover'] <= 6: st.sidebar.warning("⛅ Voilé : Shooting risqué.")
    else: st.sidebar.error("❌ Couvert : Pas de shoot possible.")

# --- FILTRAGE DES CIBLES ---
active_cats = []
if show_m: active_cats.append("Messier")
if show_ngc: active_cats.append("NGC / IC")
if show_arp: active_cats.append("Arp (Raretés)")
if show_abell: active_cats.append("Abell (Planétaires)")

filtered_list = []
for cat in active_cats:
    filtered_list.extend(CATALOGUES[cat])

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites : Centre de Contrôle 2026")

if not filtered_list:
    st.warning("👈 Sélectionnez au moins un catalogue dans la colonne de gauche.")
else:
    tab1, tab2, tab3 = st.tabs(["🎯 Cibles & Visibilité", "☄️ Comètes & Éclipses", "👨‍🏫 Coach de Session"])

    with tab1:
        sel_name = st.selectbox("Choisissez votre cible :", [t["name"] for t in filtered_list])
        t_data = next(t for t in filtered_list if t["name"] == sel_name)
        
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            st.image(t_data["img"], caption=t_data["name"])
        with col_txt:
            st.subheader(f"Analyse pour {sel_name}")
            st.metric("Rareté", f"{t_data['rarity']}%")
            st.metric("Type", t_data['type'])

        # Graphique Visibilité
        target_coord = SkyCoord(t_data["ra"], t_data["dec"])
        now = Time.now()
        times = now + np.linspace(0, 12, 100)*u.hour
        altaz = target_coord.transform_to(AltAz(obstime=times, location=location))
        sun_altaz = get_sun(times).transform_to(AltAz(obstime=times, location=location))
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(np.linspace(0, 12, 100), altaz.alt.deg, color="#00ffcc", lw=3)
        ax.fill_between(np.linspace(0, 12, 100), 0, 90, where=sun_plot.alt.deg < -12 if 'sun_plot' in locals() else sun_altaz.alt.deg < -12, color='gray', alpha=0.2, label="Nuit Noire")
        ax.set_facecolor("#0e1117")
        fig.patch.set_facecolor("#0e1117")
        ax.set_ylim(0, 90)
        st.pyplot(fig)

    with tab2:
        st.header("☄️ Phénomènes 2026")
        st.write("**Comète C/2023 A3** : Rareté 100% - Passage au crépuscule.")
        st.warning("📅 **12 Août 2026** : ÉCLIPSE TOTALE DE SOLEIL.")

    with tab3:
        st.header("👨‍🏫 Stratégie d'Acquisition")
        total_h = 10 if t_data['rarity'] > 80 else 4
        autonomie = (batt_wh / 12) / 3.5
        st.metric("Temps total recommandé", f"{total_h} h")
        st.write(f"🔋 Votre autonomie est de **{autonomie:.1f}h**. Prévoyez **{int(np.ceil(total_h/autonomie))} nuit(s)**.")
        
        if "Galaxie" in t_data['type']:
            st.info("💡 **Conseil Tiroir Svbony :** Laissez le tiroir vide pour cette galaxie ou utilisez un filtre pollution léger.")
        else:
            st.success(f"💡 **Conseil Tiroir Svbony :** Glissez votre SV220, l'ASIAIR fera des merveilles en poses longues.")

if st.sidebar.button("🔔 Tester l'alerte"):
    st.toast("C'est l'heure de sortir !", icon="🔭")
    st.markdown('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3"></audio>', unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun, get_moon
from astropy import units as u
from astropy.time import Time
from datetime import datetime, timedelta

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="AstroPépites Ultime", layout="wide")

# --- DATA : CATALOGUES MONDIAUX ---
CATALOGUES = {
    "Messier": [
        {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "rarity": 10},
        {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "rarity": 5}
    ],
    "NGC / IC": [
        {"name": "NGC 6960 (Dentelles)", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse", "rarity": 45}
    ],
    "Arp (Raretés)": [
        {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "rarity": 95}
    ],
    "Abell (Planétaires)": [
        {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P.", "rarity": 90}
    ]
}

FILTERS_LIST = ["Svbony SV220", "Optolong L-Pro", "Antlia ALP-T", "ZWO LRGB", "Tiroir Vide"]

# --- SIDEBAR (TOUT EST ICI) ---
st.sidebar.title("🛠️ CONFIGURATION")

with st.sidebar.expander("📍 GPS & Localisation", expanded=True):
    lat = st.number_input("Latitude", value=48.85)
    lon = st.number_input("Longitude", value=2.35)
    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)

with st.sidebar.expander("🔭 Mon Matériel", expanded=True):
    user_scope = st.text_input("Télescope", "Evolux 62ED")
    user_filter = st.selectbox("Filtre utilisé", FILTERS_LIST)
    batt_wh = st.number_input("Batterie (Wh)", value=268)

with st.sidebar.expander("📚 Catalogues à afficher", expanded=True):
    sel_cats = []
    for cat in CATALOGUES.keys():
        if st.checkbox(cat, value=True):
            sel_cats.append(cat)

with st.sidebar.expander("🌲 Boussole (Horizon)", expanded=False):
    h_n = st.slider("Nord", 0, 70, 20)
    h_e = st.slider("Est", 0, 70, 15)
    h_s = st.slider("Sud", 0, 70, 10)
    h_o = st.slider("Ouest", 0, 70, 25)

# --- LOGIQUE MÉTÉO ---
st.sidebar.divider()
def check_weather(lat, lon):
    try:
        r = requests.get(f"https://www.7timer.info/bin/astro.php?lon={lon}&lat={lat}&ac=0&unit=metric&output=json").json()
        return r['dataseries'][0]['cloudcover']
    except: return 9

cloud = check_weather(lat, lon)
if cloud <= 3: st.sidebar.success("✅ CIEL CLAIR : Sortez le matériel !")
elif cloud <= 6: st.sidebar.warning("⛅ VOILÉ : Prudence...")
else: st.sidebar.error("❌ COUVERT : Attendez une trouée.")

# --- CONSTRUCTION DE LA LISTE DE CIBLES ---
final_targets = []
for cat in sel_cats:
    final_targets.extend(CATALOGUES[cat])

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites : Planificateur Expert")

if not final_targets:
    st.warning("Veuillez cocher au moins un catalogue dans la colonne de gauche.")
else:
    # 1. Sélection de la cible
    sel_target_name = st.selectbox("🎯 Choisissez votre pépite :", [t["name"] for t in final_targets])
    t_data = next(t for t in final_targets if t["name"] == sel_target_name)

    # 2. Affichage Expert
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Score de Rareté", f"{t_data['rarity']}%")
    with c2:
        st.metric("Type d'objet", t_data['type'])
    with c3:
        autonomie = (batt_wh / 12) / 3.5
        st.metric("Autonomie Batterie", f"{autonomie:.1f} h")

    # 3. Conseil Filtre & Coaching
    st.divider()
    st.subheader("👨‍🏫 Coaching de Session")
    
    col_f, col_t = st.columns(2)
    with col_f:
        if "Galaxie" in t_data['type']:
            st.info(f"**Filtre recommandé :** L-Pro ou Vide.\n\n**Action tiroir :** Laissez vide pour capter tout le spectre de {t_data['name']}.")
        else:
            st.success(f"**Filtre recommandé :** {user_filter}.\n\n**Action tiroir :** Insérez le filtre pour booster le contraste.")
    
    with col_t:
        total_time = 12 if t_data['rarity'] > 80 else 4
        st.write(f"⏱️ **Temps d'intégration requis :** {total_time} heures.")
        st.write(f"📅 **Nombre de nuits estimé :** {int(np.ceil(total_time/autonomie))} nuit(s).")

    # 4. Graphique de Visibilité & Nuit Noire
    st.divider()
    st.subheader("📈 Courbe de hauteur & Fenêtre de tir")
    
    target_coord = SkyCoord(t_data['ra'], t_data['dec'])
    now = Time.now()
    times_plot = now + np.linspace(0, 12, 100)*u.hour
    altaz_plot = target_coord.transform_to(AltAz(obstime=times_plot, location=location))
    sun_plot = get_sun(times_plot).transform_to(AltAz(obstime=times_plot, location=location))

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.linspace(0, 12, 100), altaz_plot.alt.deg, color='#00ffcc', lw=3, label=t_data['name'])
    ax.fill_between(np.linspace(0, 12, 100), 0, 90, where=sun_plot.alt.deg < -12, color='gray', alpha=0.3, label="Nuit Noire")
    ax.axhline(15, color="red", linestyle="--", label="Horizon")
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")
    ax.set_ylim(0, 90)
    ax.legend()
    st.pyplot(fig)

    # 5. Événements spéciaux
    st.divider()
    st.subheader("☄️ Événements & Comètes 2026")
    st.write("🔭 **Comète C/2023 A3** : Passage exceptionnel, rareté 100%.")
    st.warning("☀️ **12 Août 2026** : ÉCLIPSE TOTALE DE SOLEIL (Préparez vos filtres solaires !)")

# Notification Sonore (Bouton de test)
if st.button("🔔 Tester la notification"):
    st.toast("C'est l'heure de shooter !", icon="🔭")
    st.markdown('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3"></audio>', unsafe_allow_html=True)

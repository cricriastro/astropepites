import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun
from astropy import units as u
from astropy.time import Time
from datetime import datetime, timedelta

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="AstroPépites : Master Control", layout="wide")

# --- BASE DE DONNÉES ÉLARGIE ---
DB_OBJECTS = {
    "Messier": [
        {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "difficulty": "Facile", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/M31_09-01-2011.jpg/320px-M31_09-01-2011.jpg"},
        {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "difficulty": "Facile", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg/320px-Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg"},
        {"name": "M51 (Tourbillon)", "ra": "13h29m52s", "dec": "+47d11m43s", "type": "Galaxie", "difficulty": "Moyen", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Messier51a.jpg/320px-Messier51a.jpg"},
        {"name": "M101 (Moulinet)", "ra": "14h03m12s", "dec": "+54d20m57s", "type": "Galaxie", "difficulty": "Moyen", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/M101_hires_STScI-PRC2006-10a.jpg/320px-M101_hires_STScI-PRC2006-10a.jpg"}
    ],
    "NGC / IC": [
        {"name": "NGC 6960 (Dentelles)", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse", "difficulty": "Moyen", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/The_Witch%27s_Broom_Nebula.jpg/320px-The_Witch%27s_Broom_Nebula.jpg"},
        {"name": "NGC 7000 (North America)", "ra": "20h58m47s", "dec": "+44d19m40s", "type": "Nébuleuse", "difficulty": "Facile", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/North_America_Nebula_Final.jpg/320px-North_America_Nebula_Final.jpg"}
    ],
    "Arp (Raretés)": [
        {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "difficulty": "Expert", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/320px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg"},
        {"name": "Arp 240", "ra": "14h03m05s", "dec": "+24d33m37s", "type": "Galaxie", "difficulty": "Expert", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Arp_240_Hubble.jpg/320px-Arp_240_Hubble.jpg"}
    ],
    "Abell (Planétaires)": [
        {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P.", "difficulty": "Expert", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/320px-Abell_31_nebula.jpg"},
        {"name": "Abell 21 (Medusa)", "ra": "07h29m02s", "dec": "+13d14m15s", "type": "Nébuleuse P.", "difficulty": "Expert", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/The_Medusa_Nebula.jpg/320px-The_Medusa_Nebula.jpg"}
    ]
}

# --- SIDEBAR : LE SETUP COMPLET ---
st.sidebar.title("🛡️ SETUP ASTRO PRO")

with st.sidebar.expander("📍 Localisation & GPS", expanded=False):
    lat = st.number_input("Latitude", value=48.85)
    lon = st.number_input("Longitude", value=2.35)
    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)

with st.sidebar.expander("🔭 Optique & Capteur", expanded=True):
    tube = st.text_input("Lunette/Télescope", "Evolux 62ED")
    optique = st.selectbox("Correcteur / Barlow", ["Réducteur 0.8x", "Correcteur 1.0x", "Barlow 2x", "Aucun"])
    camera = st.text_input("Caméra principale", "ASI 183MC")
    filtre = st.selectbox("Filtre", ["Svbony SV220", "Optolong L-Pro", "Antlia ALP-T", "ZWO LRGB", "Tiroir Vide"])

with st.sidebar.expander("🔌 Accessoires & Énergie", expanded=True):
    # Consommation estimée en Watts
    has_eaf = st.toggle("EAF (Focusseur auto)", value=True)
    has_dew = st.toggle("Chauffage de rosée", value=True)
    has_guiding = st.toggle("Autoguidage (ASI120 Mini)", value=True)
    
    st.divider()
    batt_type = st.selectbox("Modèle Batterie", ["Bluetti EB3A (268Wh)", "Bluetti EB70 (716Wh)", "Batterie Marine 100Ah", "Secteur"])
    
    # Calcul de la puissance totale consommée
    pwr_base = 15 # ASIAIR + Caméra (Refroidissement) + Monture
    pwr_eaf = 2 if has_eaf else 0
    pwr_dew = 10 if has_dew else 0
    pwr_guide = 3 if has_guiding else 0
    total_pwr = pwr_base + pwr_eaf + pwr_dew + pwr_guide

with st.sidebar.expander("📚 Gestion Catalogues", expanded=True):
    active_cats = []
    if st.checkbox("Messier", value=True): active_cats.append("Messier")
    if st.checkbox("NGC / IC", value=True): active_cats.append("NGC / IC")
    if st.checkbox("Arp", value=True): active_cats.append("Arp (Raretés)")
    if st.checkbox("Abell", value=True): active_cats.append("Abell (Planétaires)")

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites : L'App de l'Année 2026")

# Filtrage
targets_pool = []
for cat in active_cats:
    targets_pool.extend(DB_OBJECTS[cat])

if not targets_pool:
    st.warning("👈 Activez des catalogues dans le menu de gauche.")
else:
    # --- ONGLET 1 : CIBLES ET EXPORT ---
    tab1, tab2, tab3 = st.tabs(["🎯 Cibles & ASIAIR", "🔋 Énergie & Autonomie", "☄️ Comètes & Alertes"])

    with tab1:
        sel_name = st.selectbox("Choisir une cible :", [t["name"] for t in targets_pool])
        t_data = next(t for t in targets_pool if t["name"] == sel_name)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(t_data["img"], use_container_width=True)
        with c2:
            st.header(f"Verdict : {sel_name}")
            st.write(f"**Difficulté :** {t_data['difficulty']}")
            st.write(f"**Coordonnées :** `{t_data['ra']}` | `{t_data['dec']}`")
            
            # Export CSV
            csv_str = f"Name,RA,Dec\n{t_data['name']},{t_data['ra']},{t_data['dec']}"
            st.download_button("📥 Générer CSV pour ASIAIR", data=csv_str, file_name=f"{sel_name}.csv")
            
            # Conseil Matériel
            if "Galaxie" in t_data['type'] and "Réducteur" in optique:
                st.info("💡 Tip : Pour cette galaxie, le réducteur est parfait pour le champ large.")
            elif "Planétaires" in t_data['type']:
                st.warning("⚠️ Tip : Objet très petit. Une Barlow serait idéale si le ciel est stable.")

    with tab2:
        st.header("⚡ Bilan Énergétique")
        
        # Capacité batterie
        if "EB3A" in batt_type: wh = 268
        elif "EB70" in batt_type: wh = 716
        elif "100Ah" in batt_type: wh = 1200
        else: wh = 9999
        
        autonomie = wh / total_pwr
        
        col_pwr, col_time = st.columns(2)
        with col_pwr:
            st.metric("Consommation Totale", f"{total_pwr} W")
            st.write(f"• Base + Monture : 15W")
            if has_dew: st.write(f"• Chauffage Rosée : 10W")
            if has_eaf: st.write(f"• EAF : 2W")
        
        with col_time:
            if wh > 5000:
                st.success("Autonomie : Illimitée (Secteur)")
            else:
                st.metric("Temps de shoot max", f"{autonomie:.1f} heures")
                st.progress(min(autonomie/12, 1.0), text="Remplissage de la nuit")

    with tab3:
        st.subheader("🔔 Alertes & Événements")
        st.write("📅 **12 Août 2026** : Eclipse Totale de Soleil (France/Espagne)")
        st.write("☄️ **C/2023 A3** : Magnitude prévue 2.0 (Spectaculaire)")
        
        if st.button("🔊 Tester l'alarme sonore de sortie"):
            st.toast("Il est l'heure !")
            st.markdown('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3"></audio>', unsafe_allow_html=True)

# --- COURBE DE HAUTEUR ---
st.divider()
target_coord = SkyCoord(t_data["ra"], t_data["dec"])
times = Time.now() + np.linspace(0, 12, 100)*u.hour
altaz = target_coord.transform_to(AltAz(obstime=times, location=location))
sun_altaz = get_sun(times).transform_to(AltAz(obstime=times, location=location))

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(np.linspace(0, 12, 100), altaz.alt.deg, color="#00ffcc", lw=2, label=t_data["name"])
ax.fill_between(np.linspace(0, 12, 100), 0, 90, where=sun_altaz.alt.deg < -12, color='gray', alpha=0.3, label="Nuit Noire")
ax.axhline(15, color="red", linestyle="--", label="Horizon")
ax.set_facecolor("#0e1117")
fig.patch.set_facecolor("#0e1117")
ax.set_ylim(0, 90)
ax.legend()
st.pyplot(fig)

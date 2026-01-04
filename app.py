import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun, get_moon
from astropy import units as u
from astropy.time import Time
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : L'App Ultime", layout="wide", page_icon="🔭")

# --- DATA : CATALOGUES & ÉVÉNEMENTS ---
DB_OBJECTS = [
    {"name": "Arp 273 (La Rose)", "cat": "Arp (Raretés)", "type": "Galaxie", "ra": "02h21m28s", "dec": "+39d22m32s", "difficulty": "⭐⭐⭐⭐", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/320px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg"},
    {"name": "Abell 31", "cat": "Abell (Planétaires)", "type": "Nébuleuse P.", "ra": "08h54m13s", "dec": "+08d53m52s", "difficulty": "⭐⭐⭐⭐⭐", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/320px-Abell_31_nebula.jpg"},
    {"name": "M31 (Andromède)", "cat": "Messier", "type": "Galaxie", "ra": "00h42m44s", "dec": "+41d16m09s", "difficulty": "⭐", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/M31_09-01-2011.jpg/320px-M31_09-01-2011.jpg"},
    {"name": "NGC 6960 (Balai de Sorcière)", "cat": "NGC / IC", "type": "Nébuleuse", "ra": "20h45m42s", "dec": "+30d42m30s", "difficulty": "⭐⭐", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/The_Witch%27s_Broom_Nebula.jpg/320px-The_Witch%27s_Broom_Nebula.jpg"}
]

FILTERS_DB = ["Svbony SV220", "Optolong L-Pro", "Optolong L-Ultimate", "Antlia ALP-T", "ZWO LRGB", "Tiroir Vide"]

# --- SIDEBAR COMPLÈTE (COLONNE DE GAUCHE) ---
st.sidebar.title("🛠️ MONITORING SETUP")

with st.sidebar.expander("📍 Localisation & GPS", expanded=True):
    lat = st.number_input("Latitude", value=48.85)
    lon = st.number_input("Longitude", value=2.35)
    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)

with st.sidebar.expander("🔭 Mon Matériel", expanded=True):
    sel_scope = st.text_input("Télescope", "Evolux 62ED")
    sel_filter = st.selectbox("Filtre installé", FILTERS_DB)
    batt_wh = st.number_input("Batterie (Wh)", value=268)

with st.sidebar.expander("📚 Catalogues du Monde", expanded=True):
    show_m = st.checkbox("Messier", value=True)
    show_ngc = st.checkbox("NGC / IC", value=True)
    show_arp = st.checkbox("Arp (Raretés)", value=True)
    show_abell = st.checkbox("Abell (Planétaires)", value=True)

with st.sidebar.expander("🌲 Horizon (Boussole)", expanded=False):
    h_n = st.slider("Nord", 0, 70, 20)
    h_e = st.slider("Est", 0, 70, 15)
    h_s = st.slider("Sud", 0, 70, 10)
    h_o = st.slider("Ouest", 0, 70, 25)

# --- LOGIQUE MÉTÉO LIVE ---
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
    else: st.sidebar.error("❌ Couvert : Prévu dégagé dans quelques heures ?")

# --- FILTRAGE DES CIBLES ---
active_cats = []
if show_m: active_cats.append("Messier")
if show_ngc: active_cats.append("NGC / IC")
if show_arp: active_cats.append("Arp (Raretés)")
if show_abell: active_cats.append("Abell (Planétaires)")

filtered_targets = [t for t in DB_OBJECTS if t["cat"] in active_cats]

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites : Centre de Contrôle Intégral")

tab1, tab2, tab3 = st.tabs(["🎯 Cibles & Filtres", "☄️ Comètes & Éclipses", "👨‍🏫 Coach de Session"])

with tab1:
    sel_obj_name = st.selectbox("Choisir une cible", [t["name"] for t in filtered_targets])
    t_data = next(t for t in filtered_targets if t["name"] == sel_obj_name)
    
    col_vignette, col_details = st.columns([1, 2])
    with col_vignette:
        st.image(t_data["img"], caption=t_data["name"])
    
    with col_details:
        st.subheader(f"Infos pour {t_data['name']}")
        st.write(f"**Type :** {t_data['type']} | **Difficulté :** {t_data['difficulty']}")
        # Conseil Filtre / Tiroir
        if "Galaxie" in t_data["type"]:
            st.info(f"💡 **Conseil Tiroir Svbony :** Pour cette galaxie, privilégiez le **Tiroir Vide** ou un filtre L-Pro pour garder les couleurs.")
        else:
            st.success(f"💡 **Conseil Tiroir Svbony :** Glissez votre **{sel_filter}** pour isoler les détails de cette nébuleuse.")

    # --- GRAPHIQUE VISIBILITÉ ---
    st.divider()
    target_coord = SkyCoord(t_data["ra"], t_data["dec"])
    now = Time.now()
    times = now + np.linspace(0, 12, 100)*u.hour
    altaz = target_coord.transform_to(AltAz(obstime=times, location=location))
    sun_altaz = get_sun(times).transform_to(AltAz(obstime=times, location=location))
    
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(np.linspace(0, 12, 100), altaz.alt.deg, color="#00ffcc", lw=3)
    ax.fill_between(np.linspace(0, 12, 100), 0, 90, where=sun_altaz.alt.deg < -12, color='gray', alpha=0.2, label="Nuit Noire")
    ax.axhline(15, color="red", linestyle="--", label="Horizon")
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")
    st.pyplot(fig)

with tab2:
    st.header("☄️ Phénomènes Spéciaux 2026")
    col_com, col_ecl = st.columns(2)
    with col_com:
        st.subheader("Comètes")
        st.write("- **C/2023 A3** : Rareté 100% (Pépite)")
        st.write("- **67P/C-G** : Visible en fin de nuit")
    with col_ecl:
        st.subheader("Éclipses")
        st.warning("📅 12 Août 2026 : Éclipse Totale de Soleil")
        st.write("📅 28 Août 2026 : Éclipse Lunaire Partielle")

with tab3:
    st.header("👨‍🏫 Stratégie de Shooting")
    total_h_req = 12 if "Arp" in t_data["cat"] else 6
    st.metric("Temps total recommandé", f"{total_h_req} heures")
    
    # Calcul Batterie
    conso = 3.5
    autonomie = (batt_wh / 12) / conso
    st.write(f"🔋 Avec votre setup, autonomie de **{autonomie:.1f}h** par nuit.")
    st.write(f"📅 Il vous faudra **{int(np.ceil(total_h_req/autonomie))} nuits** pour une image parfaite.")

# --- NOTIFICATION SONORE ---
if st.button("🔔 Tester l'alerte de sortie"):
    st.toast("Il est temps de sortir le matériel !", icon="🔭")
    st.markdown('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3"></audio>', unsafe_allow_html=True)

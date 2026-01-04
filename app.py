import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun, get_body
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Expert Planning", layout="wide")

OW_API_KEY = "16f68f1e07fea20e39f52de079037925"

# --- CATALOGUE AVEC TEMPS DE SHOOT MAX ---
CATALOG = [
    {"name": "M42 (Orion)", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse", "mag": 4.0, "total_hours": 3, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg/600px-Orion_Nebula_-_Hubble_2006_mosaic_18000.jpg"},
    {"name": "M31 (Andromède)", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie", "mag": 3.4, "total_hours": 5, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/M31_09-01-2011.jpg/600px-M31_09-01-2011.jpg"},
    {"name": "NGC 6960 (Dentelles)", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse", "mag": 7.0, "total_hours": 8, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/The_Witch%27s_Broom_Nebula.jpg/600px-The_Witch%27s_Broom_Nebula.jpg"},
    {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie", "mag": 13.0, "total_hours": 12, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/600px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg"},
    {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P.", "mag": 12.2, "total_hours": 15, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/600px-Abell_31_nebula.jpg"},
    {"name": "C/2023 A3 (Comète)", "ra": "18h40m00s", "dec": "+05h00m00s", "type": "Comète", "mag": 5.0, "total_hours": 1, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Comet_C2023_A3_2024-10-14.jpg/600px-Comet_C2023_A3_2024-10-14.jpg"}
]

# --- SIDEBAR : BOUSSOLE DÉTAILLÉE ---
st.sidebar.title("🧭 BOUSSOLE D'HORIZON")
with st.sidebar.expander("🌲 Obstacles (8 secteurs)", expanded=True):
    obs = {
        "N": st.slider("Nord", 0, 70, 20),
        "NE": st.slider("Nord-Est", 0, 70, 15),
        "E": st.slider("Est", 0, 70, 25),
        "SE": st.slider("Sud-Est", 0, 70, 10),
        "S": st.slider("Sud", 0, 70, 5),
        "SO": st.slider("Sud-Ouest", 0, 70, 20),
        "O": st.slider("Ouest", 0, 70, 30),
        "NO": st.slider("Nord-Ouest", 0, 70, 15),
    }

def get_horizon_height(az):
    if az < 22.5 or az >= 337.5: return obs["N"]
    if 22.5 <= az < 67.5: return obs["NE"]
    if 67.5 <= az < 112.5: return obs["E"]
    if 112.5 <= az < 157.5: return obs["SE"]
    if 157.5 <= az < 202.5: return obs["S"]
    if 202.5 <= az < 247.5: return obs["SO"]
    if 247.5 <= az < 292.5: return obs["O"]
    return obs["NO"]

# --- CALCUL DES CIBLES VISIBLES ---
lat = st.sidebar.number_input("Lat", value=48.85)
lon = st.sidebar.number_input("Lon", value=2.35)
loc = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()
visible_targets = []

for obj in CATALOG:
    coord = SkyCoord(obj["ra"], obj["dec"])
    altaz = coord.transform_to(AltAz(obstime=now, location=loc))
    if altaz.alt.deg > get_horizon_height(altaz.az.deg):
        visible_targets.append(obj)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites : Expert Planning 2026")

if not visible_targets:
    st.warning("⚠️ Aucune cible n'est visible au-dessus de vos obstacles.")
    sel_name = st.selectbox("Toutes les cibles :", [t["name"] for t in CATALOG])
else:
    sel_name = st.selectbox("🎯 Cibles VISIBLES (Filtrées par boussole) :", [t["name"] for t in visible_targets])

t_data = next(t for t in CATALOG if t["name"] == sel_name)

# --- AFFICHAGE & RECOMMENDATIONS ---
c1, c2 = st.columns([1, 1.5])
with c1:
    st.image(t_data["img"], use_container_width=True)
with c2:
    st.subheader(f"📊 Analyse Expert : {sel_name}")
    st.info(f"Magnitude: {t_data['mag']} | Type: {t_data['type']}")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("⏱️ **Pose Unitaire (ASIAIR) :**")
        st.write(f"👉 {120 if t_data['mag'] < 6 else 300 if t_data['mag'] < 10 else 600}s")
    with col_b:
        st.write("🌌 **Temps total recommandé :**")
        st.write(f"👉 {t_data['total_hours']} heures minimum")

    if "Galaxie" in t_data['type']:
        st.error("💎 FILTRE : Tiroir VIDE ou Optolong L-Pro")
    else:
        st.success("🌀 FILTRE : Svbony SV220 (Dual-Band)")

# --- GRAPHIQUE ---
st.divider()
times = now + np.linspace(0, 12, 100)*u.hour
target_altaz = SkyCoord(t_data["ra"], t_data["dec"]).transform_to(AltAz(obstime=times, location=loc))
moon_alt = get_body('moon', times, loc).transform_to(AltAz(obstime=times, location=loc)).alt.deg
h_curve = [get_horizon_height(az) for az in target_altaz.az.deg]

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(np.linspace(0, 12, 100), target_altaz.alt.deg, color="#00ffcc", lw=3, label=t_data["name"])
ax.plot(np.linspace(0, 12, 100), moon_alt, color="white", ls="--", alpha=0.3, label="Lune")
ax.fill_between(np.linspace(0, 12, 100), 0, h_curve, color='red', alpha=0.2, label="Obstacles (Boussole)")
ax.set_ylim(0, 90)
ax.set_facecolor("#0e1117")
fig.patch.set_facecolor("#0e1117")
ax.legend()
st.pyplot(fig)

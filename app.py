import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy import units as u
from astropy.time import Time

# Configuration de la page
st.set_page_config(page_title="AstroPépites Pro", layout="wide", page_icon="🔭")

# --- BASES DE DONNÉES COMPLÈTES ---
POWER_STATIONS = {"Bluetti EB3A (268Wh)": 22, "Jackery 500": 43, "EcoFlow River Pro": 60}
TELESCOPES = {"Sky-Watcher Evolux 62ED": 400, "Askar FRA400": 400, "72ED": 420, "C8 f/6.3": 1280}
MOUNTS = {"Star Adventurer GTi": 0.5, "HEQ5": 1.2, "EQ6-R Pro": 1.5}
CAMERAS = {"ZWO ASI 183 MC Pro": {"w": 13.2, "h": 8.8, "px": 2.4, "cons": 1.5}, "ASI 2600MC": {"w": 23.5, "h": 15.7, "px": 3.76, "cons": 2.0}}

# --- SIDEBAR : CONFIGURATION ---
st.sidebar.title("🛠 CONFIGURATION SETUP")
sel_scope = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
sel_mount = st.sidebar.selectbox("Monture", list(MOUNTS.keys()))
sel_cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))
sel_ps = st.sidebar.selectbox("Batterie", list(POWER_STATIONS.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("🌲 Horizon Local (Boussole)")
h_n = st.sidebar.slider("Nord", 0, 60, 15)
h_e = st.sidebar.slider("Est", 0, 60, 15)
h_s = st.sidebar.slider("Sud", 0, 60, 15)
h_o = st.sidebar.slider("Ouest", 0, 60, 15)

# --- CALCULS LOGISTIQUES ---
cons_totale = MOUNTS[sel_mount] + CAMERAS[sel_cam]["cons"] + 1.5 # + ASIAIR & Dew
autonomie = POWER_STATIONS[sel_ps] / cons_totale
resolution = (CAMERAS[sel_cam]["px"] / TELESCOPES[sel_scope]) * 206

# --- INTERFACE PRINCIPALE ---
st.title("🔭 AstroPépites : Planificateur Expert")

c1, c2, c3 = st.columns(3)
c1.metric("⚡ Conso.", f"{cons_totale:.2f} A")
c2.metric("🔋 Autonomie (Bluetti)", f"{autonomie:.1f} h")
c3.metric("📏 Échantillonnage", f"{resolution:.2f} \"/px")

# --- RECHERCHE ET VISIBILITÉ ---
st.header("🎯 Cibles & Visibilité")
col_lat, col_lon = st.columns(2)
lat = col_lat.number_input("Latitude", value=48.85)
lon = col_lon.number_input("Longitude", value=2.35)
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

targets_db = [
    {"name": "Arp 273 (La Rose)", "ra": "02h21m28s", "dec": "+39d22m32s", "size": 2.1},
    {"name": "Sh2-132 (Lion)", "ra": "22h18m42s", "dec": "+56d07m24s", "size": 90},
    {"name": "Abell 39", "ra": "16h27m33s", "dec": "+27d54m33s", "size": 2.5}
]

sel_target = st.selectbox("Choisir une cible rare", [t["name"] for t in targets_db])
t_data = next(t for t in targets_db if t["name"] == sel_target)

# --- GRAPHIQUE DE VISIBILITÉ ---
coord = SkyCoord(t_data["ra"], t_data["dec"])
times = now + np.linspace(0, 12, 50)*u.hour
altaz = coord.transform_to(AltAz(obstime=times, location=location))

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(np.linspace(0, 12, 50), altaz.alt.deg, color="#00ffcc", lw=2)
ax.axhline(15, color="red", linestyle="--", label="Horizon")
ax.set_facecolor("#0e1117")
fig.patch.set_facecolor("#0e1117")
ax.tick_params(colors='white')
ax.set_ylabel("Altitude (°)", color="white")
st.pyplot(fig)

# --- EXPORT ASIAIR & MAIL ---
st.divider()
st.subheader("📲 Transfert vers ASIAIR")

# Correction de l'erreur TypeError mailto
mail_body = f"Cible: {sel_target}\nRA: {t_data['ra']}\nDEC: {t_data['dec']}\n\nBon shoot !"
subject = f"Cible Astro: {sel_target}"
# Encodage simple pour éviter les erreurs de caractères
mailto_url = f"mailto:?subject={subject}&body={mail_body}".replace(" ", "%20").replace("\n", "%0A")

col_a, col_b = st.columns(2)
with col_a:
    st.text_input("Coordonnées à copier :", f"{t_data['ra']} | {t_data['dec']}")
    st.markdown(f'<a href="{mailto_url}"><button style="width:100%; padding:10px; border-radius:10px; background-color:#ff4b4b; color:white; border:none; cursor:pointer;">📧 Envoyer par Mail</button></a>', unsafe_allow_html=True)

with col_b:
    csv = f"Name,RA,Dec\n{sel_target},{t_data['ra']},{t_data['dec']}"
    st.download_button("💾 Télécharger CSV ASIAIR", csv, file_name=f"{sel_target}.csv")

st.caption("AstroPépites v4.0 - Optimisé pour Evolux 62ED & Bluetti EB3A")

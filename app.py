import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy import units as u
from astropy.time import Time
# Les imports qui posaient problème sont maintenant gérés par le requirements.txt
try:
    from astroquery.simbad import Simbad
    from astroquery.vizier import Vizier
except ImportError:
    st.error("L'application installe encore les bibliothèques. Veuillez patienter ou vérifier votre fichier requirements.txt.")

# ==========================================
# BASES DE DONNÉES (MATÉRIEL & POWER)
# ==========================================
POWER_STATIONS = {"Jackery 500": 43, "Bluetti EB3A": 22, "EcoFlow River 2 Pro": 64, "Batterie 100Ah": 100}
TELESCOPES = {"Sky-Watcher Evolux 62ED": 400, "Askar FRA400": 400, "72ED": 420}
MOUNTS = {"Star Adventurer GTi": {"cons": 0.5, "max": 5.0}, "EQ6-R Pro": {"cons": 1.5, "max": 20.0}}
CAMERAS = {"ZWO ASI 183 MC Pro": {"w": 13.2, "h": 8.8, "px": 2.4, "cons": 1.5}}

# ==========================================
# INTERFACE
# ==========================================
st.sidebar.title("🛠 CONFIGURATION SETUP")
sel_scope = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
sel_mount = st.sidebar.selectbox("Monture", list(MOUNTS.keys()))
sel_cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))
sel_ps = st.sidebar.selectbox("Batterie", list(POWER_STATIONS.keys()))

# Calcul consommation
cons_totale = MOUNTS[sel_mount]["cons"] + CAMERAS[sel_cam]["cons"] + 1.5 # + ASIAIR & Dew
autonomie = POWER_STATIONS[sel_ps] / cons_totale

st.title("🔭 AstroPépites : Planificateur Pro")

# --- RECHERCHE DE CIBLES ---
st.header("🎯 Recherche d'objets rares")
col_lat, col_lon = st.columns(2)
lat = col_lat.number_input("Latitude", value=48.85)
lon = col_lon.number_input("Longitude", value=2.35)

# Cibles exotiques pré-définies (pour éviter les erreurs d'API au début)
targets_db = [
    {"name": "Arp 273", "ra": "02h 21m 28s", "dec": "+39° 22' 32\"", "type": "Galaxies en interaction"},
    {"name": "Abell 39", "ra": "16h 27m 33s", "dec": "+27° 54' 33\"", "type": "Nébuleuse Planétaire"},
    {"name": "Sh2-132", "ra": "22h 18m 42s", "dec": "+56° 07' 24\"", "type": "Nébuleuse du Lion"}
]

target = st.selectbox("Choisir une cible rare", [t["name"] for t in targets_db])
target_info = next(t for t in targets_db if t["name"] == target)

# --- VISIBILITÉ & LOGISTIQUE ---
st.subheader(f"📊 Infos pour {target}")
c1, c2 = st.columns(2)
c1.metric("Autonomie Batterie", f"{autonomie:.1f} h")
c2.metric("Échantillonnage", f"{(CAMERAS[sel_cam]['px']/TELESCOPES[sel_scope])*206:.2f} \"/px")

# --- EXPORT & ENVOI MAIL ---
st.divider()
st.subheader("📬 Envoyer vers mon ASIAIR")

# Préparation du texte pour le mail
mail_body = f"Cible : {target}\nCoordonnees J2000 :\nRA : {target_info['ra']}\nDEC : {target_info['dec']}\n\nGenere par AstroPepites."
subject = f"Cible Astro : {target}"
mailto_link = f"mailto:?subject={subject}&body={mail_body.replace(' ', '%20').replace('\n', '%0A')}"

col_mail, col_csv = st.columns(2)

with col_mail:
    st.markdown(f'<a href="{mailto_link}" style="text-decoration:none;"><button style="width:100%; border-radius:5px; background-color:#ff4b4b; color:white; border:none; padding:10px;">📧 Envoyer par Mail</button></a>', unsafe_allow_status=True)

with col_csv:
    # Export CSV format ASIAIR
    csv_str = f"Name,RA,Dec\n{target},{target_info['ra']},{target_info['dec']}"
    st.download_button("💾 Télécharger CSV (ASIAIR)", csv_str, file_name=f"{target}_asiair.csv", mime="text/csv")

st.info("💡 Le bouton Mail ouvrira votre application de messagerie. Copiez ensuite ces valeurs dans l'onglet 'User Objects' de votre ASIAIR.")

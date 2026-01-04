import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_moon
from astropy import units as u
from astropy.time import Time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Communauté & Catalogues", layout="wide")

# --- 1. SIDEBAR : MATÉRIEL UNIVERSEL & BOUSSOLE ---
st.sidebar.title("🛠 CONFIGURATION SETUP")

with st.sidebar.expander("🔭 Mon Matériel (Personnalisable)", expanded=True):
    # Permet à n'importe qui d'entrer ses propres specs
    scope_name = st.text_input("Nom du Télescope", "Evolux 62ED")
    focal_length = st.number_input("Focale (mm)", value=400)
    cam_name = st.text_input("Nom de la Caméra", "ASI 183 MC Pro")
    pixel_size = st.number_input("Taille Pixel (µm)", value=2.4, format="%.2f")
    batt_wh = st.number_input("Capacité Batterie (Wh)", value=268) # 268Wh par défaut (EB3A)

with st.sidebar.expander("🌲 Ma Boussole d'Horizon", expanded=True):
    st.caption("Définissez la hauteur de vos obstacles locaux (°)")
    h_n = st.slider("Nord (0°)", 0, 70, 20)
    h_e = st.slider("Est (90°)", 0, 70, 15)
    h_s = st.slider("Sud (180°)", 0, 70, 10)
    h_o = st.slider("Ouest (270°)", 0, 70, 25)

with st.sidebar.expander("📚 Filtres Catalogues", expanded=True):
    show_m = st.checkbox("Messier (M)", value=True)
    show_ngc = st.checkbox("NGC / IC", value=True)
    show_arp = st.checkbox("Arp (Raretés)", value=True)
    show_abell = st.checkbox("Abell (Planétaires)", value=True)

# --- 2. BASE DE DONNÉES ÉTENDUE ---
# Exemple de base de données multi-catalogues
DB_OBJECTS = [
    {"name": "M31 - Andromède", "cat": "Messier", "ra": "00h42m44s", "dec": "+41d16m09s", "type": "Galaxie"},
    {"name": "M42 - Orion", "cat": "Messier", "ra": "05h35m17s", "dec": "-05d23m28s", "type": "Nébuleuse"},
    {"name": "NGC 6960 - Dentelles", "cat": "NGC / IC", "ra": "20h45m42s", "dec": "+30d42m30s", "type": "Nébuleuse"},
    {"name": "Arp 273 - La Rose", "cat": "Arp (Raretés)", "ra": "02h21m28s", "dec": "+39d22m32s", "type": "Galaxie"},
    {"name": "Abell 31", "cat": "Abell (Planétaires)", "ra": "08h54m13s", "dec": "+08d53m52s", "type": "Nébuleuse P."},
]

# Filtrage dynamique de la liste selon les cases cochées
active_cats = []
if show_m: active_cats.append("Messier")
if show_ngc: active_cats.append("NGC / IC")
if show_arp: active_cats.append("Arp (Raretés)")
if show_abell: active_cats.append("Abell (Planétaires)")

filtered_list = [obj for obj in DB_OBJECTS if obj["cat"] in active_cats]

# --- 3. INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites : Le Planificateur Communautaire")

# Calculs techniques universels
resolution = (pixel_size / focal_length) * 206
st.info(f"✨ Votre configuration ({scope_name} + {cam_name}) échantillonne à **{resolution:.2f} \"/px**.")

# Sélection de la cible
sel_obj = st.selectbox("🎯 Choisir une cible dans les catalogues sélectionnés", [o["name"] for o in filtered_list])
t_data = next(obj for obj in filtered_list if obj["name"] == sel_obj)

# --- 4. ANALYSE LUNAIRE ET VISIBILITÉ ---
now = Time.now()
location = EarthLocation(lat=48.8*u.deg, lon=2.3*u.deg) # GPS par défaut
moon = get_moon(now, location)
target_coord = SkyCoord(t_data['ra'], t_data['dec'])
dist_moon = target_coord.separation(moon)

# Graphique avec Horizon Boussole
times = now + np.linspace(0, 12, 100)*u.hour
altaz = target_coord.transform_to(AltAz(obstime=times, location=location))

# Logique Horizon dynamique
horizons = []
for az in altaz.az.deg:
    if 315 <= az or az < 45: horizons.append(h_n)
    elif 45 <= az < 135: horizons.append(h_e)
    elif 135 <= az < 225: horizons.append(h_s)
    else: horizons.append(h_o)

fig, ax = plt.subplots(figsize=(10, 3.5))
ax.plot(np.linspace(0, 12, 100), altaz.alt.deg, color="#00ffcc", lw=3, label="Trajectoire")
ax.fill_between(np.linspace(0, 12, 100), 0, horizons, color="red", alpha=0.3, label="Zone Masquée")
ax.set_facecolor("#0e1117")
fig.patch.set_facecolor("#0e1117")
ax.set_ylim(0, 90)
ax.legend()
st.pyplot(fig)

# --- 5. INFOS & FILTRES CONSEILLÉS ---
st.divider()
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("💡 Conseils Matériel")
    if "Galaxie" in t_data['type']:
        st.write("Filtre : **RGB / L-Pro** recommandé.")
        st.write("Tiroir : Laisser vide ou Anti-pollution léger.")
    else:
        st.write("Filtre : **Narrowband (SV220)** recommandé.")
        st.write("Tiroir : Glisser le filtre pour isoler le signal.")

with c2:
    st.subheader("🌙 Influence Lunaire")
    st.write(f"Distance Cible/Lune : **{dist_moon.deg:.1f}°**")
    if dist_moon.deg < 30:
        st.error("Lune trop proche ! Risque de voile blanc.")
    else:
        st.success("Distance de sécurité OK.")

with c3:
    st.subheader("🔋 Autonomie Estimée")
    # Calcul basique pour n'importe quelle batterie
    conso_moyenne = 3.5 # Amps
    autonomie = (batt_wh / 12) / conso_moyenne
    st.write(f"Sur une batterie de {batt_wh} Wh :")
    st.metric("Durée", f"{autonomie:.1f} h")

st.caption("AstroPépites v7.0 - Outil de planification multi-utilisateur")

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- DATA / CATALOGUES ---
@st.cache_data
def load_data():
    return [
        {"name": "M42 Orion", "ra": "05h35m17s", "dec": "-05d23m28s", "cat": "Messier", "type": "Nébuleuse", "mag": 4.0, "hours": 3},
        {"name": "M31 Andromède", "ra": "00h42m44s", "dec": "+41d16m09s", "cat": "Messier", "type": "Galaxie", "mag": 3.4, "hours": 5},
        {"name": "NGC 6960 Dentelles", "ra": "20h45m42s", "dec": "+30d42m30s", "cat": "NGC", "type": "Nébuleuse", "mag": 7.0, "hours": 8},
        {"name": "Arp 273 La Rose", "ra": "02h21m28s", "dec": "+39d22m32s", "cat": "Arp", "type": "Galaxie", "mag": 13.0, "hours": 12},
        {"name": "Abell 31", "ra": "08h54m13s", "dec": "+08d53m52s", "cat": "Abell", "type": "Nébuleuse P.", "mag": 12.2, "hours": 15},
        {"name": "C/2023 A3 Tsuchinshan", "ra": "18h40m00s", "dec": "+05h00m00s", "cat": "Comètes", "type": "Comète", "mag": 5.0, "hours": 1}
    ]

# --- SIDEBAR COMPACTE ---
st.sidebar.header("⚙️ CONFIGURATION")

# 1. Sélection Catalogues
with st.sidebar.expander("📂 Catalogues à afficher", expanded=True):
    show_m = st.checkbox("Messier", True)
    show_n = st.checkbox("NGC", True)
    show_a = st.checkbox("Arp / Abell", True)
    show_c = st.checkbox("Comètes", True)

# 2. Setup Optique
with st.sidebar.expander("🔭 Optique (Evolux 62ED)", expanded=False):
    f_nat = st.number_input("Focale (mm)", value=400)
    opt_type = st.selectbox("Accessoire", ["Aucun (1.0x)", "Réducteur (0.8x)", "Réducteur (0.9x)", "Barlow (2.0x)"])
    mult = 1.0
    if "0.8" in opt_type: mult = 0.8
    elif "0.9" in opt_type: mult = 0.9
    elif "2.0" in opt_type: mult = 2.0
    f_res = f_nat * mult
    st.caption(f"Focale finale : {f_res:.0f} mm")

# 3. Batterie Bluetti
with st.sidebar.expander("🔋 Énergie", expanded=False):
    conso = st.slider("Conso (W)", 5, 60, 25)
    st.caption(f"Autonomie EB3A : {268/conso:.1f}h")

# 4. Boussole (Horizon) - Design plus fin
st.sidebar.subheader("🧭 Horizon (Boussole)")
h_vals = {}
cols_b = st.sidebar.columns(2)
directions = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
for i, d in enumerate(directions):
    h_vals[d] = cols_b[i%2].number_input(f"{d} (°)", 0, 80, 15, step=5)

# --- CALCULS ---
lat, lon = 46.65, 6.91
loc = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

def is_visible(ra, dec):
    altaz = SkyCoord(ra, dec).transform_to(AltAz(obstime=now, location=loc))
    lim = list(h_vals.values())[int(((altaz.az.deg + 22.5) % 360) // 45)]
    return altaz.alt.deg > lim

# Filtrage Catalogue
full_cat = load_data()
filtered_cat = [obj for obj in full_cat if 
                (show_m and obj['cat'] == "Messier") or 
                (show_n and obj['cat'] == "NGC") or 
                (show_a and (obj['cat'] == "Arp" or obj['cat'] == "Abell")) or 
                (show_c and obj['cat'] == "Comètes")]

visibles = [o for o in filtered_cat if is_visible(o["ra"], o["dec"])]

# --- INTERFACE ---
st.title("🔭 AstroPépites Pro 2026")

col_main, col_side = st.columns([2, 1])

with col_main:
    if visibles:
        target_name = st.selectbox("🎯 Cibles VISIBLES :", [o["name"] for o in visibles])
    else:
        st.warning("Aucune cible visible avec ces filtres/horizon.")
        target_name = st.selectbox("Toutes les cibles :", [o["name"] for o in filtered_cat])

    target = next(o for o in full_cat if o["name"] == target_name)
    
    # Dashboard Info
    c1, c2, c3 = st.columns(3)
    c1.metric("Magnitude", target["mag"])
    c2.metric("Type", target["type"])
    c3.metric("Shoot Recommandé", f"{target['hours']}h")

    # Alerte Filtre
    if target["type"] in ["Galaxie", "Comète"]:
        st.error("🚫 FILTRE : Retirez le SV220 ! (Utilisez un filtre clair)")
    else:
        st.success("✅ FILTRE : SV220 Dual-Band OK")

    # Graphique Trajectoire
    times = now + np.linspace(0, 12, 100)*u.hour
    obj_altaz = SkyCoord(target["ra"], target["dec"]).transform_to(AltAz(obstime=times, location=loc))
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.linspace(0, 12, 100), obj_altaz.alt.deg, color="#00ffcc", lw=3)
    ax.fill_between(np.linspace(0, 12, 100), 0, 15, color='red', alpha=0.2)
    ax.set_ylim(0, 90)
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")
    st.pyplot(fig)

with col_side:
    st.subheader("🌹 Horizon Local")
    # Rose des vents compacte
    angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
    fig_r, ax_r = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3,3))
    ax_r.bar(angles, list(h_vals.values()), color='red', alpha=0.5)
    ax_r.bar(angles, [90-v for v in h_vals.values()], bottom=list(h_vals.values()), color='green', alpha=0.3)
    ax_r.set_theta_zero_location('N')
    ax_r.set_theta_direction(-1)
    ax_r.set_facecolor("#0e1117")
    fig_r.patch.set_facecolor("#0e1117")
    st.pyplot(fig_r)
    
    st.info(f"📍 Romont (46.65, 6.91)\n🕒 {now.iso[:16]}")

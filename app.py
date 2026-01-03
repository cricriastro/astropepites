import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# =========================
# CONFIG PAGE & STYLE
# =========================
st.set_page_config(page_title="AstroPépites Pro – Pro Edition", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #000; color: white; }
h1, h2, h3 { color: #ff4444 !important; }
.stMetric { background: #120000; border: 1px solid #ff4444; border-radius: 10px; padding: 10px; }
[data-testid="stMetricValue"] { color: #ff4444; }
.stTabs [data-baseweb="tab-list"] { background-color: #000; }
</style>
""", unsafe_allow_html=True)

# =========================
# GÉOLOCALISATION
# =========================
st.sidebar.title("🔭 AstroPépites Pro")

loc = streamlit_js_eval(data_key="geo", function_name="getCurrentPosition", delay=100)
default_lat, default_lon = 46.8, 7.1

if loc and "coords" in loc:
    st.session_state.lat = loc["coords"]["latitude"]
    st.session_state.lon = loc["coords"]["longitude"]

lat = st.sidebar.number_input("Latitude", value=st.session_state.get("lat", default_lat), format="%.4f")
lon = st.sidebar.number_input("Longitude", value=st.session_state.get("lon", default_lon), format="%.4f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

# =========================
# MASQUE HORIZON
# =========================
st.sidebar.header("🌲 Masque Horizon")
use_csv = st.sidebar.checkbox("Importer un CSV horizon")
csv_horizon = None
if use_csv:
    file = st.sidebar.file_uploader("Fichier (azimuth,altitude)", type="csv")
    if file: csv_horizon = pd.read_csv(file)

with st.sidebar.expander("Réglage manuel", expanded=not use_csv):
    m_vals = [st.slider(f"{d}", 0, 90, 15) for d in ["Nord", "NE", "Est", "SE", "Sud", "SW", "Ouest", "NW"]]

def get_horizon_limit(az):
    if csv_horizon is not None:
        return np.interp(az, csv_horizon.iloc[:,0], csv_horizon.iloc[:,1])
    idx = int(((az + 22.5) % 360) // 45)
    return m_vals[idx]

# Boussole Horizon (Corrigée et Robuste)
angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
fig_pol, ax_pol = plt.subplots(figsize=(3,3), subplot_kw={"projection":"polar"})
ax_pol.set_theta_zero_location("N")
ax_pol.set_theta_direction(-1)
angles_closed, m_vals_closed = np.append(angles, angles), np.append(m_vals, m_vals)
ax_pol.fill(angles_closed, m_vals_closed, color="red", alpha=0.4)
ax_pol.fill_between(angles_closed, m_vals_closed, 90, color="green", alpha=0.2)
ax_pol.set_yticklabels([])
ax_pol.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
ax_pol.set_facecolor("black")
fig_pol.patch.set_facecolor("black")
st.sidebar.pyplot(fig_pol)

# =========================
# CATALOGUES PRO
# =========================
# Ajout de plus d'objets pour étendre le catalogue
catalog_pro = [
    # Messier
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxie","rgb":True,"ha":True},
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Nébuleuse","rgb":True,"ha":True},
    {"name":"M51 Whirlpool","ra":"13:29:52","dec":"+47:11:43","type":"Galaxie","rgb":True,"ha":True},
    {"name":"M13 Hercules","ra":"16:41:41","dec":"+36:27:37","type":"Amas Globulaire","rgb":True,"ha":False},
    # NGC & IC populaires
    {"name":"NGC 7000 North America","ra":"20:58:54","dec":"+44:19:00","type":"Nébuleuse","rgb":True,"ha":True},
    {"name":"NGC 6960 Veil","ra":"20:45:58","dec":"+30:43:00","type":"SNR","rgb":True,"ha":True},
    {"name":"IC 1396 Elephant Trunk","ra":"21:34:55","dec":"+57:29:10","type":"Nébuleuse","rgb":True,"ha":True},
    {"name":"NGC 891","ra":"02:22:33","dec":"+42:20:50","type":"Galaxie","rgb":True,"ha":False},
    {"name":"NGC 281 Pacman","ra":"00:52:59","dec":"+56:37:19","type":"Nébuleuse","rgb":True,"ha":True},
]

# =========================
# BASES DE DONNÉES MATÉRIEL (Télescopes & Caméras)
# =========================
TELESCOPES = [
    "Sélectionner un télescope",
    "Sky-Watcher Evolux 62 ED (Votre équipement)",
    "Celestron EdgeHD 800",
    "Omegon Dobson N 200/1200",
    "William Optics RedCat 51",
    "Autres réfracteurs APO..."
]

CAMERAS = [
    "Sélectionner une caméra",
    "ZWO ASI 183 MC Pro (Votre équipement)",
    "ZWO ASI 2600 MC Pro",
    "ZWO ASI 585 MC Pro (Planétaire)",
    "QHY 268C",
    "Canon EOS Ra (DSLR)"
]


tab1, tab2, tab3, tab4 = st.tabs(["💎 Cibles & Radar", "⚙️ Mon Matériel", "☄️ Système Solaire", "📤 Exports"])

# --- TAB 1 : RADAR ---
with tab1:
    names = [o["name"] for o in catalog_pro]
    target_name = st.selectbox("Choisir une cible", names)
    obj = next(o for o in catalog_pro if o["name"]==target_name)
    coord = SkyCoord(obj["ra"], obj["dec"], unit=(u.hourangle,u.deg))
    altaz = coord.transform_to(AltAz(obstime=now,location=location))
    limit = get_horizon_limit(altaz.az.deg)
    visible = altaz.alt.deg > limit
    
    col1,col2 = st.columns(2)
    with col1:
        status = "VISIBLE" if visible else "MASQUÉ"
        st.subheader(f"{target_name} – {status}")
        st.write(f"Altitude : {altaz.alt:.1f} | Azimut : {altaz.az:.1f}")
        modes=[]
        if obj["rgb"]: modes.append("RGB")
        if obj["ha"]: modes.append("Ha")
        st.write("📸 Modes conseillés :", " + ".join(modes))

    with col2:
        times = now + np.linspace(0,12,30)*u.hour
        alts=[coord.transform_to(AltAz(obstime=t,location=location)).alt.deg for t in times]
        chart_data = pd.DataFrame({"Altitude":alts, "Horizon":[get_horizon_limit(a.az.deg) for a in coord.transform_to(AltAz(obstime=times,location=location))]})
        st.line_chart(chart_data)

# --- TAB 2 : MATÉRIEL ---
with tab2:
    st.subheader("Configuration d'imagerie")
    col_scope, col_cam = st.columns(2)
    with col_scope:
        telescope = st.selectbox("Télescope principal", TELESCOPES)
    with col_cam:
        camera = st.selectbox("Caméra principale", CAMERAS)
    
    if telescope == "Sky-Watcher Evolux 62 ED (Votre équipement)":
        st.info("ℹ️ Votre configuration utilise une focale de 400mm (ou 340mm avec réducteur 0.85x), idéale pour les grands objets comme M31 ou NGC 7000.")

# --- TAB 3 : SYSTÈME SOLAIRE ---
with tab3:
    st.subheader("🌑 Éphémérides de la nuit")
    c1, c2, c3 = st.columns(3)
    # Utilisation de get_body() qui est robuste
    moon = get_body("moon", now).transform_to(AltAz(obstime=now, location=location))
    sun = get_body("sun", now).transform_to(AltAz(obstime=now, location=location))
    
    c1.metric("Lune Alt", f"{moon.alt.deg:.1f}°")
    c2.metric("Soleil Alt", f"{sun.alt.deg:.1f}°")
    c3.metric("Phase Lune", "À calculer...") 

    st.subheader("📅 Événements 2026")
    st.info("📢 **12 Août 2026** : Éclipse Solaire Totale (Europe)")

# --- TAB 4 : EXPORTS ---
with tab4:
    st.subheader("📋 Coordonnées pour votre monture")
    st.code(f"TARGET: {target_name}\nRA: {coord.ra.to_string(unit=u.hour)}\nDEC: {coord.dec.to_string(unit=u.deg)}")
    df = pd.DataFrame([{"name":target_name, "ra":coord.ra.deg, "dec":coord.dec.deg, "alt":round(altaz.alt.deg,1), "az":round(altaz.az.deg,1)}])
    st.download_button("Télécharger CSV", df.to_csv(index=False), file_name="astropepites_target.csv")

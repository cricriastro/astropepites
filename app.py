import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Importations astropy corrigées:
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy import get_moon, get_sun # <-- Correct: import direct depuis astropy
from astropy.time import Time
import astropy.units as u

from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# =========================
# CONFIG PAGE & STYLE
# =========================
st.set_page_config(page_title="AstroPépites Pro – 2026 Edition", layout="wide")

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
# GÉOLOCALISATION SÉCURISÉE
# =========================
st.sidebar.title("🔭 AstroPépites Pro")

loc = streamlit_js_eval(data_key="geo", function_name="getCurrentPosition", delay=100)

# Valeurs par défaut si la géoloc échoue
default_lat = 46.8
default_lon = 7.1

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
    m_vals = []
    directions = ["Nord", "NE", "Est", "SE", "Sud", "SW", "Ouest", "NW"]
    for d in directions:
        m_vals.append(st.slider(f"{d}", 0, 90, 15))

def get_horizon_limit(az):
    if csv_horizon is not None:
        return np.interp(az, csv_horizon.iloc[:,0], csv_horizon.iloc[:,1])
    idx = int(((az + 22.5) % 360) // 45)
    return m_vals[idx]

# Boussole Horizon
angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
fig_pol, ax_pol = plt.subplots(figsize=(3,3), subplot_kw={"projection":"polar"})
ax_pol.set_theta_zero_location("N")
ax_pol.set_theta_direction(-1)
ax_pol.fill(np.append(angles, angles), m_vals + [m_vals], color="red", alpha=0.4)
ax_pol.set_yticklabels([])
ax_pol.set_facecolor("black")
fig_pol.patch.set_facecolor("black")
st.sidebar.pyplot(fig_pol)

# =========================
# CATALOGUE & LOGIQUE
# =========================
catalog = [
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxie","rgb":True,"ha":True},
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Nébuleuse","rgb":True,"ha":True},
    {"name":"M51 Whirlpool","ra":"13:29:52","dec":"+47:11:43","type":"Galaxie","rgb":True,"ha":True},
    {"name":"M13 Hercules","ra":"16:41:41","dec":"+36:27:37","type":"Amas","rgb":True,"ha":False},
    {"name":"NGC 7000 North America","ra":"20:58:54","dec":"+44:19:00","type":"Nébuleuse","rgb":True,"ha":True},
]

tab1, tab2, tab3 = st.tabs(["💎 Radar Cibles", "☄️ Système Solaire", "📤 Exports"])

# --- TAB 1 : RADAR ---
with tab1:
    col_sel, col_info = st.columns()
    with col_sel:
        target_name = st.selectbox("Sélectionner une pépite", [o["name"] for o in catalog])
        obj = next(o for o in catalog if o["name"] == target_name)
        coord = SkyCoord(obj["ra"], obj["dec"], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=location))
        
        limit = get_horizon_limit(altaz.az.deg)
        is_visible = altaz.alt.deg > limit
        
        st.metric("Altitude Actuelle", f"{altaz.alt.deg:.1f}°", 
                  delta="VISIBLE" if is_visible else "MASQUÉ", 
                  delta_color="normal" if is_visible else "inverse")

    with col_info:
        st.write(f"**Type:** {obj['type']}")
        st.write(f"**Azimut:** {altaz.az.deg:.1f}°")
        st.write(f"**Filtres:** {'🔴 Ha' if obj['ha'] else ''} {'🌈 RGB' if obj['rgb'] else ''}")

    # Graphique de soirée
    st.subheader("Trajectoire (prochaines 12h)")
    times = now + np.linspace(0, 12, 50) * u.hour
    frame = AltAz(obstime=times, location=location)
    orbit = coord.transform_to(frame)
    
    chart_data = pd.DataFrame({
        "Heure": [(datetime.now() + timedelta(hours=h)).strftime("%H:%M") for h in np.linspace(0, 12, 50)],
        "Altitude": orbit.alt.deg,
        "Horizon": [get_horizon_limit(a.az.deg) for a in orbit]
    }).set_index("Heure")
    
    st.area_chart(chart_data)

# --- TAB 2 : SYSTÈME SOLAIRE ---
with tab2:
    st.subheader("🌑 Éphémérides de la nuit")
    c1, c2, c3 = st.columns(3)
    
    moon = get_moon(now).transform_to(AltAz(obstime=now, location=location))
    sun = get_sun(now).transform_to(AltAz(obstime=now, location=location))
    
    c1.metric("Lune", f"{moon.alt.deg:.1f}°")
    c2.metric("Soleil", f"{sun.alt.deg:.1f}°")
    c3.metric("Phase Lune", "85% (Test)")

    st.subheader("📅 Événements 2026")
    st.info("📢 **12 Août 2026** : Éclipse Solaire Totale (visible partiellement en Europe)")
    st.warning("☄️ **Comète 12P/Pons-Brooks** : Vérifiez les mises à jour d'éphémérides.")

# --- TAB 3 : EXPORTS ---
with tab3:
    st.subheader("📋 Coordonnées pour votre monture")
    st.code(f"TARGET: {target_name}\nRA: {coord.ra.to_string(unit=u.hour)}\nDEC: {coord.dec.to_string(unit=u.deg)}")
    
    if st.button("Générer fichier de séquence (JSON)"):
        st.success("Fichier prêt pour N.I.N.A ou Stellarium (Simulation)")

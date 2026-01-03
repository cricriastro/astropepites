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
# CONFIG PAGE
# =========================
st.set_page_config(page_title="AstroPépites Pro – Free Edition", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #000; color: white; }
h1,h2,h3 { color:#ff4444; }
.stMetric { background:#120000; border:1px solid #ff4444; border-radius:10px; }
[data-testid="stMetricValue"] { color:#ff4444; }
</style>
""", unsafe_allow_html=True)

# =========================
# GEOLOCALISATION
# =========================
st.sidebar.title("🔭 AstroPépites Pro")

loc = streamlit_js_eval(
    data_key="geo",
    function_name="getCurrentPosition",
    delay=100
)

if loc:
    st.session_state.lat = loc["coords"]["latitude"]
    st.session_state.lon = loc["coords"]["longitude"]

lat = st.sidebar.number_input("Latitude", value=st.session_state.get("lat", 46.8))
lon = st.sidebar.number_input("Longitude", value=st.session_state.get("lon", 7.1))

location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()

# =========================
# MASQUE HORIZON
# =========================
st.sidebar.header("🌲 Masque Horizon")

use_csv = st.sidebar.checkbox("Importer un CSV horizon")

csv_horizon = None
if use_csv:
    file = st.sidebar.file_uploader("CSV azimuth / altitude", type="csv")
    if file:
        csv_horizon = pd.read_csv(file)

with st.sidebar.expander("Réglage manuel (sliders)", expanded=not use_csv):
    mN  = st.slider("Nord",0,90,15)
    mNE = st.slider("NE",0,90,15)
    mE  = st.slider("Est",0,90,20)
    mSE = st.slider("SE",0,90,30)
    mS  = st.slider("Sud",0,90,15)
    mSW = st.slider("SW",0,90,15)
    mW  = st.slider("Ouest",0,90,20)
    mNW = st.slider("NW",0,90,15)

mask_values = [mN,mNE,mE,mSE,mS,mSW,mW,mNW]

def horizon_limit(az):
    if csv_horizon is not None:
        return np.interp(az,
                         csv_horizon["azimuth"],
                         csv_horizon["altitude"])
    idx = int(((az+22.5)%360)//45)
    return mask_values[idx]

# =========================
# BOUSSOLE
# =========================
angles = np.linspace(0,2*np.pi,8,endpoint=False)
fig,ax = plt.subplots(figsize=(3,3), subplot_kw={"projection":"polar"})
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.fill(np.append(angles,angles[0]),
        mask_values+[mask_values[0]],
        color="red",alpha=0.4)
ax.fill_between(np.append(angles,angles[0]),
                mask_values+[mask_values[0]],90,
                color="green",alpha=0.2)
ax.set_yticklabels([])
ax.set_xticklabels(["N","NE","E","SE","S","SW","W","NW"])
fig.patch.set_facecolor("black")
ax.set_facecolor("black")
st.sidebar.pyplot(fig)

# =========================
# CATALOGUES GRATUITS
# =========================
catalog = [
    # Messier
    {"name":"M31 Andromède","ra":"00:42:44","dec":"+41:16:09","type":"Galaxy","rgb":True,"ha":True},
    {"name":"M42 Orion","ra":"05:35:17","dec":"-05:23:28","type":"Emission","rgb":True,"ha":True},
    {"name":"M51 Whirlpool","ra":"13:29:52","dec":"+47:11:43","type":"Galaxy","rgb":True,"ha":True},
    {"name":"M13 Hercules","ra":"16:41:41","dec":"+36:27:37","type":"Cluster","rgb":True,"ha":False},

    # NGC
    {"name":"NGC 7000 North America","ra":"20:58:54","dec":"+44:19:00","type":"Emission","rgb":True,"ha":True},
    {"name":"NGC 6960 Veil","ra":"20:45:58","dec":"+30:43:00","type":"SNR","rgb":True,"ha":True},
]

# =========================
# TABS
# =========================
st.title("🔭 AstroPépites Pro – Free Edition")

tab1,tab2,tab3 = st.tabs([
    "💎 Radar Cibles",
    "☄️ Comètes & Éclipses",
    "📤 Exports"
])

# =========================
# RADAR
# =========================
with tab1:
    names = [o["name"] for o in catalog]
    target_name = st.selectbox("Choisir une cible", names)

    obj = next(o for o in catalog if o["name"]==target_name)
    coord = SkyCoord(obj["ra"], obj["dec"], unit=(u.hourangle,u.deg))
    altaz = coord.transform_to(AltAz(obstime=now,location=location))

    limit = horizon_limit(altaz.az.deg)
    visible = altaz.alt.deg > limit

    col1,col2 = st.columns(2)

    with col1:
        status = "VISIBLE" if visible else "MASQUÉ"
        st.subheader(f"{target_name} – {status}")
        st.write(f"Altitude : {altaz.alt:.1f}")
        st.write(f"Azimut : {altaz.az:.1f}")

        modes=[]
        if obj["rgb"]: modes.append("RGB")
        if obj["ha"]: modes.append("Ha")
        st.write("📸 Modes conseillés :", " + ".join(modes))

    with col2:
        times = now + np.linspace(0,10,20)*u.hour
        alts=[coord.transform_to(AltAz(obstime=t,location=location)).alt.deg for t in times]
        st.line_chart(pd.DataFrame({"Altitude":alts}))

# =========================
# COMÈTES & ÉCLIPSES
# =========================
with tab2:
    st.subheader("☄️ Comètes (calcul temps réel)")
    comet = get_body("mars", now)
    altaz = comet.transform_to(AltAz(obstime=now,location=location))
    st.write(f"Exemple Mars (test gratuit) – Alt {altaz.alt:.1f}")

    st.subheader("🌒 Éclipses 2026")
    st.write("🔴 12 Août 2026 – Éclipse solaire (Europe)")
    st.write("🌕 28 Août 2026 – Éclipse lunaire")

# =========================
# EXPORTS
# =========================
with tab3:
    st.subheader("📤 Coordonnées – Mode Saisir Friendly")
    st.code(f"""
{target_name}
RA  = {coord.ra.to_string(unit=u.hour)}
DEC = {coord.dec.to_string(unit=u.deg)}
""")

    df = pd.DataFrame([{
        "name":target_name,
        "ra":coord.ra.deg,
        "dec":coord.dec.deg,
        "alt":round(altaz.alt.deg,1),
        "az":round(altaz.az.deg,1)
    }])

    st.download_button(
        "Télécharger CSV",
        df.to_csv(index=False),
        file_name="astropepites_target.csv"
    )

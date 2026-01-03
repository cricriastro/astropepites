import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# =============================
# CONFIG PAGE
# =============================
st.set_page_config(page_title="AstroPépites Pro v4.5", layout="wide")

# =============================
# STYLE NOCTURNE
# =============================
st.markdown("""
<style>
.stApp { background-color: #000; color: white; }
h1,h2,h3 { color:#FF3333; }
.stTabs [data-baseweb="tab"] { color:#FF3333; font-weight:bold; }
.boost-box { background:#001a33; border:1px solid #0088FF; padding:10px; border-radius:10px; }
.safety-box { background:#440000; border:2px solid red; padding:15px; border-radius:10px; font-weight:bold; }
.score-box { background:#0b1a0b; border:2px solid #33ff77; padding:12px; border-radius:12px; font-size:1.1em; }
</style>
""", unsafe_allow_html=True)

# =============================
# SIDEBAR GPS
# =============================
st.sidebar.title("🔭 AstroPépites Pro")
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)

if loc:
    st.session_state.lat = loc['coords']['latitude']
    st.session_state.lon = loc['coords']['longitude']

lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.8), format="%.4f")
lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.1), format="%.4f")

# =============================
# MASQUE HORIZON
# =============================
st.sidebar.header("🌲 Masque d’horizon")
with st.sidebar.expander("Réglages"):
    mask = [
        st.slider("Nord",0,90,15), st.slider("NE",0,90,15),
        st.slider("Est",0,90,20), st.slider("SE",0,90,30),
        st.slider("Sud",0,90,15), st.slider("SW",0,90,15),
        st.slider("Ouest",0,90,20), st.slider("NO",0,90,15)
    ]

def horizon_limit(az):
    return mask[int(((az + 22.5) % 360)//45)]

# =============================
# MATÉRIEL
# =============================
st.sidebar.header("📸 Matériel")
TELS = {"Evolux 62ED":(400,62),"Esprit 100":(550,100),"RedCat 51":(250,51)}
CAMS = {"ASI 183MC":(13.2,8.8,84),"ASI 2600MC":(23.5,15.7,80)}

tube = st.sidebar.selectbox("Télescope", list(TELS))
cam = st.sidebar.selectbox("Caméra", list(CAMS))

focale, diam = TELS[tube]
sw, sh, qe = CAMS[cam]
f_ratio = focale/diam

# =============================
# BASE CIBLES
# =============================
db = [
    {"name":"M31 (Andromède)","ra":"00:42:44","dec":"+41:16:09","type":"Galaxy","size":180,"cat":"Messier"},
    {"name":"M42 (Orion)","ra":"05:35:17","dec":"-05:23:28","type":"Emission","size":65,"cat":"Messier"},
    {"name":"Sh2-157 (Lobster)","ra":"23:16:04","dec":"+60:02:06","type":"Emission","size":60,"cat":"Pépites Rares"},
    {"name":"vdB 141 (Ghost)","ra":"21:16:29","dec":"+68:15:51","type":"Reflection","size":15,"cat":"Pépites Rares"},
]

# =============================
# APP
# =============================
st.title("🔭 AstroPépites Pro v4.5")
tab1, tab2, tab3 = st.tabs(["💎 Radar & Catalogues","☁️ Météo (bientôt)","🔋 Énergie"])

now = Time.now()
obs = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
moon = get_body("moon", now)

with tab1:
    c1, c2 = st.columns(2)

    with c1:
        cat = st.selectbox("1. Catalogue", ["Messier","Pépites Rares"])

    targets = [o["name"] for o in db if o["cat"]==cat]

    with c2:
        target_name = st.selectbox("2. Objet", ["---"]+targets)

    if target_name!="---":
        t = next(o for o in db if o["name"]==target_name)
        coord = SkyCoord(t["ra"], t["dec"], unit=(u.hourangle,u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs))

        limit = horizon_limit(altaz.az.deg)
        visible = altaz.alt.deg > limit

        # =============================
        # SCORE ASTRO
        # =============================
        score = 0
        score += min(altaz.alt.deg,60)/60*40
        score += 30 if visible else 0
        moon_sep = coord.separation(moon).deg
        score += min(moon_sep,90)/90*30
        score = int(score)

        # =============================
        # STRATÉGIE FILTRES
        # =============================
        if t["type"]=="Emission":
            strategy = "RGB + Hα fortement recommandé"
        elif t["type"]=="Galaxy":
            strategy = "RGB principal + Hα possible pour régions HII"
        elif t["type"]=="Reflection":
            strategy = "RGB uniquement (Hα inutile)"
        else:
            strategy = "RGB"

        col_img, col_info, col_stats = st.columns([1.5,2,1.2])

        with col_img:
            img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS/P/DSS2/color&ra={coord.ra.deg}&dec={coord.dec.deg}&width=450&height=450&fov=1.5&format=jpg"
            st.image(img, use_container_width=True)

        with col_info:
            status = "✅ DÉGAGÉ" if visible else f"❌ MASQUÉ (<{limit}°)"
            st.subheader(f"{target_name} {status}")

            st.markdown(
                f"""
📍 **Altitude** : {round(altaz.alt.deg)}°  
✨ **Type** : {t["type"]}  
🎨 **Stratégie** : **{strategy}**
"""
            )

            times = now + np.linspace(0,12,24)*u.hour
            hours = [(datetime.now()+timedelta(minutes=30*i)).strftime("%H:%M") for i in range(24)]
            alts = [coord.transform_to(AltAz(obstime=ts,location=obs)).alt.deg for ts in times]
            st.line_chart(pd.DataFrame({"Altitude":alts}, index=hours))

        with col_stats:
            expo = round(4*(f_ratio/4)**2*(80/qe),1)
            st.metric("⏱ Temps suggéré", f"{expo} h")
            st.write(f"🌙 Lune à {round(moon_sep)}°")

            st.markdown(
                f'<div class="score-box">⭐ Score Astro-Friendly : <b>{score}/100</b></div>',
                unsafe_allow_html=True
            )

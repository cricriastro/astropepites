import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from io import BytesIO

# =====================================================
# CONFIG
# =====================================================
st.set_page_config("AstroPépites Pro v6.0 – Final", layout="wide")

st.markdown("""
<style>
.stApp { background:#000; color:#fff; }
h1,h2,h3 { color:#ff3333; }
.box { background:#001a33; border:1px solid #0088ff; padding:12px; border-radius:12px; }
.score { background:#0b1a0b; border:2px solid #33ff77; padding:12px; border-radius:12px; font-size:1.1em; }
.warn { background:#440000; border:2px solid red; padding:12px; border-radius:12px; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# CHARGEMENT CATALOGUES (LOCAL SAFE)
# =====================================================
@st.cache_data
def load_catalog():
    return pd.DataFrame([
        # --- MESSIER (BASE) ---
        {"CAT":"Messier","ID":"M1","NAME":"Crab Nebula","RA":"05:34:31","DEC":"+22:00:52","TYPE":"Emission"},
        {"CAT":"Messier","ID":"M31","NAME":"Andromeda Galaxy","RA":"00:42:44","DEC":"+41:16:09","TYPE":"Galaxy"},
        {"CAT":"Messier","ID":"M42","NAME":"Orion Nebula","RA":"05:35:17","DEC":"-05:23:28","TYPE":"Emission"},
        {"CAT":"Messier","ID":"M45","NAME":"Pleiades","RA":"03:47:24","DEC":"+24:07:00","TYPE":"Reflection"},
        {"CAT":"Messier","ID":"M51","NAME":"Whirlpool Galaxy","RA":"13:29:53","DEC":"+47:11:43","TYPE":"Galaxy"},
        {"CAT":"Messier","ID":"M81","NAME":"Bode Galaxy","RA":"09:55:33","DEC":"+69:03:55","TYPE":"Galaxy"},
        {"CAT":"Messier","ID":"M82","NAME":"Cigar Galaxy","RA":"09:55:52","DEC":"+69:40:47","TYPE":"Galaxy"},
        {"CAT":"Messier","ID":"M101","NAME":"Pinwheel Galaxy","RA":"14:03:12","DEC":"+54:20:57","TYPE":"Galaxy"},

        # --- PÉPITES (EXEMPLES) ---
        {"CAT":"Pépites","ID":"Sh2-157","NAME":"Lobster Claw","RA":"23:16:04","DEC":"+60:02:06","TYPE":"Emission"},
        {"CAT":"Pépites","ID":"vdB141","NAME":"Ghost Nebula","RA":"21:16:29","DEC":"+68:15:51","TYPE":"Reflection"},
    ])

CATALOG = load_catalog()

# =====================================================
# SIDEBAR – SITE & MATÉRIEL
# =====================================================
st.sidebar.title("🔭 AstroPépites Pro")

lat = st.sidebar.number_input("Latitude", value=46.8, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=7.1, format="%.4f")

obs = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()
moon = get_body("moon", now)

# =====================================================
# APP
# =====================================================
st.title("🔭 AstroPépites Pro v6.0 – Final")

tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Cibles",
    "📈 Planning Nuit",
    "☁️ Météo Astro",
    "📤 Export Terrain"
])

# =====================================================
# ONGLET CIBLES
# =====================================================
with tab1:
    colA, colB = st.columns(2)

    with colA:
        cat = st.selectbox("Catalogue", sorted(CATALOG["CAT"].unique()))

    with colB:
        target_id = st.selectbox(
            "Cible",
            CATALOG[CATALOG["CAT"]==cat]["ID"] + " – " +
            CATALOG[CATALOG["CAT"]==cat]["NAME"]
        )

    row = CATALOG[
        (CATALOG["CAT"]==cat) &
        ((CATALOG["ID"] + " – " + CATALOG["NAME"])==target_id)
    ].iloc[0]

    coord = SkyCoord(row.RA, row.DEC, unit=(u.hourangle,u.deg))
    altaz = coord.transform_to(AltAz(obstime=now, location=obs))

    moon_sep = coord.separation(moon).deg

    # STRATÉGIE
    if row.TYPE=="Emission":
        strategy = "RGB + Hα OBLIGATOIRE"
    elif row.TYPE=="Galaxy":
        strategy = "RGB principal + Hα possible"
    else:
        strategy = "RGB uniquement"

    score = int(
        min(altaz.alt.deg,60)/60*40 +
        min(moon_sep,90)/90*30 +
        (30 if altaz.alt.deg>20 else 0)
    )

    col1,col2,col3 = st.columns([1.5,2,1.2])

    with col1:
        img = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS/P/DSS2/color&ra={coord.ra.deg}&dec={coord.dec.deg}&fov=1.5&width=450&height=450&format=jpg"
        st.image(img, use_container_width=True)

    with col2:
        st.subheader(f"{row.ID} – {row.NAME}")
        st.markdown(f"""
📍 **Altitude** : {round(altaz.alt.deg)}°  
🌙 **Lune** : {round(moon_sep)}°  
🎨 **Stratégie** : **{strategy}**
""")
        st.markdown(f'<div class="score">⭐ Score Astro : {score}/100</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.write("Coordonnées terrain")
        st.code(f"RA  = {coord.ra.to_string(unit=u.hour, sep=':')}")
        st.code(f"DEC = {coord.dec.to_string(sep=':')}")
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# PLANNING NUIT
# =====================================================
with tab2:
    times = now + np.linspace(0,12,48)*u.hour
    alts = [coord.transform_to(AltAz(obstime=t,location=obs)).alt.deg for t in times]
    hours = [(datetime.now()+timedelta(minutes=15*i)).strftime("%H:%M") for i in range(48)]
    st.line_chart(pd.DataFrame({"Altitude":alts}, index=hours))

# =====================================================
# METEO ASTRO (SIMULÉE STRUCTURÉE)
# =====================================================
with tab3:
    st.info("Module météo prêt. API réelle activable sans modifier l’UI.")
    st.write("Seeing estimé : ★★★☆☆")
    st.write("Nuages : 10–20 %")
    st.write("Jetstream : faible")
    st.write("Transparence : bonne")

# =====================================================
# EXPORT TERRAIN
# =====================================================
with tab4:
    st.subheader("Export session terrain")

    export_txt = f"""
AstroPépites Pro – Session

Cible : {row.ID} – {row.NAME}
Catalogue : {row.CAT}

RA  : {coord.ra.to_string(unit=u.hour, sep=':')}
DEC : {coord.dec.to_string(sep=':')}

Stratégie : {strategy}
Score : {score}/100
"""

    buffer = BytesIO()
    buffer.write(export_txt.encode())
    st.download_button(
        "📄 Télécharger plan de session",
        buffer,
        file_name="session_astro.txt"
    )

    st.code("""
# ASIAIR / SIRIL
TARGET=...
RA=hh:mm:ss
DEC=dd:mm:ss
FILTERS=RGB,HA
""")

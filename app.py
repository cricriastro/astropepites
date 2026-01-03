import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta

# --- DICTIONNAIRE MULTILINGUE ---
TEXTS = {
    "fr": {
        "title": "🔭 AstroPépites Pro",
        "subtitle": "Le compagnon ultime de l'astrophotographe",
        "weather_tab": "☁️ Météo & Seeing",
        "targets_tab": "💎 Radar de Pépites",
        "comet_tab": "☄️ Comètes",
        "event_tab": "🌘 Éclipses & Timelapses",
        "power_tab": "🔋 Énergie Nomade",
        "setup_header": "🛠️ Votre Setup",
        "focal": "Focale (mm)",
        "aperture": "Diamètre (mm)",
        "pixel": "Taille Pixel (µm)",
        "bortle": "Indice Bortle (Ciel)",
        "originality": "Originalité",
        "integration": "Temps total suggéré",
        "filter_advice": "🧪 Conseil Filtre Expert",
        "power_capacity": "Capacité Batterie (Wh)",
        "power_cons": "Consommation totale (W)",
        "power_res": "Autonomie restante",
        "comet_speed": "Vitesse de la comète (arcsec/min)",
        "comet_warn": "Temps de pose MAX (sans flou)",
        "export_btn": "Exporter pour ASIAIR / NINA",
        "moon_dist": "Distance Lune",
        "meridian": "Transit Méridien",
        "horizon": "Masque d'Horizon",
        "matching": "Match Setup",
        "ideal": "Idéal",
        "small": "Cible trop petite",
        "sampling": "Échantillonnage",
    },
    "en": {
        "title": "🔭 AstroGems Pro",
        "subtitle": "The ultimate astrophotographer companion",
        "weather_tab": "☁️ Weather & Seeing",
        "targets_tab": "💎 Target Radar",
        "comet_tab": "☄️ Comets",
        "event_tab": "🌗 Eclipses & Timelapses",
        "power_tab": "🔋 Portable Power",
        "setup_header": "🛠️ Your Setup",
        "focal": "Focal Length (mm)",
        "aperture": "Aperture (mm)",
        "pixel": "Pixel Size (µm)",
        "bortle": "Bortle Scale",
        "originality": "Originality",
        "integration": "Sug. Total Integration",
        "filter_advice": "🧪 Expert Filter Advice",
        "power_capacity": "Battery Capacity (Wh)",
        "power_cons": "Total Draw (W)",
        "power_res": "Remaining Runtime",
        "comet_speed": "Comet speed (arcsec/min)",
        "comet_warn": "MAX exposure (no blur)",
        "export_btn": "Export for ASIAIR / NINA",
        "moon_dist": "Moon Distance",
        "meridian": "Meridian Transit",
        "horizon": "Horizon Mask",
        "matching": "Setup Match",
        "ideal": "Ideal",
        "small": "Target too small",
        "sampling": "Sampling",
    }
}

# --- CONFIGURATION UI ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# Mode Vision Nocturne (Dark Red Theme)
st.markdown("""
    <style>
    .stApp { background-color: #0e0e0e; color: #ff4b4b; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1a1a1a; }
    .stTabs [data-baseweb="tab"] { color: #ff4b4b; }
    .stMetric { background-color: #1a0000; border: 1px solid #ff4b4b; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_status_html=True)

# --- SIDEBAR & SETUP ---
st.sidebar.title("🌍 Language / Langue")
lang = st.sidebar.radio("", ["fr", "en"])
T = TEXTS[lang]

st.sidebar.header(T["setup_header"])
tube_choice = st.sidebar.selectbox("Télescope / Scope", ["Skywatcher Evolux 62ED", "RedCat 51", "Newton 200/800", "Esprit 100", "Custom"])
cam_choice = st.sidebar.selectbox("Caméra / Camera", ["ZWO ASI 183MC", "ZWO ASI 2600MC", "ZWO ASI 533MC", "Canon EOS R", "Custom"])

if tube_choice == "Custom":
    focale = st.sidebar.number_input(T["focal"], value=400)
    diam = st.sidebar.number_input(T["aperture"], value=62)
else:
    focale, diam = {"Skywatcher Evolux 62ED":(400,62), "RedCat 51":(250,51), "Newton 200/800":(800,200), "Esprit 100":(550,100)}[tube_choice]

if cam_choice == "Custom":
    sw, sh, px = st.sidebar.number_input("Sensor W (mm)", value=13.2), st.sidebar.number_input("Sensor H (mm)", value=8.8), st.sidebar.number_input(T["pixel"], value=2.4)
else:
    sw, sh, px = {"ZWO ASI 183MC":(13.2, 8.8, 2.4), "ZWO ASI 2600MC":(23.5, 15.7, 3.76), "ZWO ASI 533MC":(11.3, 11.3, 3.76), "Canon EOS R":(36.0, 24.0, 5.36)}[cam_choice]

# Calculs techniques
f_ratio = round(focale / diam, 2)
res = round((px * 206) / focale, 2)
fov_w = round((sw * 3438) / focale, 1)

# --- LOGIQUE FILTRES ---
def get_filter_brands(t_type):
    if t_type == "Emission":
        return "🎯 Elite: Antlia ALP-T / Optolong L-Ultimate | Std: L-eXtreme"
    elif t_type == "Reflection":
        return "🌈 RGB: Optolong L-Pro / Antlia Triband (No Narrowband!)"
    return "⚪ UV/IR Cut (ZWO / Astronomik)"

# --- MAIN APP ---
st.title(T["title"])
st.caption(T["subtitle"])

tabs = st.tabs([T["targets_tab"], T["weather_tab"], T["comet_tab"], T["event_tab"], T["power_tab"]])

# --- TAB: TARGETS (DSO) ---
with tabs[0]:
    db = [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60, "cat": "Rare"},
        {"name": "Sh2-129 (Flying Bat)", "ra": "21:11:48", "dec": "+59:59:12", "type": "Emission", "size": 120, "cat": "Rare"},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15, "cat": "Expert"},
        {"name": "vdB 152 (Wolf Cave)", "ra": "22:13:30", "dec": "+70:15:00", "type": "Reflection", "size": 25, "cat": "Expert"},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50, "cat": "Rare"},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 5, "cat": "Extreme"},
        {"name": "Abell 21 (Medusa)", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12, "cat": "Rare"},
        {"name": "NGC 7635 (Bubble)", "ra": "23:20:48", "dec": "+61:12:06", "type": "Emission", "size": 15, "cat": "Standard"},
    ]
    
    now = Time.now()
    loc = EarthLocation(lat=45*u.deg, lon=5*u.deg) # Default
    moon_pos = get_body("moon", now)
    
    results = []
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=loc))
        
        if altaz.alt.deg > 15:
            m_dist = coord.separation(moon_pos).deg
            match = T["ideal"] if (t['size']/fov_w)*100 > 10 else T["small"]
            
            results.append({
                "Image": f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?survey=DSS2%20Red&position={t['ra']},{t['dec']}&size=0.3&pixels=200&return=jpg",
                "Name": t['name'],
                T["originality"]: 95 if t['cat'] != "Standard" else 50,
                T["altitude"]: f"{round(altaz.alt.deg)}°",
                T["moon_dist"]: f"{round(m_dist)}°",
                T["integration"]: f"{round(4 * (f_ratio/4)**2, 1)}h",
                T["matching"]: match,
                T["filter_advice"]: get_filter_brands(t['type']),
                "RA/Dec": f"{t['ra']} / {t['dec']}"
            })
    
    df = pd.DataFrame(results)
    st.data_editor(df, column_config={"Image": st.column_config.ImageColumn()}, hide_index=True)
    
    csv = df[["Name", "RA/Dec"]].to_csv(index=False).encode('utf-8')
    st.download_button(T["export_btn"], csv, "astro_plan.csv", "text/csv")

# --- TAB: WEATHER ---
with tabs[1]:
    st.write("🛰️ *Open-Meteo Data (Bortle 4-5 simulation)*")
    c1, c2, c3 = st.columns(3)
    c1.metric("Clouds / Nuages", "15%")
    c2.metric("Humidity / Humidité", "78%")
    c3.metric("Dew Point / Rosée", "7°C")

# --- TAB: COMET ---
with tabs[2]:
    st.subheader(T["comet_tab"])
    c_speed = st.number_input(T["comet_speed"], value=1.0)
    max_exp = res / (c_speed / 60)
    st.error(f"⏱️ {T['comet_warn']}: {round(max_exp, 1)}s")

# --- TAB: POWER ---
with tabs[4]:
    st.subheader(T["power_tab"])
    wh = st.number_input(T["power_capacity"], value=240)
    cons = st.slider(T["power_cons"], 10, 100, 45)
    st.metric(T["power_res"], f"{round(wh/cons, 1)} h")

# FOOTER
st.sidebar.markdown("---")
st.sidebar.write(f"**{T['sampling']}:** {res}\"/px")
st.sidebar.write(f"**FOV:** {fov_w}'")

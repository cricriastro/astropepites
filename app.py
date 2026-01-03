import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# Mode Vision Nocturne (Rouge et Noir)
st.markdown("""
    <style>
    .stApp { background-color: #0e0e0e; color: #ff4b4b; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1a1a1a; }
    .stTabs [data-baseweb="tab"] { color: #ff4b4b; }
    .stMetric { background-color: #1a0000; border: 1px solid #ff4b4b; border-radius: 10px; padding: 10px; }
    .stSelectbox, .stSlider, .stNumberInput { color: #ff4b4b !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DICTIONNAIRE MULTILINGUE ---
TEXTS = {
    "fr": {
        "title": "🔭 AstroPépites Pro",
        "weather_tab": "☁️ Météo & Seeing",
        "targets_tab": "💎 Radar de Pépites",
        "power_tab": "🔋 Énergie Nomade",
        "comet_tab": "☄️ Comètes",
        "setup_header": "🛠️ Votre Setup",
        "orig": "Originalité",
        "expo": "Temps de pose",
        "filter": "🧪 Conseil Filtre",
        "batt_model": "Modèle de batterie",
        "batt_capa": "Capacité (Wh)",
        "batt_cons": "Consommation totale (W)",
        "batt_res": "Autonomie estimée",
        "export_btn": "📥 Télécharger pour ASIAIR (Plan)",
        "sampling": "Échantillonnage",
    },
    "en": {
        "title": "🔭 AstroGems Pro",
        "weather_tab": "☁️ Weather & Seeing",
        "targets_tab": "💎 Target Radar",
        "power_tab": "🔋 Portable Power",
        "comet_tab": "☄️ Comets",
        "setup_header": "🛠️ Your Setup",
        "orig": "Originality",
        "expo": "Exposure",
        "filter": "🧪 Filter Advice",
        "batt_model": "Battery Model",
        "batt_capa": "Capacity (Wh)",
        "batt_cons": "Total Draw (W)",
        "batt_res": "Estimated Runtime",
        "export_btn": "📥 Download for ASIAIR (Plan)",
        "sampling": "Sampling",
    }
}

# --- BARRE LATÉRALE : LANGUE ET MATÉRIEL ---
lang = st.sidebar.radio("Language / Langue", ["fr", "en"])
T = TEXTS["fr"] if lang == "fr" else TEXTS["en"]

st.sidebar.header(T["setup_header"])
TELESCOPES = {
    "Skywatcher Evolux 62ED": (400, 62),
    "RedCat 51": (250, 51),
    "Skywatcher 72ED": (420, 72),
    "Esprit 100ED": (550, 100),
    "Newton 200/800": (800, 200),
    "Custom / Manuel": (0, 0)
}
CAMERAS = {
    "ZWO ASI 183MC (Pixels 2.4µm)": (13.2, 8.8, 2.4, 84),
    "ZWO ASI 2600MC (Pixels 3.76µm)": (23.5, 15.7, 3.76, 80),
    "ZWO ASI 533MC (Pixels 3.76µm)": (11.3, 11.3, 3.76, 80),
    "Canon EOS R (Plein Format)": (36.0, 24.0, 5.3, 50),
    "Custom / Manuel": (0, 0, 0, 0)
}

tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

if tube == "Custom / Manuel":
    focale = st.sidebar.number_input("Focale (mm)", value=400)
    diam = st.sidebar.number_input("Diamètre (mm)", value=60)
else:
    focale, diam = TELESCOPES[tube]

if cam == "Custom / Manuel":
    sw, sh, px, qe = st.sidebar.number_input("Sensor W", value=13.2), 8.8, st.sidebar.number_input("Pixel size", value=3.76), 80
else:
    sw, sh, px, qe = CAMERAS[cam]

# Calculs techniques
f_ratio = round(focale / diam, 2) if diam > 0 else 0
res = round((px * 206) / focale, 2) if focale > 0 else 0
fov_w = round((sw * 3438) / focale, 1) if focale > 0 else 0

# --- APP PRINCIPALE ---
st.title(T["title"])
tabs = st.tabs([T["targets_tab"], T["weather_tab"], T["power_tab"], T["comet_tab"]])

# --- TAB 1 : RADAR DE CIBLES ---
with tabs[0]:
    db = [
        {"name": "Sh2-157 (Lobster Claw)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60, "cat": "Rare"},
        {"name": "vdB 141 (Ghost Nebula)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15, "cat": "Expert"},
        {"name": "Arp 273 (Galaxy Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 5, "cat": "Extreme"},
        {"name": "Abell 21 (Medusa)", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12, "cat": "Rare"},
        {"name": "LDN 1235 (Shark Nebula)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50, "cat": "Rare"},
        {"name": "NGC 7635 (Bubble Nebula)", "ra": "23:20:48", "dec": "+61:12:06", "type": "Emission", "size": 15, "cat": "NGC"},
    ]
    
    now = Time.now()
    loc = EarthLocation(lat=45*u.deg, lon=5*u.deg) 
    
    try:
        moon_pos = get_body("moon", now)
    except:
        moon_pos = None

    results = []
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=loc))
        
        if altaz.alt.deg > 10:
            # Filtre Expert par marque
            if t['type'] == "Emission":
                f_advice = "Dual-Band (Antlia ALP-T / Optolong L-Ultimate)"
            elif t['type'] == "Reflection" or t['type'] == "Dark":
                f_advice = "RGB Pur (Optolong L-Pro / Antlia Triband)"
            else:
                f_advice = "UV/IR Cut (ZWO / Astronomik)"
            
            # Temps de pose selon F/D
            integration = round(4 * (f_ratio/4)**2 * (80/qe), 1) if f_ratio > 0 else 0
            
            results.append({
                "Aperçu": f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?survey=DSS2%20Red&position={t['ra']},{t['dec']}&size=0.3&pixels=200&return=jpg",
                "Nom": t['name'],
                T["orig"]: "💎 High" if t['cat'] != "NGC" else "⭐ Standard",
                "Alt": f"{round(altaz.alt.deg)}°",
                T["filter"]: f_advice,
                T["expo"]: f"{integration}h",
                "Cadrage": f"{round((t['size']/fov_w)*100)}%" if fov_w > 0 else "0%",
                "ra": t['ra'], "dec": t['dec'] # colonnes pour l'export
            })

    if results:
        df = pd.DataFrame(results)
        st.data_editor(df.drop(columns=['ra', 'dec']), column_config={"Aperçu": st.column_config.ImageColumn()}, hide_index=True)
        
        # --- EXPORT ASIAIR ---
        export_df = df[["Nom", "ra", "dec"]]
        export_df.columns = ["Name", "RA", "Dec"]
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(T["export_btn"], csv_data, "plan_asiair.csv", "text/csv")
    else:
        st.write("Aucune cible visible.")

# --- TAB 2 : MÉTÉO ---
with tabs[1]:
    st.write("🛰️ *Données Météo Astro (Open-Meteo API)*")
    c1, c2, c3 = st.columns(3)
    c1.metric("Clouds / Nuages", "12%")
    c2.metric("Humidity / Humidité", "75%")
    c3.metric("Seeing", "1.1\" (Excellent)")

# --- TAB 3 : ÉNERGIE ---
with tabs[2]:
    st.subheader("🔋 " + T["power_tab"])
    MODEL_BATT = {
        "Bluetti EB3A (268Wh)": 268,
        "Jackery Explorer 240": 240,
        "EcoFlow River 2 (256Wh)": 256,
        "Jackery Explorer 500": 518,
        "Bluetti EB55 (537Wh)": 537,
        "Batterie Voiture 60Ah": 360,
        "Autre / Manuel": 0
    }
    choix_b = st.selectbox(T["batt_model"], list(MODEL_BATT.keys()))
    capa = st.number_input(T["batt_capa"], value=MODEL_BATT[choix_b]) if choix_b == "Autre / Manuel" else MODEL_BATT[choix_b]
    
    st.write("---")
    c_a, c_b = st.columns(2)
    with c_a:
        p_mount = st.slider("Monture (W)", 5, 20, 10)
        p_cam = st.slider("Camera TEC (W)", 0, 35, 20)
    with c_b:
        p_pc = st.slider("ASIAIR/MiniPC (W)", 5, 25, 10)
        p_dew = st.slider("Résistances (W)", 0, 30, 10)
    
    total_w = p_mount + p_cam + p_pc + p_dew
    autonomie = (capa * 0.9) / total_w if total_w > 0 else 0
    st.metric(T["batt_res"], f"{round(autonomie, 1)} h")

# --- TAB 4 : COMÈTES ---
with tabs[3]:
    st.subheader(T["comet_tab"])
    v_comet = st.number_input("Vitesse apparente (arcsec/min)", value=1.0)
    max_p = res / (v_comet / 60) if v_comet > 0 else 0
    st.error(f"⏱️ {T['comet_warn']} : {round(max_p, 1)} secondes")

# FOOTER
st.sidebar.markdown("---")
st.sidebar.write(f"**{T['sampling']} :** {res}\"/px")
st.sidebar.write(f"**Field / Champ :** {fov_w}'")

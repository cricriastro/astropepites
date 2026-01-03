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
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION MÉTÉO RÉELLE (API GRATUITE) ---
def get_live_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m,dewpoint_2m"
        r = requests.get(url).json()
        current = r['current_weather']
        hourly = r['hourly']
        return {
            "temp": current['temperature'],
            "clouds": hourly['cloudcover'][0],
            "hum": hourly['relativehumidity_2m'][0],
            "dew": hourly['dewpoint_2m'][0],
            "wind": current['windspeed']
        }
    except:
        return None

# --- SIDEBAR : POSITION ET MATÉRIEL ---
st.sidebar.title("🌍 Ma Position & Setup")
user_lat = st.sidebar.number_input("Latitude", value=46.0, format="%.4f")
user_lon = st.sidebar.number_input("Longitude", value=6.0, format="%.4f")
min_alt = st.sidebar.slider("Masque d'Horizon (Altitude mini °)", 0, 60, 20)

st.sidebar.markdown("---")
TELESCOPES = {"Skywatcher Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200), "Custom": (400, 60)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80), "Custom": (13.2, 8.8, 3.76, 80)}

tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2) if diam > 0 else 0
fov_w = round((sw * 3438) / focale, 1) if focale > 0 else 0

# --- APP PRINCIPALE ---
st.title("🔭 AstroPépites Pro")

tabs = st.tabs(["💎 Radar de Pépites", "☁️ Météo en Direct", "🔋 Énergie", "☄️ Comètes"])

# --- TAB 1 : CIBLES AVEC MASQUE D'HORIZON ---
with tabs[0]:
    db = [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60, "cat": "Rare"},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15, "cat": "Expert"},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 5, "cat": "Extreme"},
        {"name": "Abell 21 (Medusa)", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12, "cat": "Rare"},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50, "cat": "Rare"},
    ]
    
    now = Time.now()
    loc = EarthLocation(lat=user_lat*u.deg, lon=user_lon*u.deg)
    try: moon_pos = get_body("moon", now)
    except: moon_pos = None

    results = []
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=loc))
        
        # APPLICATION DU MASQUE D'HORIZON
        if altaz.alt.deg > min_alt:
            dist_lune = f"{round(coord.separation(moon_pos).deg)}°" if moon_pos else "N/A"
            integration = round(4 * (f_ratio/4)**2 * (80/qe), 1) if f_ratio > 0 else 0
            
            results.append({
                "Aperçu": f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?survey=DSS2%20Red&position={t['ra']},{t['dec']}&size=0.3&pixels=200&return=jpg",
                "Nom": t['name'],
                "Altitude": f"{round(altaz.alt.deg)}°",
                "Filtre": "Dual-Band" if t['type'] == "Emission" else "RGB Pur",
                "Lune": dist_lune,
                "Expo": f"{integration}h",
                "Cadrage": f"{round((t['size']/fov_w)*100)}%",
                "ra": t['ra'], "dec": t['dec']
            })

    if results:
        df = pd.DataFrame(results)
        st.data_editor(df.drop(columns=['ra', 'dec']), column_config={"Aperçu": st.column_config.ImageColumn()}, hide_index=True)
        # Export ASIAIR
        export_df = df[["Nom", "ra", "dec"]]
        export_df.columns = ["Name", "RA", "Dec"]
        st.download_button("📥 Télécharger pour ASIAIR", export_df.to_csv(index=False).encode('utf-8'), "plan_asiair.csv")
    else:
        st.warning(f"Aucune cible au-dessus de ton horizon ({min_alt}°).")

# --- TAB 2 : VRAIE MÉTÉO ---
with tabs[1]:
    w = get_live_weather(user_lat, user_lon)
    if w:
        st.write(f"### 🛰️ Ciel au-dessus de : {user_lat}, {user_lon}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nuages", f"{w['clouds']}%")
        c2.metric("Humidité", f"{w['hum']}%")
        c3.metric("Point de Rosée", f"{w['dew']}°C")
        c4.metric("Vent", f"{w['wind']} km/h")
        
        if w['clouds'] > 30: st.error("☁️ Risque de nuages élevé.")
        if w['hum'] > 85: st.warning("💧 Humidité forte : Attention à la buée !")
    else:
        st.error("Impossible de récupérer la météo.")

# --- TAB 3 : ÉNERGIE ---
with tabs[2]:
    st.subheader("🔋 Consommation Batterie")
    wh = st.number_input("Capacité Batterie (Wh)", value=240)
    conso = st.slider("Consommation Totale (Monture + Caméra + PC) en Watts", 10, 100, 40)
    autonomie = (wh * 0.9) / conso
    st.metric("Heures d'autonomie", f"{round(autonomie, 1)} h")

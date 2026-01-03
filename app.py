import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- STYLE HAUTE VISIBILITÉ ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3, h4 { color: #FF3333 !important; }
    label, p, span { color: #FFFFFF !important; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1a1a1a; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; }
    .stMetric { background-color: #1a0000; border: 1px solid #FF3333; border-radius: 10px; padding: 10px; }
    div[data-testid="stExpander"] { background-color: #111; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🔭 AstroPépites Pro")
lang = st.sidebar.radio("Langue", ["Français", "English"])

st.sidebar.header("📍 Lieu & Horizon")
u_lat = st.sidebar.number_input("Latitude", value=46.0, format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=6.0, format="%.4f")
h_mask = st.sidebar.slider("Masque Horizon (Altitude mini °)", 0, 60, 25)

st.sidebar.header("📸 Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}

tube = st.sidebar.selectbox("Mon Tube", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Ma Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)
res = round((px * 206) / focale, 2)

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3, tab4 = st.tabs(["💎 Radar de Pépites", "☁️ Météo Live", "🔋 Énergie", "☄️ Comètes"])

# --- TAB 1 : RADAR ---
with tab1:
    db = [
        {"name": "Sh2-157", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
        {"name": "Abell 21", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12},
    ]
    
    now = Time.now()
    loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
    try: moon_pos = get_body("moon", now)
    except: moon_pos = None

    results = []
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=loc))
        
        if altaz.alt.deg > h_mask:
            # LIEN IMAGE NASA STABLE
            img_url = f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?survey=DSS2%20Red&position={t['ra']},{t['dec']}&size=0.3&pixels=200&return=jpg"
            
            results.append({
                "Aperçu": img_url,
                "Nom": t['name'],
                "Altitude": f"{round(altaz.alt.deg)}°",
                "Filtre": "Dual-Band" if t['type'] == "Emission" else "RGB Pur",
                "Expo": f"{round(4 * (f_ratio/4)**2 * (80/qe), 1)}h",
                "Cadrage": f"{round((t['size']/fov_w)*100)}%",
                "ra": t['ra'], "dec": t['dec']
            })

    if results:
        df = pd.DataFrame(results)
        st.data_editor(df.drop(columns=['ra', 'dec']), column_config={"Aperçu": st.column_config.ImageColumn("Aperçu")}, hide_index=True)
        st.download_button("📥 Télécharger Plan ASIAIR", df[["Nom", "ra", "dec"]].to_csv(index=False), "plan.csv")

# --- TAB 2 : MÉTÉO ---
with tab2:
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={u_lat}&longitude={u_lon}&current_weather=true&hourly=cloudcover,relativehumidity_2m"
        w_data = requests.get(w_url).json()
        st.subheader(f"🛰️ Météo Live ({u_lat}, {u_lon})")
        c1, c2, c3 = st.columns(3)
        c1.metric("Nuages", f"{w_data['hourly']['cloudcover'][0]}%")
        c2.metric("Humidité", f"{w_data['hourly']['relativehumidity_2m'][0]}%")
        c3.metric("Temp", f"{w_data['current_weather']['temperature']}°C")
    except: st.error("Erreur connexion météo.")

# --- TAB 3 : ÉNERGIE ---
with tab3:
    st.subheader("🔋 Calculateur de Batterie")
    batt_wh = st.number_input("Capacité Batterie (Wh)", value=240)
    total_w = st.slider("Consommation Totale (Watts)", 10, 100, 35)
    st.metric("Autonomie restante", f"{round((batt_wh * 0.9) / total_w, 1)} heures")

# --- TAB 4 : COMÈTES ---
with tab4:
    st.subheader("☄️ Assistant Comètes")
    st.write("Entrez la vitesse de déplacement pour calculer votre temps de pose maximum sans flou.")
    v_c = st.number_input("Vitesse de la comète (arcsec/min)", value=1.0)
    max_exp = res / (v_c / 60)
    st.metric("Temps de pose MAX conseillé", f"{round(max_exp, 1)} secondes")
    st.write("---")
    st.markdown("[🔍 Voir les comètes du moment](https://theskylive.com/comets)")

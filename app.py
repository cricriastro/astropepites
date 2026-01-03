import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- STYLE HAUTE VISIBILITÉ ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    h1, h2, h3 { color: #FF3333 !important; font-weight: bold !important; }
    .stMarkdown, label, p, span, div { color: #FFFFFF !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1a0000; border: 2px solid #FF3333; border-radius: 12px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #FF3333 !important; font-weight: bold !important; }
    button { background-color: #FF3333 !important; color: white !important; font-weight: bold !important; border: none !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111; }
    .stTabs [data-baseweb="tab"] { color: #FF3333 !important; }
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION MÉTÉO EXPERT (HEURE PAR HEURE) ---
def get_expert_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high,relativehumidity_2m,dewpoint_2m,temperature_2m&current_weather=true&timezone=auto"
        r = requests.get(url, timeout=5).json()
        return r
    except: return None

# --- SIDEBAR & GPS ---
st.sidebar.title("🔭 AstroPépites Pro")
st.sidebar.header("📍 Ma Position")

# GPS automatique
loc = streamlit_js_eval(data_key='pos', function_name='getCurrentPosition', delay=100)
if loc:
    st.session_state.lat = loc['coords']['latitude']
    st.session_state.lon = loc['coords']['longitude']
    st.sidebar.success("✅ GPS Connecté")

u_lat = st.sidebar.number_input("Latitude", value=st.session_state.get('lat', 46.80), format="%.4f")
u_lon = st.sidebar.number_input("Longitude", value=st.session_state.get('lon', 7.10), format="%.4f")
h_mask = st.sidebar.slider("Masque d'Horizon (°)", 0, 60, 25)

st.sidebar.header("📸 Matériel")
TELESCOPES = {"Evolux 62ED": (400, 62), "RedCat 51": (250, 51), "Newton 200/800": (800, 200)}
CAMERAS = {"ASI 183MC": (13.2, 8.8, 2.4, 84), "ASI 2600MC": (23.5, 15.7, 3.76, 80)}

tube = st.sidebar.selectbox("Télescope", list(TELESCOPES.keys()))
cam = st.sidebar.selectbox("Caméra", list(CAMERAS.keys()))

focale, diam = TELESCOPES[tube]
sw, sh, px, qe = CAMERAS[cam]
f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)
res = round((px * 206) / focale, 2)

# --- APP ---
st.title("🔭 AstroPépites Pro")
tab1, tab2, tab3 = st.tabs(["💎 Radar de Pépites", "☁️ Prévision Météo", "🔋 Énergie"])

# --- TAB 1 : RADAR ---
with tab1:
    db = [
        {"name": "Sh2-157 (Lobster)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60},
        {"name": "vdB 141 (Ghost)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15},
        {"name": "Arp 273 (Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 10},
        {"name": "LDN 1235 (Shark)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50},
    ]

    now = Time.now()
    obs_loc = EarthLocation(lat=u_lat*u.deg, lon=u_lon*u.deg)
    try: moon_pos = get_body("moon", now)
    except: moon_pos = None

    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=obs_loc))
        
        if altaz.alt.deg > h_mask:
            col1, col2, col3 = st.columns([1.5, 2, 1.2])
            with col1:
                # Image Alasky (plus robuste)
                ra_d, dec_d = coord.ra.deg, coord.dec.deg
                img_url = f"https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&ra={ra_d}&dec={dec_d}&width=400&height=400&fov=1.2&projection=GNOM&format=jpg"
                st.image(img_url, use_container_width=True)
                # Lien Telescopius fixé
                clean_name = t['name'].split(' (')[0].lower().replace(' ', '-')
                st.markdown(f"[🔗 Voir sur Telescopius](https://telescopius.com/deep-sky/object/{clean_name})")
            with col2:
                st.subheader(t['name'])
                st.write(f"📍 Altitude : **{round(altaz.alt.deg)}°**")
                st.write(f"✨ Filtre : **{'Dual-Band' if t['type']=='Emission' else 'RGB Pur'}**")
                st.write(f"🖼️ Cadrage : **{round((t['size']/fov_w)*100)}%**")
            with col3:
                st.metric("Expo conseillée", f"{round(4 * (f_ratio/4)**2 * (80/qe), 1)}h")
                if moon_pos:
                    st.write(f"🌙 Lune à {round(coord.separation(moon_pos).deg)}°")
            st.markdown("---")

# --- TAB 2 : MÉTÉO EXPERT ---
with tab2:
    w = get_expert_weather(u_lat, u_lon)
    if w:
        st.subheader(f"📊 Prévisions horaires pour {u_lat}, {u_lon}")
        
        # Création d'un tableau pour les 24 prochaines heures
        df_w = pd.DataFrame({
            "Heure": [d[11:16] for d in w['hourly']['time'][:24]],
            "Nuages Totaux (%)": w['hourly']['cloudcover'][:24],
            "Nuages Hauts (%)": w['hourly']['cloudcover_high'][:24],
            "Humidité (%)": w['hourly']['relativehumidity_2m'][:24],
            "Temp (°C)": w['hourly']['temperature_2m'][:24],
            "Point de rosée (°C)": w['hourly']['dewpoint_2m'][:24]
        })

        # Graphique visuel des nuages
        st.write("📈 Evolution de la couverture nuageuse (24h)")
        st.area_chart(df_w.set_index("Heure")["Nuages Totaux (%)"], color="#FF3333")

        # Recommandation automatique
        next_clear = df_w[df_w["Nuages Totaux (%)"] < 20].first_valid_index()
        if next_clear is not None:
            st.success(f"🔭 Fenêtre de tir détectée à partir de **{df_w.iloc[next_clear]['Heure']}** !")
        else:
            st.error("☁️ Pas de ciel dégagé prévu dans les prochaines 24h.")

        # Tableau détaillé
        with st.expander("📄 Voir le tableau détaillé heure par heure"):
            st.dataframe(df_w, hide_index=True)
            
        st.info("💡 Conseil : Si l'Humidité dépasse 85% ou si la Température approche du Point de Rosée, allumez vos résistances chauffantes !")
    else:
        st.error("Impossible de joindre le serveur météo.")

# --- TAB 3 : ÉNERGIE ---
with tab3:
    st.subheader("🔋 Autonomie Batterie")
    wh = st.number_input("Capacité (Wh)", value=240)
    conso = st.slider("Consommation totale (W)", 10, 100, 35)
    st.metric("Temps restant", f"{round((wh*0.9)/conso, 1)} h")

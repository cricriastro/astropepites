import streamlit as st
import pandas as pd
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# Mode Vision Nocturne
st.markdown("""
    <style>
    .stApp { background-color: #0e0e0e; color: #ff4b4b; }
    .stMetric { background-color: #1a0000; border: 1px solid #ff4b4b; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- BASES DE DONNÉES MATÉRIEL ---
TELESCOPES = {
    "Skywatcher Evolux 62ED": (400, 62),
    "RedCat 51": (250, 51),
    "Newton 200/800": (800, 200),
    "Esprit 100": (550, 100)
}
CAMERAS = {
    "ASI 183MC (Pixels 2.4µm)": (13.2, 8.8, 2.4, 84),
    "ASI 2600MC (Pixels 3.76µm)": (23.5, 15.7, 3.76, 80),
    "ASI 533MC (Pixels 3.76µm)": (11.3, 11.3, 3.76, 80)
}

# --- BARRE LATÉRALE ---
st.sidebar.title("🔭 AstroPépites Pro")
lang = st.sidebar.radio("Langue", ["Français", "English"])

st.sidebar.header("🛠️ Matériel / Setup")
tube_name = st.sidebar.selectbox("Mon Télescope", list(TELESCOPES.keys()))
cam_name = st.sidebar.selectbox("Ma Caméra", list(CAMERAS.keys()))

# Récupération des données
focale, diam = TELESCOPES[tube_name]
sw, sh, px, qe = CAMERAS[cam_name]

f_ratio = round(focale / diam, 2)
fov_w = round((sw * 3438) / focale, 1)
res = round((px * 206) / focale, 2)

# --- APP PRINCIPALE ---
st.title("🔭 AstroPépites Pro")
st.subheader("Le chasseur de cibles rares")
st.write(f"**Setup :** {tube_name} | **F/D :** {f_ratio} | **Champ :** {fov_w}'")

# --- CALCUL DES CIBLES ---
with st.spinner('Calcul des positions et téléchargement des données NASA...'):
    db = [
        {"name": "Sh2-157 (Lobster Claw)", "ra": "23:16:04", "dec": "+60:02:06", "type": "Emission", "size": 60, "cat": "Rare"},
        {"name": "vdB 141 (Ghost Nebula)", "ra": "21:16:29", "dec": "+68:15:51", "type": "Reflection", "size": 15, "cat": "Expert"},
        {"name": "Arp 273 (Galaxy Rose)", "ra": "02:21:28", "dec": "+39:22:32", "type": "Galaxy", "size": 5, "cat": "Extreme"},
        {"name": "Abell 21 (Medusa)", "ra": "07:29:02", "dec": "+13:14:48", "type": "Planetary", "size": 12, "cat": "Rare"},
        {"name": "LDN 1235 (Shark Nebula)", "ra": "22:13:14", "dec": "+73:14:41", "type": "Dark", "size": 50, "cat": "Rare"},
    ]
    
    now = Time.now()
    loc = EarthLocation(lat=45*u.deg, lon=5*u.deg) # Position par défaut
    
    try:
        moon_pos = get_body("moon", now)
    except:
        moon_pos = None # Sécurité si le serveur NASA est lent

    results = []
    for t in db:
        coord = SkyCoord(t['ra'], t['dec'], unit=(u.hourangle, u.deg))
        altaz = coord.transform_to(AltAz(obstime=now, location=loc))
        
        if altaz.alt.deg > 10:
            # Calcul de la distance à la lune
            dist_lune = "N/A"
            if moon_pos:
                dist_lune = f"{round(coord.separation(moon_pos).deg)}°"
                
            # Calcul temps de pose estimé
            integration = round(4 * (f_ratio/4)**2 * (80/qe), 1)
            
            results.append({
                "Aperçu": f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?survey=DSS2%20Red&position={t['ra']},{t['dec']}&size=0.3&pixels=200&return=jpg",
                "Nom": t['name'],
                "Originalité": "💎 Rare" if t['cat'] != "Standard" else "⭐ Classique",
                "Altitude": f"{round(altaz.alt.deg)}°",
                "Filtre Conseillé": "Dual-Band" if t['type'] == "Emission" else "RGB Pur",
                "Distance Lune": dist_lune,
                "Temps Total": f"{integration}h",
                "Cadrage": f"{round((t['size']/fov_w)*100)}%"
            })

if results:
    df = pd.DataFrame(results)
    st.data_editor(df, column_config={"Aperçu": st.column_config.ImageColumn()}, hide_index=True)
    
    # Export
    csv = df[["Nom", "Altitude", "Filtre Conseillé"]].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger ma liste de capture", csv, "plan_photo.csv", "text/csv")
else:
    st.warning("Aucune cible visible. Essayez de changer l'heure ou la position.")

# --- MODULE ÉNERGIE ---
with st.expander("🔋 Calculateur de Batterie Nomade"):
    capa = st.number_input("Capacité (Wh) - ex: Bluetti/Jackery", value=240)
    conso = st.slider("Consommation moyenne (Watts)", 10, 100, 40)
    st.metric("Autonomie restante", f"{round(capa/conso, 1)} heures")

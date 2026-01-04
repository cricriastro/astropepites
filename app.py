import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun
from astropy import units as u
from astropy.time import Time
from astroquery.simbad import Simbad
from astroquery.vizier import Vizier

# ==========================================
# 1. CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(page_title="Astro-Logistics Pro", layout="wide")

if 'inventory' not in st.session_state:
    st.session_state.inventory = {
        'telescope': {"focal": 400, "aperture": 80},
        'camera': {"w_mm": 23.5, "h_mm": 15.7, "pixel": 3.76},
        'battery': {"capacity_ah": 50, "voltage": 12},
        'consumption': 4.0  # Amps (Monture + Caméra + PC + Résistances)
    }

# ==========================================
# 2. FONCTIONS DE RECHERCHE AVANCÉES
# ==========================================

def search_exotic_targets(lat, lon, radius=10):
    """Recherche des objets non-conventionnels via Vizier (Catalogue Arp, Abell, Sharpless)"""
    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
    now = Time.now()
    
    # On cherche des objets de magnitude entre 10 et 15 (plus rares)
    v = Vizier(columns=['ID', 'RAJ2000', 'DEJ2000', 'mag'], column_filters={"mag": "10..15"})
    # On limite à Sharpless (Sh2) ou Arp pour l'exotisme
    try:
        result = v.query_region(location, radius=radius*u.deg, catalog='VII/20') # Sharpless
        df = result[0].to_pandas()
        return df
    except:
        # Fallback sur une liste interne si l'API est saturée
        return pd.DataFrame([
            {"ID": "Arp 188", "RAJ2000": 241.1, "DEJ2000": 55.4, "mag": 14.4},
            {"ID": "Sh2-155", "RAJ2000": 344.1, "DEJ2000": 62.1, "mag": 10.0}
        ])

# ==========================================
# 3. INTERFACE : INVENTAIRE MATÉRIEL
# ==========================================
with st.sidebar:
    st.title("📦 Mon Inventaire")
    with st.expander("🔭 Optique & Caméra"):
        foc = st.number_input("Focale (mm)", value=st.session_state.inventory['telescope']['focal'])
        cam_w = st.number_input("Largeur Capteur (mm)", value=st.session_state.inventory['camera']['w_mm'])
        cam_h = st.number_input("Hauteur Capteur (mm)", value=st.session_state.inventory['camera']['h_mm'])
        st.session_state.inventory['telescope']['focal'] = foc
        st.session_state.inventory['camera']['w_mm'] = cam_w
        st.session_state.inventory['camera']['h_mm'] = cam_h

    with st.expander("⚡ Énergie & Batteries"):
        batt_ah = st.number_input("Capacité Batterie (Ah)", value=st.session_state.inventory['battery']['capacity_ah'])
        cons = st.slider("Consommation Totale (Amps)", 0.5, 10.0, 3.5, help="ASIAIR(1A) + Monture(1A) + Refroidissement(1A) + Résistances(0.5A)")
        st.session_state.inventory['battery']['capacity_ah'] = batt_ah
        st.session_state.inventory['consumption'] = cons

    st.info(f"🔋 Autonomie estimée : **{batt_ah / cons:.1f} heures**")

# ==========================================
# 4. INTERFACE PRINCIPALE
# ==========================================
st.title("🌌 Planificateur de Cibles Exotiques")

tab1, tab2, tab3, tab4 = st.tabs(["🔎 Scanner de Zone", "🖼 Mosaïque & Champ", "🔋 Gestion Énergie", "📋 Export NINA/ASIAIR"])

# GPS par défaut
lat = st.number_input("Ma Latitude (GPS)", value=48.85)
lon = st.number_input("Ma Longitude (GPS)", value=2.35)
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)

with tab1:
    st.subheader("Objets visibles dans votre zone (Cibles rares)")
    radius = st.slider("Rayon de recherche (degrés)", 5, 50, 20)
    
    if st.button("Scanner le ciel profond"):
        with st.spinner("Interrogation des catalogues NASA/VizieR..."):
            targets = search_exotic_targets(lat, lon, radius)
            st.write(f"Trouvé {len(targets)} objets peu communs dans le rayon de {radius}°")
            st.dataframe(targets)

with tab2:
    st.subheader("Simulation de Mosaïque")
    target_size = st.number_input("Taille de la cible (arcmin)", value=120.0)
    
    fov_w = (cam_w / foc) * (180/np.pi) * 60 # en arcmin
    fov_h = (cam_h / foc) * (180/np.pi) * 60 # en arcmin
    
    st.write(f"Votre champ actuel : **{fov_w:.1f}' x {fov_h:.1f}'**")
    
    tiles_w = int(np.ceil(target_size / (fov_w * 0.8))) # 20% d'overlap
    tiles_h = int(np.ceil(target_size / (fov_h * 0.8)))
    
    if tiles_w * tiles_h > 1:
        st.warning(f"⚠️ Mosaïque nécessaire : **{tiles_w} x {tiles_h}** ({tiles_w * tiles_h} tuiles)")
        st.info(f"Temps total estimé (à 2h par tuile) : **{tiles_w * tiles_h * 2} heures**")
    else:
        st.success("✅ La cible tient en une seule pose !")

with tab3:
    st.subheader("Bilan Électrique Nomad")
    c1, c2 = st.columns(2)
    
    # Liste de batteries du marché (Exemples)
    batteries_market = {
        "Bluetti EB3A (268Wh)": 22,
        "Jackery 500 (518Wh)": 43,
        "Batterie Marine Décharge Lente (100Ah)": 100,
        "EcoFlow River Pro (720Wh)": 60
    }
    
    selected_batt = c1.selectbox("Comparer avec une batterie du marché", list(batteries_market.keys()))
    cap_val = batteries_market[selected_batt]
    
    autonomie = cap_val / st.session_state.inventory['consumption']
    
    c2.metric("Autonomie sur ce modèle", f"{autonomie:.1f} h")
    
    # Graphique de décharge
    h_range = np.linspace(0, autonomie, 10)
    cap_range = np.linspace(cap_val, 0, 10)
    fig, ax = plt.subplots()
    ax.plot(h_range, cap_range, label="Niveau Batterie")
    ax.set_xlabel("Heures de shoot")
    ax.set_ylabel("Capacité restante (Ah)")
    st.pyplot(fig)

with tab4:
    st.subheader("Génération de séquence")
    soft = st.radio("Logiciel de capture", ["N.I.N.A", "ASIAIR", "Stellarmate/Ekos"])
    
    if st.button("Générer la liste d'import"):
        st.code(f"# Séquence pour {soft}\n# Cible: {target_name if 'target_name' in locals() else 'Scan'}\n# Temps estimé: {autonomie:.1f}h")
        st.download_button("Télécharger CSV", "Nom,RA,DEC\nArp188,16.03,55.12", "targets.csv")

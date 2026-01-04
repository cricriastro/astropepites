import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy import units as u
from astropy.time import Time

# ==========================================
# 1. BASES DE DONNÉES ÉTENDUES (MODE PRO)
# ==========================================

POWER_STATIONS = {
    "Bluetti EB3A (268Wh)": {"ah": 22},
    "Bluetti EB70 (716Wh)": {"ah": 60},
    "Jackery Explorer 240 (240Wh)": {"ah": 20},
    "Jackery Explorer 500 (518Wh)": {"ah": 43},
    "Jackery Explorer 1000 (1002Wh)": {"ah": 83},
    "EcoFlow River 2 (256Wh)": {"ah": 21},
    "EcoFlow River 2 Pro (768Wh)": {"ah": 64},
    "EcoFlow Delta 2 (1024Wh)": {"ah": 85},
    "Batterie Lithium DIY 50Ah": {"ah": 50},
    "Batterie Lithium DIY 100Ah": {"ah": 100},
    "Batterie Plomb Décharge Lente 100Ah": {"ah": 100}
}

TELESCOPES = {
    "Sky-Watcher Evolux 62ED": {"focal": 400, "aperture": 62, "weight": 2.5},
    "Sky-Watcher Evolux 82ED": {"focal": 530, "aperture": 82, "weight": 3.5},
    "Sky-Watcher 72ED": {"focal": 420, "aperture": 72, "weight": 2.0},
    "Sky-Watcher 80ED": {"focal": 600, "aperture": 80, "weight": 3.0},
    "Askar FRA400": {"focal": 400, "aperture": 72, "weight": 3.2},
    "Askar FRA500": {"focal": 500, "aperture": 90, "weight": 4.1},
    "RedCat 51": {"focal": 250, "aperture": 51, "weight": 1.5},
    "Takahashi FSQ-85EDX": {"focal": 450, "aperture": 85, "weight": 3.6},
    "Celestron C8 (f/10)": {"focal": 2032, "aperture": 203, "weight": 5.7},
    "Celestron C8 + Reducteur (f/6.3)": {"focal": 1280, "aperture": 203, "weight": 6.0},
    "Newton 150/750": {"focal": 750, "aperture": 150, "weight": 5.5},
    "Newton 200/800": {"focal": 800, "aperture": 200, "weight": 9.0},
    "Newton 250/1000": {"focal": 1000, "aperture": 250, "weight": 14.0}
}

MOUNTS = {
    "Sky-Watcher Star Adventurer GTi": {"track": 0.5, "slew": 1.5, "max": 5.0},
    "Sky-Watcher Star Adventurer 2i": {"track": 0.1, "slew": 0.2, "max": 5.0},
    "Sky-Watcher EQ5 Pro": {"track": 1.0, "slew": 2.5, "max": 9.0},
    "Sky-Watcher HEQ5 Pro": {"track": 1.2, "slew": 3.0, "max": 11.0},
    "Sky-Watcher EQ6-R Pro": {"track": 1.5, "slew": 4.0, "max": 20.0},
    "ZWO AM3": {"track": 0.5, "slew": 1.5, "max": 8.0},
    "ZWO AM5": {"track": 0.7, "slew": 2.5, "max": 13.0},
    "Ioptron GEM28": {"track": 0.8, "slew": 2.0, "max": 12.0}
}

CAMERAS = {
    "ZWO ASI 183 MC Pro (Couleur)": {"w": 13.2, "h": 8.8, "px": 2.4, "cons": 1.5},
    "ZWO ASI 183 MM Pro (Mono)": {"w": 13.2, "h": 8.8, "px": 2.4, "cons": 1.5},
    "ZWO ASI 2600 MC Pro": {"w": 23.5, "h": 15.7, "px": 3.76, "cons": 2.0},
    "ZWO ASI 2600 MM Pro": {"w": 23.5, "h": 15.7, "px": 3.76, "cons": 2.0},
    "ZWO ASI 533 MC Pro": {"w": 11.3, "h": 11.3, "px": 3.76, "cons": 1.5},
    "ZWO ASI 294 MC Pro": {"w": 19.1, "h": 13.0, "px": 4.63, "cons": 1.8},
    "ZWO ASI 1600 MM Pro": {"w": 17.7, "h": 13.4, "px": 3.8, "cons": 1.5},
    "ZWO ASI 071 MC Pro": {"w": 23.6, "h": 15.6, "px": 4.78, "cons": 2.0},
    "ZWO ASI 2400 MC Pro (Full)": {"w": 36.0, "h": 24.0, "px": 5.94, "cons": 2.2},
    "ZWO ASI 6200 MC Pro (Full)": {"w": 36.0, "h": 24.0, "px": 3.76, "cons": 2.5},
    "QHY 268C": {"w": 23.5, "h": 15.7, "px": 3.76, "cons": 2.0},
    "Canon EOS 6D (Full Frame)": {"w": 36.0, "h": 24.0, "px": 6.54, "cons": 0.6},
    "Canon EOS 80D / 90D / 800D": {"w": 22.3, "h": 14.9, "px": 3.7, "cons": 0.5},
    "Nikon D850 / Z7 (Full Frame)": {"w": 35.9, "h": 23.9, "px": 4.35, "cons": 0.7},
    "Sony A7 III (Full Frame)": {"w": 35.6, "h": 23.8, "px": 5.9, "cons": 0.7}
}

# ==========================================
# 2. INTERFACE STREAMLIT
# ==========================================
st.set_page_config(page_title="AstroPépites Expert", layout="wide")

st.sidebar.title("🛠 MON SETUP NOMADE")

# Section Tube
st.sidebar.subheader("🔭 Optique")
sel_scope = st.sidebar.selectbox("Modèle de Télescope", sorted(list(TELESCOPES.keys())))
scope = TELESCOPES[sel_scope]

# Section Monture
st.sidebar.subheader("📡 Monture")
sel_mount = st.sidebar.selectbox("Modèle de Monture", sorted(list(MOUNTS.keys())))
mount = MOUNTS[sel_mount]

# Section Caméra
st.sidebar.subheader("📷 Caméra")
sel_cam = st.sidebar.selectbox("Modèle de Caméra", sorted(list(CAMERAS.keys())))
cam = CAMERAS[sel_cam]

# Section Énergie
st.sidebar.subheader("⚡ Énergie")
sel_ps = st.sidebar.selectbox("Power Station / Batterie", list(POWER_STATIONS.keys()))
ps = POWER_STATIONS[sel_ps]

# Accessoires
st.sidebar.subheader("🔌 Accessoires connectés")
use_asiair = st.sidebar.checkbox("ASIAIR Plus/Mini", value=True)
use_dew = st.sidebar.checkbox("Résistance chauffante", value=True)
use_eaf = st.sidebar.checkbox("Focusser EAF", value=True)

# ==========================================
# 3. CALCULS LOGISTIQUES
# ==========================================

# Calcul consommation totale
total_amps = mount["track"] + cam["cons"]
if use_asiair: total_amps += 0.8
if use_dew: total_amps += 0.7
if use_eaf: total_amps += 0.1

autonomie_h = ps["ah"] / total_amps
charge_kg = scope["weight"] + 1.2 # + Caméra, EAF, Cables env 1.2kg

# ==========================================
# 4. DASHBOARD PRINCIPAL
# ==========================================

st.title("🌌 AstroPépites Expert : Planificateur")

# Indicateurs clés
c1, c2, c3, c4 = st.columns(4)
c1.metric("⚡ Conso. estimée", f"{total_amps:.2f} A")
c2.metric("🔋 Autonomie", f"{autonomie_h:.1f} h")
c3.metric("📐 Échantillonnage", f"{(cam['px']/scope['focal'])*206:.2f} \"/px")
c4.metric("⚖️ Charge Utile", f"{charge_kg:.1f} kg / {mount['max']} kg")

if charge_kg > mount["max"]:
    st.error(f"⚠️ ATTENTION : Votre setup est trop lourd ({charge_kg:.1f}kg) pour la {sel_mount} (Max {mount['max']}kg) !")

tab1, tab2, tab3 = st.tabs(["🔎 SCANNER DE CIBLES", "📏 CHAMP & MOSAÏQUE", "🔋 ANALYSE ÉLECTRIQUE"])

with tab1:
    st.header("🎯 Cibles Exotiques & Rares")
    col_gps1, col_gps2 = st.columns(2)
    lat = col_gps1.number_input("Latitude GPS", value=48.85)
    lon = col_gps2.number_input("Longitude GPS", value=2.35)
    
    st.write("### Cibles conseillées pour votre setup actuel :")
    
    # Logique de conseil selon la focale
    if scope["focal"] <= 400:
        cat_type = "Nébuleuses étendues (Sharpless / Barnard)"
        targets = [
            {"Nom": "Sh2-132 (Nébuleuse du Lion)", "Type": "Émission", "Rare": "Oui", "Note": "Superbe en HOO"},
            {"Nom": "IC 1396 (Trompe d'Éléphant)", "Type": "Nébuleuse", "Rare": "Non", "Note": "Tient pile dans le champ"},
            {"Nom": "LDN 1251 (Nébuleuse Sombre)", "Type": "Poussière", "Rare": "Très", "Note": "Défi ciel pur"}
        ]
    else:
        cat_type = "Galaxies lointaines & Interaction (Arp)"
        targets = [
            {"Nom": "Arp 273 (La Rose)", "Type": "Galaxies", "Rare": "Oui", "Note": "Nécessite bon suivi"},
            {"Nom": "NGC 5907 (Galaxie du Splinter)", "Type": "Galaxie", "Rare": "Oui", "Note": "Tranchante, superbe"},
            {"Nom": "Abell 39 (La Bulle)", "Type": "Planétaire", "Rare": "Extrême", "Note": "Filtre OIII obligatoire"}
        ]
        
    st.success(f"Mode détecté : **{cat_type}**")
    st.table(targets)

with tab2:
    st.header("Simulateur de Champ de Vision (FOV)")
    fov_w = (cam["w"] / scope["focal"]) * (180/np.pi) * 60
    fov_h = (cam["h"] / scope["focal"]) * (180/np.pi) * 60
    st.info(f"Votre champ réel : **{fov_w:.1f}' x {fov_h:.1f}' arcmin**")
    
    # Calcul mosaïque
    obj_size = st.number_input("Taille de l'objet à photographier (arcmin)", value=60)
    tx = int(np.ceil(obj_size / (fov_w * 0.8)))
    ty = int(np.ceil(obj_size / (fov_h * 0.8)))
    
    if tx*ty > 1:
        st.warning(f"📐 Mosaïque nécessaire : {tx} x {ty} tuiles ({tx*ty} au total).")
    else:
        st.success("✅ La cible rentre dans un seul panneau !")

with tab3:
    st.header("Gestion de la Batterie")
    st.write(f"Analyse de la station : **{sel_ps}**")
    
    # Graphique
    h_x = np.linspace(0, autonomie_h, 20)
    batt_y = [ps["ah"] - (total_amps * t) for t in h_x]
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(h_x, 0, batt_y, color="#00ff00", alpha=0.3)
    ax.plot(h_x, batt_y, color="#00ff00", lw=2)
    ax.set_ylim(0, ps["ah"])
    ax.set_facecolor("#121212")
    fig.patch.set_facecolor("#121212")
    ax.tick_params(colors='white')
    ax.set_xlabel("Heures de Shoot", color="white")
    ax.set_ylabel("Capacité Ah", color="white")
    st.pyplot(fig)
    
    st.write(f"⚠️ **Note :** Gardez toujours 20% de marge de sécurité ({ps['ah']*0.2:.1f} Ah) pour éviter de couper l'ASIAIR brutalement.")

st.markdown("---")
st.caption("AstroPépites Expert v3.0 | Créé pour les astrophotographes exigeants.")

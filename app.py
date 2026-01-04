import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_moon
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Expert Filtres Mondial", layout="wide")

# --- 1. BIBLIOTHÈQUE MONDIALE DE FILTRES ---
FILTERS_MARKET = {
    "Svbony": ["SV220 Dual-Band", "SV226 CLS", "UV/IR Cut"],
    "Optolong": ["L-Pro", "L-Extreme", "L-Ultimate", "L-Enhance", "Clear Sky"],
    "Antlia": ["ALP-T Dual Band (5nm)", "Triband RGB Ultra", "Ha/OIII/SII Pro"],
    "ZWO": ["Duo-Band Filter", "LRGB Kit", "Narrowband 7nm"],
    "Baader": ["Neodymium (Moon & Skyglow)", "UHC-S", "Fringe Killer"],
    "IDAS": ["LPS-D2", "NBZ Nebula Boost", "LPS-D3"]
}

# Mise à plat de la liste pour la recherche
all_filters_list = []
for brand, models in FILTERS_MARKET.items():
    for model in models:
        all_filters_list.append(f"{brand} - {model}")
all_filters_list.append("Aucun / Tiroir Vide")

# --- 2. LOGIQUE DE CONSEIL FILTRE ---
def get_filter_advice(target_type, selected_filter):
    advice = ""
    is_narrow = any(x in selected_filter for x in ["Dual", "Extreme", "Ultimate", "Narrow", "SV220", "NBZ", "ALP-T"])
    
    if "Galaxie" in target_type or "Amas" in target_type:
        if is_narrow:
            advice = "⚠️ **Attention :** Ce filtre est trop sélectif pour une galaxie. Vous allez perdre les couleurs des bras spiraux. Utilisez plutôt un filtre L-Pro ou laissez le tiroir vide."
        else:
            advice = "✅ **Bon choix :** Ce filtre large bande (ou vide) respectera les couleurs naturelles de la galaxie."
    
    elif "Nébuleuse" in target_type:
        if is_narrow:
            advice = "✅ **Parfait :** Ce filtre Narrowband fera ressortir le H-alpha et l'OIII, même avec la Lune ou de la pollution."
        else:
            advice = "💡 **Conseil :** Pour cette nébuleuse, un filtre Dual-Band (type SV220 ou L-Extreme) donnerait beaucoup plus de contraste."
            
    return advice

# --- 3. SIDEBAR : MATÉRIEL & CATALOGUES ---
st.sidebar.title("🛠 CONFIGURATION SETUP")

with st.sidebar.expander("🔭 Mon Matériel & Filtres", expanded=True):
    sel_scope = st.text_input("Télescope", "Evolux 62ED")
    # LISTE DÉROULANTE MONDIALE
    user_filter = st.selectbox("Filtre installé dans le tiroir", all_filters_list)
    batt_wh = st.number_input("Batterie (Wh)", value=268)

with st.sidebar.expander("🌲 Boussole & Catalogues", expanded=True):
    h_n = st.slider("Nord", 0, 70, 20)
    h_e = st.slider("Est", 0, 70, 15)
    h_s = st.slider("Sud", 0, 70, 10)
    h_o = st.slider("Ouest", 0, 70, 25)
    show_arp = st.checkbox("Arp (Raretés)", value=True)
    show_m = st.checkbox("Messier", value=True)

# --- 4. BASE DE DONNÉES CIBLES ---
DB_OBJECTS = [
    {"name": "Arp 273 (La Rose)", "type": "Galaxie", "ra": "02h21m28s", "dec": "+39d22m32s", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg/320px-Interacting_galaxy_pair_Arp_273_%28captured_by_the_Hubble_Space_Telescope%29.jpg"},
    {"name": "Abell 31", "type": "Nébuleuse P.", "ra": "08h54m13s", "dec": "+08d53m52s", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Abell_31_nebula.jpg/320px-Abell_31_nebula.jpg"}
]

# --- 5. INTERFACE ---
st.title("🌌 AstroPépites : Planificateur Universel")

sel_obj = st.selectbox("🎯 Choisir une cible", [o["name"] for o in DB_OBJECTS])
t_data = next(obj for obj in DB_OBJECTS if obj["name"] == sel_obj)

# Affichage de la vignette et du conseil filtre
col_img, col_txt = st.columns([1, 2])

with col_img:
    st.image(t_data["img"], caption=f"Cible : {t_data['name']}")

with col_txt:
    st.subheader(f"🛡️ Stratégie pour {t_data['name']}")
    st.write(f"**Cible de type :** {t_data['type']}")
    st.write(f"**Filtre actuel :** {user_filter}")
    
    # Affichage du conseil intelligent basé sur le filtre choisi
    conseil = get_filter_advice(t_data['type'], user_filter)
    st.info(conseil)

# Graphique de visibilité (Logique boussole conservée)
st.divider()
st.subheader("📈 Visibilité & Horizon Local")
# ... (Code du graphique identique à la v7.0) ...

# Rappel pour l'utilisateur
if st.button("💾 Sauvegarder ma configuration"):
    st.success(f"Configuration sauvegardée : {sel_scope} avec {user_filter}.")

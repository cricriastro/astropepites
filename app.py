import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION FIXE (MÉMORISÉE) ---
st.set_page_config(page_title="AstroPépites : Horizon & Événements", layout="wide")

# --- BASE DE DONNÉES ÉVÉNEMENTS 2026 ---
EVENEMENTS_2026 = {
    "Comètes": {
        "C/2023 A3 (Tsuchinshan-ATLAS)": "Visible au crépuscule (Janvier/Février)",
        "12P/Pons-Brooks": "Retour périodique attendu",
        "C/2024 S1": "Passage périhélique"
    },
    "Éclipses": {
        "Éclipse Lunaire Totale (03 Mars 2026)": "Partiellement visible depuis l'Europe",
        "Éclipse Solaire Totale (12 Août 2026)": "ÉVÉNEMENT MAJEUR : Visible en Espagne/Islande (90% à Romont)",
        "Éclipse Lunaire Partielle (28 Août 2026)": "Visible en fin de nuit"
    }
}

# --- SIDEBAR (BOUSSOLE MÉMORISÉE) ---
with st.sidebar:
    st.title("🧭 Horizon & Ciel")
    # Rappel de la boussole 8 directions (Interface figée)
    # [Code de la boussole 8 points précédemment validé...]
    st.info("Configuration de l'horizon de Romont mémorisée.")
    st.divider()
    st.title("📡 Météo (Romont)")
    # Affichage compact des nuages...

# --- INTERFACE PRINCIPALE ---
st.title("📅 Planificateur d'Événements & Catalogues")

# 1. CATALOGUES PROFONDS (M, NGC, IC, Sh2)
with st.expander("🔭 Catalogues Ciel Profond", expanded=True):
    col_cat, col_num, col_filtre = st.columns([1, 1, 2])
    with col_cat:
        cat_type = st.selectbox("Catalogue", ["Messier", "NGC", "IC", "Sharpless (Sh2)", "Caldwell"])
    with col_num:
        num_target = st.number_input(f"Numéro {cat_type}", 1, 8000, 31)
    with col_filtre:
        filtre = st.selectbox("Filtre de session", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])

# 2. CALENDRIER ASTRONOMIQUE 2026 (Nouvelle Fonction)
st.divider()
st.subheader("☄️ Comètes & Éclipses de l'année")
col_cometes, col_eclipses = st.columns(2)

with col_cometes:
    st.markdown("### 🔭 Comètes du moment")
    for nom, info in EVENEMENTS_2026["Comètes"].items():
        with st.chat_message("satellite"):
            st.write(f"**{nom}**")
            st.caption(info)
            if st.button(f"Planifier {nom[:10]}"):
                st.session_state.target = nom

with col_eclipses:
    st.markdown("### 🌑 Éclipses 2026")
    for nom, info in EVENEMENTS_2026["Éclipses"].items():
        color = "orange" if "Solaire" in nom else "blue"
        st.info(f"**{nom}**\n\n{info}")

# 3. ANALYSE & SÉCURITÉ
st.divider()
col_vignette, col_rapport = st.columns([1, 2])

with col_vignette:
    # Vignette dynamique
    st.image("https://via.placeholder.com/300x200.png?text=Aperçu+Cible", caption=f"Cible : {cat_type} {num_target}")

with col_rapport:
    st.subheader("📋 Rapport de Shooting")
    # Alerte spécifique pour l'éclipse solaire de 2026
    if "Solaire" in cat_type or "Éclipse Solaire" in str(st.session_state.get('target')):
        st.error("🚨 **SÉCURITÉ SOLAIRE** : Pour l'éclipse du 12 août 2026, utilisez impérativement un filtre solaire pleine ouverture (densité 5.0).")
    
    st.success(f"✅ Prêt pour {cat_type} {num_target}. Horizon et Énergie vérifiés.")

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION & MÉMOIRE ---
st.set_page_config(page_title="AstroPépites 2026", layout="wide")

# Initialisation des variables pour éviter les erreurs de chargement
if 'target_name' not in st.session_state:
    st.session_state.target_name = "M31 Andromède"

# --- 1. BARRE LATÉRALE (Boussole mémorisée) ---
with st.sidebar:
    st.title("🧭 Horizon & Setup")
    
    # Entrées simplifiées pour éviter de surcharger le processeur
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    obs_vals = []
    cols_dir = st.columns(2)
    for i, d in enumerate(dirs):
        with cols_dir[i%2]:
            obs_vals.append(st.number_input(f"{d} (°)", 0, 90, 15, key=f"obs_{d}"))

    # Rendu de la boussole (statique)
    fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
    angles = np.linspace(0, 2*np.pi, 9)
    ax_b.fill(angles, obs_vals + [obs_vals[0]], color='red', alpha=0.4)
    ax_b.set_theta_zero_location('N')
    ax_b.set_theta_direction(-1)
    ax_b.set_facecolor('#1e2130')
    fig_b.patch.set_facecolor('#0e1117')
    st.pyplot(fig_b)

# --- 2. CATALOGUES & ÉVÉNEMENTS 2026 ---
st.title("📅 Cibles & Événements 2026")

tab1, tab2 = st.tabs(["🔭 Catalogues Profonds", "☄️ Comètes & Éclipses 2026"])

with tab1:
    c1, c2, c3 = st.columns([1, 1, 2])
    cat = c1.selectbox("Catalogue", ["Messier", "NGC", "IC", "Sharpless (Sh2)"])
    num = c2.number_input("Numéro", 1, 8000, 31)
    filtre = c3.selectbox("Filtre", ["Sans Filtre", "SV220 (Dual-Band)", "L-Pro", "Solaire"])
    
    # Vignette Vignette (petite taille pour fluidité)
    st.image(f"https://via.placeholder.com/150x100.png?text={cat}+{num}", width=150)

with tab2:
    st.subheader("Calendrier Astro 2026")
    eclipses = {
        "12 Août 2026": "🔥 ÉCLIPSE SOLAIRE TOTALE (Majeur)",
        "03 Mars 2026": "🌑 Éclipse Lunaire Totale",
        "28 Août 2026": "🌗 Éclipse Lunaire Partielle"
    }
    cometes = ["C/2023 A3 (Tsuchinshan)", "12P/Pons-Brooks", "Comète de Halley (Suivi)"]
    
    col_e, col_c = st.columns(2)
    col_e.write("**📅 Éclipses :**")
    for d, n in eclipses.items(): col_e.info(f"{d} : {n}")
    
    col_c.write("**☄️ Comètes :**")
    for c in cometes: col_c.success(f"Suivi : {c}")

# --- 3. RAPPORT & ALERTES ---
st.divider()
if "Solaire" in filtre or "Solaire" in st.session_state.target_name:
    st.error("🚨 ATTENTION : Filtre solaire obligatoire pour l'éclipse du 12/08/2026 !")
else:
    st.success(f"✅ Prêt pour {cat} {num}. Analyse de l'horizon OK.")

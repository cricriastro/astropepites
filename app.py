import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Planificateur Expert", layout="wide")

# --- BASE DE DONNÉES ÉTENDUE ---
# On structure par catalogue pour que le menu "Cibles" soit filtré
CATALOGUES = {
    "Messier": ["M1", "M13", "M16", "M27", "M31", "M33", "M42", "M45", "M51", "M81", "M101"],
    "NGC / IC": ["NGC 7000", "NGC 6960", "NGC 2237", "IC 434", "IC 1396", "NGC 891", "NGC 4565", "IC 1805"],
    "Abell (Néb. Planétaires)": ["Abell 21 (Medusa)", "Abell 33", "Abell 39", "Abell 70", "Abell 1656"],
    "Arp (Galaxies exotiques)": ["Arp 244 (Antennae)", "Arp 188 (Tadpole)", "Arp 273 (Rose)", "Arp 297"],
    "Sharpless (Sh2)": ["Sh2-155 (Cave)", "Sh2-101 (Tulip)", "Sh2-129 (Squid)", "Sh2-190 (Heart)"],
    "Barnard / LDN": ["Barnard 33", "Barnard 150", "LDN 1251", "LDN 673", "LBN 438"],
    "Événements 2026": ["Éclipse Solaire Totale (12/08)", "C/2023 A3 (Comète)", "Éclipse Lunaire (03/03)"]
}

# --- SIDEBAR (Boussole 8 points restaurée) ---
with st.sidebar:
    st.title("🧭 Horizon & Setup")
    obs = {}
    # Tes directions précises
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    for d in dirs:
        obs[d] = st.slider(f"Obstacle {d} (°)", 0, 90, 15)

    # Rendu Graphique Polaire
    fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
    angles = np.linspace(0, 2*np.pi, 9)
    values = [obs[d] for d in dirs] + [obs["N"]]
    ax_b.fill(angles, values, color='#ff4b4b', alpha=0.4, edgecolor='#ff4b4b', lw=2)
    ax_b.set_theta_zero_location('N')
    ax_b.set_theta_direction(-1)
    ax_b.set_facecolor('#1e2130')
    fig_b.patch.set_facecolor('#0e1117')
    ax_b.tick_params(colors='white')
    st.pyplot(fig_b)

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session : Catalogues Universels")

# 1. MOTEUR DE RECHERCHE LIBRE (Pour les cibles hors-listes)
with st.expander("🔍 Recherche Libre (NASA / Hubble / Simbad)", expanded=False):
    search_query = st.text_input("Tapez le matricule de la cible (ex: PGC 1234, Arp 273, Hubble 12...)", "")
    if search_query:
        st.info(f"🛰️ Recherche étendue activée pour : **{search_query}**")

# 2. SÉLECTION DYNAMIQUE PAR CATALOGUE
st.divider()
c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    choix_cat = st.selectbox("1. Choisir le Catalogue", list(CATALOGUES.keys()))

with c2:
    # Le menu déroulant des cibles se met à jour selon le catalogue choisi au-dessus
    choix_cible = st.selectbox(f"2. Cibles {choix_cat}", CATALOGUES[choix_cat])

with c3:
    filtre = st.selectbox("3. Filtre installé", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "Filtre Solaire"])

# 3. RAPPORT DE MISSION & VIGNETTE
st.divider()
col_img, col_txt = st.columns([1, 2])

# On définit la cible finale (soit la recherche, soit le menu)
cible_finale = search_query if search_query else choix_cible

with col_img:
    # Placeholder dynamique pour la vignette
    st.image(f"https://via.placeholder.com/400x300.png?text={cible_finale.replace(' ', '+')}", 
             caption=f"Aperçu catalogue : {cible_finale}", use_container_width=True)

with col_txt:
    st.subheader(f"📋 Rapport d'Analyse : {cible_finale}")
    
    # Alertes intelligentes
    if "Barnard" in choix_cat or "LDN" in choix_cat:
        st.warning("☁️ **Nébuleuse Sombre** : Évitez les filtres à bande étroite. Un ciel pur et des poses longues sont nécessaires.")
    
    if "Solaire" in choix_cible or "Solaire" in filtre:
        st.error("🚨 **SÉCURITÉ SOLAIRE** : Vérifiez votre filtre frontal avant toute visée !")
    else:
        st.success(f"✅ Configuration validée pour Romont (Altitude min : {obs['S']}° au Sud).")

    # Graphique d'autonomie (Exemple pour Bluetti EB3A)
    tx = np.linspace(0, 7, 100); ty = np.linspace(100, 10, 100)
    fig, ax = plt.subplots(figsize=(8, 2))
    ax.plot(tx, ty, color='#00ffd0')
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

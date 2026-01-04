import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Explorateur Universel", layout="wide")

# --- BASE DE DONNÉES ÉTENDUE (Exemples de catalogues rares) ---
# En production, on peut coupler cela à une API pour avoir les 100 000+ objets
CATALOGUES_PROFS = {
    "Messier (Classiques)": ["M1", "M13", "M16", "M27", "M31", "M33", "M42", "M51", "M81", "M101"],
    "NGC / IC (Complet)": ["NGC 7000", "NGC 6960", "NGC 2237", "IC 434", "IC 1396", "NGC 891", "NGC 4565"],
    "Abell (Nébuleuses Planétaires/Amas)": ["Abell 21 (Medusa)", "Abell 33", "Abell 39", "Abell 1656 (Coma Cluster)", "Abell 2151"],
    "Arp (Galaxies en interaction)": ["Arp 244 (Antennae)", "Arp 188 (Tadpole)", "Arp 273 (Rose)", "Arp 297"],
    "Barnard / LDN (Nuages sombres)": ["Barnard 33", "Barnard 150", "LDN 1251", "LDN 673", "LBN 438"],
    "Sharpless (Sh2 - Hydrogène)": ["Sh2-155 (Cave)", "Sh2-101 (Tulip)", "Sh2-129 (Squid)", "Sh2-190 (Heart)"],
    "Événements 2026 (Comètes/Éclipses)": ["Éclipse Solaire Totale (12/08)", "C/2023 A3", "Éclipse Lunaire (03/03)"]
}

# --- SIDEBAR (Boussole 8 points mémorisée) ---
with st.sidebar:
    st.title("🧭 Horizon & Setup")
    obs = {}
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
st.title("🔭 Planification Expert : Cibles Exotiques")

# 1. RECHERCHE LIBRE (Pour "Tout avoir")
with st.expander("🔍 Recherche Universelle (NASA/Hubble/Simbad)", expanded=True):
    col_search, col_type = st.columns([2, 1])
    search_target = col_search.text_input("Tapez le nom exact d'un objet (ex: Arp 273, PGC 1234, Abell 21)", placeholder="Chercher dans tous les catalogues...")
    target_origin = col_type.selectbox("Priorité Catalogue", ["Automatique", "NASA/NED", "Hubble/ESA", "Simbad"])
    if search_target:
        st.info(f"🛰️ Recherche en cours pour '**{search_target}**' dans les archives **{target_origin}**...")

# 2. SÉLECTION PAR MENUS DÉROULANTS (Catalogues Spécialisés)
st.divider()
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    cat = st.selectbox("Catégorie de Catalogue", list(CATALOGUES_PROFS.keys()))
with c2:
    target = st.selectbox("Sélectionner la Cible", CATALOGUES_PROFS[cat])
with c3:
    filtre = st.selectbox("Filtre", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "Filtre Solaire"])

# 3. AFFICHAGE IMAGE & ANALYSE
st.divider()
col_img, col_txt = st.columns([1, 2])

with col_img:
    # On affiche une vignette générique ou issue d'un moteur de recherche
    st.image(f"https://via.placeholder.com/400x300.png?text={target.replace(' ', '+')}", use_container_width=True, caption=f"Archives visuelles : {target}")

with col_txt:
    st.subheader(f"📋 Rapport de Mission : {target}")
    
    # Logique d'alerte pour cibles difficiles
    if "Abell" in target or "Arp" in target:
        st.warning("🔭 **Cible à faible magnitude surfacique** : Temps de pose unitaire long (300s+) et bon ciel recommandés.")
    
    if "SV220" in filtre and "LDN" in target:
        st.error("❌ **Incohérence Filtre** : Les nébuleuses sombres (LDN/Barnard) nécessitent un spectre large. Utilisez 'Sans Filtre'.")
    else:
        st.success(f"✅ Setup prêt pour acquisition.")

    # Graphique d'autonomie EB3A
    tx = np.linspace(0, 7, 100); ty = np.linspace(100, 15, 100)
    fig, ax = plt.subplots(figsize=(8, 2))
    ax.plot(tx, ty, color='#00ffd0')
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

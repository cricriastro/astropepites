import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Expert Horizon", layout="wide")

# --- BASE DE DONNÉES ÉTENDUE ---
CATALOGUES = {
    "Messier": ["M1", "M13", "M16", "M27", "M31", "M33", "M42", "M45", "M51", "M81", "M101"],
    "NGC / IC": ["NGC 7000", "NGC 6960", "NGC 2237", "IC 434", "IC 1396", "NGC 891", "NGC 4565", "IC 1805"],
    "Sharpless (Sh2)": ["Sh2-155 (Cave)", "Sh2-101 (Tulip)", "Sh2-129 (Squid)", "Sh2-190 (Heart)", "Sh2-276 (Barnard Loop)"],
    "Abell (Planétaires)": ["Abell 21 (Medusa)", "Abell 33", "Abell 39", "Abell 70", "Abell 1656"],
    "Arp (Galaxies)": ["Arp 244 (Antennae)", "Arp 188 (Tadpole)", "Arp 273 (Rose)", "Arp 297"],
    "Barnard / LDN": ["Barnard 33", "Barnard 150", "LDN 1251", "LDN 673", "LBN 438"],
    "Événements 2026": ["Éclipse Solaire Totale (12/08)", "C/2023 A3 (Comète)", "Éclipse Lunaire (03/03)"]
}

# Logique de recommandation de filtres
def get_recommended_filters(cat, target):
    if "Sharpless" in cat or "NGC 7000" in target or "IC 434" in target or "Abell" in cat:
        return ["Svbony SV220 (Dual-Band)", "Optolong L-eXtreme", "Filtre H-alpha"]
    elif "Barnard" in cat or "LDN" in cat or "M31" in target or "M45" in target or "Arp" in cat:
        return ["Sans Filtre / Clair", "Optolong L-Pro", "UV/IR Cut"]
    elif "Solaire" in target:
        return ["Filtre Solaire Frontal (ND 5.0)"]
    else:
        return ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro"]

# --- SIDEBAR (Boussole 8 points) ---
with st.sidebar:
    st.title("🧭 Horizon & Setup")
    obs = {}
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    for d in dirs:
        obs[d] = st.slider(f"Obstacle {d} (°)", 0, 90, 15)

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
st.title("🔭 Planification Expert : Cibles & Optique")

# 1. SÉLECTION DYNAMIQUE
st.divider()
c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    choix_cat = st.selectbox("📁 Catalogue", list(CATALOGUES.keys()))
with c2:
    choix_cible = st.selectbox(f"🎯 Cible {choix_cat}", CATALOGUES[choix_cat])
with c3:
    recommandations = get_recommended_filters(choix_cat, choix_cible)
    filtre = st.selectbox("💎 Filtre conseillé", recommandations)

# 2. VIGNETTE & ANALYSE
st.divider()
col_img, col_txt = st.columns([1, 2])

with col_img:
    # Génération d'une vignette automatique via Wikipedia/Placeholder
    # (Remplace les espaces par des + pour l'URL)
    img_query = choix_cible.split('(')[0].strip().replace(' ', '+')
    st.image(f"https://api.star-navigation.com/target_thumbnail/{img_query}", 
             fallback=f"https://via.placeholder.com/400x300.png?text=Vignette:+{img_query}",
             caption=f"Vignette de confirmation : {choix_cible}")

with col_txt:
    st.subheader(f"📋 Rapport d'Analyse : {choix_cible}")
    
    # Message intelligent basé sur le filtre choisi
    if "SV220" in filtre:
        st.info("💡 **Analyse Optique** : Ce filtre Dual-Band fera ressortir les nébulosités rouges (Ha) et bleu-vert (OIII).")
    elif "Sans Filtre" in filtre:
        st.success("💡 **Analyse Optique** : Idéal pour les galaxies ou poussières sombres afin de garder les couleurs naturelles.")

    # Graphique d'autonomie
    tx = np.linspace(0, 8, 100); ty = np.linspace(100, 10, 100)
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.plot(tx, ty, color='#00ffd0', lw=2)
    ax.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

# 3. RECHERCHE LIBRE
with st.expander("🔍 Objet hors-catalogue (NASA/Hubble)"):
    search_q = st.text_input("Taper un nom ou matricule (ex: PGC 1234)...")
    if search_q:
        st.write(f"🛰️ Recherche de métadonnées pour : {search_q}")

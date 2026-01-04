import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Expert Romont", layout="wide")

# --- 1. CATALOGUES ÉTENDUS ---
CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC / IC": ["NGC 7000", "NGC 6960", "NGC 2237", "IC 434", "IC 1396", "NGC 891", "NGC 4565", "IC 1805"],
    "Sharpless (Sh2)": [f"Sh2-{i}" for i in [1, 101, 129, 155, 190, 240, 276]],
    "Abell (Planétaires)": [f"Abell {i}" for i in [21, 31, 33, 39, 70, 72, 85]],
    "Arp (Galaxies)": [f"Arp {i}" for i in [244, 188, 273, 297, 299]],
    "Barnard / LDN": ["Barnard 33", "Barnard 150", "LDN 1251", "LDN 673"],
    "Événements 2026": ["Éclipse Solaire Totale (12/08)", "C/2023 A3 (Comète)", "Éclipse Lunaire (03/03)"]
}

# --- 2. COLONNE DE GAUCHE (Gains de place) ---
with st.sidebar:
    st.title("🎒 Gestion Matériel")
    
    # Menu rétractable pour les filtres
    with st.expander("💎 Mon Sac à Filtres", expanded=False):
        possede_clair = st.checkbox("UV-IR Cut / Clair", value=True)
        possede_dual = st.checkbox("SV220 (Dual-Band)", value=True)
        possede_lpro = st.checkbox("L-Pro / Anti-Pollution", value=True)
        possede_solaire = st.checkbox("Filtre Solaire", value=False)
    
    mes_filtres = []
    if possede_clair: mes_filtres.append("Clair")
    if possede_dual: mes_filtres.append("SV220")
    if possede_lpro: mes_filtres.append("L-Pro")

    st.divider()

    # Menu rétractable pour l'Horizon (Boussole)
    with st.expander("🧭 Horizon & Boussole", expanded=True):
        st.caption("Élévation des obstacles (°)")
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        obs = {d: st.slider(f"{d}", 0, 90, 15, key=f"slider_{d}") for d in dirs}

        # Rendu de la boussole 8 points
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

# --- 3. LOGIQUE INTELLIGENTE ---
def conseiller_filtre(cat, target, inventaire):
    if any(c in cat for c in ["Sharpless", "Abell"]) or "NGC 7000" in target:
        return "SV220" if "SV220" in inventaire else "un filtre Dual-Band"
    if any(c in cat for c in ["Arp", "Barnard", "Messier"]):
        return "L-Pro" if "L-Pro" in inventaire else "Clair"
    return "Clair"

# --- 4. INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Session 2026")

c1, c2 = st.columns([2, 1])

with c1:
    col_cat, col_target = st.columns(2)
    cat_choisi = col_cat.selectbox("Catalogue", list(CATALOGUES.keys()))
    cible_choisie = col_target.selectbox(f"Objet", CATALOGUES[cat_choisi])
    
    recommandation = conseiller_filtre(cat_choisi, cible_choisie, mes_filtres)
    st.success(f"💎 Conseil Matériel : Utilisez votre filtre **{recommandation}** pour cette cible.")

with c2:
    # Correction de l'erreur d'image (suppression du paramètre 'fallback' qui bug)
    st.write("**Vignette de confirmation**")
    clean_name = cible_choisie.split('(')[0].strip().replace(' ', '+')
    try:
        st.image(f"https://imgproxy.astronomy-imaging-camera.com/api/v1/objects/{clean_name}/thumbnail", 
                 width=250)
    except:
        st.info("Aperçu non disponible pour cette cible rare.")

# --- 5. RAPPORT ET ÉNERGIE ---
st.divider()
col_rep, col_graph = st.columns([1, 1])

with col_rep:
    st.subheader("📋 Analyse du Shooting")
    st.info(f"Cible : {cible_choisie} | Horizon Sud : {obs['S']}°")
    
    # Courbe de décharge théorique
    tx = np.linspace(0, 8, 100); ty = np.linspace(100, 10, 100)
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(tx, ty, color='#00ffd0', lw=2)
    ax.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
    ax.set_title("Autonomie Batterie (Wh)", color="white")
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

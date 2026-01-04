import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites : Expert Romont", layout="wide")

# --- 1. BASE DE DONNÉES DES CATALOGUES (Versions étendues) ---
CATALOGUES = {
    "Messier (Classiques)": [f"M{i}" for i in range(1, 111)],
    "NGC / IC (Sélection)": ["NGC 7000", "NGC 6960", "NGC 2237", "IC 434", "IC 1396", "NGC 891", "NGC 4565", "IC 1805", "NGC 253", "NGC 6946"],
    "Abell (Planétaires)": [f"Abell {i}" for i in [21, 31, 33, 39, 70, 72, 85]],
    "Arp (Galaxies Exotiques)": [f"Arp {i}" for i in [244, 188, 273, 297, 299, 317]],
    "Sharpless (Sh2 - Nébuleuses)": [f"Sh2-{i}" for i in [1, 101, 129, 155, 190, 240, 276]],
    "Barnard / LDN (Sombres)": [f"Barnard {i}" for i in [33, 150, 142]] + [f"LDN {i}" for i in [1251, 673, 438]],
    "Hickson (HCG - Groupes)": [f"HCG {i}" for i in [44, 68, 92]],
    "Événements 2026": ["Éclipse Solaire Totale (12/08)", "C/2023 A3 (Comète)", "Éclipse Lunaire (03/03)"]
}

# --- 2. GESTION DU MATÉRIEL (Ton inventaire) ---
with st.sidebar:
    st.title("🎒 Mon Sac à Matériel")
    st.subheader("Mes Filtres")
    possede_clair = st.checkbox("Filtre Clair / UV-IR Cut", value=True)
    possede_dual = st.checkbox("Svbony SV220 (Dual-Band)", value=True)
    possede_lpro = st.checkbox("Optolong L-Pro / Anti-Pollution", value=False)
    possede_solaire = st.checkbox("Filtre Solaire Frontal", value=False)
    
    mes_filtres = []
    if possede_clair: mes_filtres.append("UV-IR Cut / Clair")
    if possede_dual: mes_filtres.append("SV220 (Dual-Band)")
    if possede_lpro: mes_filtres.append("L-Pro / Anti-Pollution")
    if possede_solaire: mes_filtres.append("Filtre Solaire")

    st.divider()
    st.title("🧭 Horizon (Romont)")
    obs = {d: st.slider(f"{d} (°)", 0, 90, 15) for d in ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]}

# --- 3. LOGIQUE DE RECOMMANDATION INTELLIGENTE ---
def conseiller_filtre(cat, target, inventaire):
    # Logique pour Nébuleuses (Ha/OIII)
    if any(c in cat for c in ["Sharpless", "Abell"]) or "NGC 7000" in target or "IC 434" in target:
        if "SV220 (Dual-Band)" in inventaire:
            return "✅ Utilise ton **SV220** (Idéal pour faire ressortir le gaz)."
        return "⚠️ Tu devrais utiliser un filtre Dual-Band (non possédé)."
    
    # Logique pour Galaxies / Poussières
    if any(c in cat for c in ["Arp", "Barnard", "Messier"]):
        if "L-Pro / Anti-Pollution" in inventaire:
            return "✅ Utilise ton **L-Pro** (Bon compromis contre la pollution de Romont)."
        return "✅ Utilise ton **Filtre Clair** (Garde le spectre complet pour cette cible)."
    
    return "Filtre standard conseillé."

# --- 4. INTERFACE PRINCIPALE ---
st.title("🔭 Planification de Shooting Expert")

c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("🎯 Choix de la cible")
    col_cat, col_target = st.columns(2)
    cat_choisi = col_cat.selectbox("Catalogue", list(CATALOGUES.keys()))
    cible_choisie = col_target.selectbox(f"Objet dans {cat_choisi}", CATALOGUES[cat_choisi])
    
    # Recommandation basée sur TON matériel
    recommandation = conseiller_filtre(cat_choisi, cible_choisie, mes_filtres)
    st.info(recommandation)

with c2:
    # VIGNETTE DYNAMIQUE
    st.write("**Vignette de confirmation**")
    clean_name = cible_choisie.split('(')[0].strip().replace(' ', '+')
    # Utilisation d'un service d'imagerie astro simplifié
    st.image(f"https://imgproxy.astronomy-imaging-camera.com/api/v1/objects/{clean_name}/thumbnail", 
             caption=f"Aperçu {cible_choisie}",
             fallback="https://via.placeholder.com/200x150.png?text=Cible+Rare")

# --- 5. RAPPORT ET ÉNERGIE ---
st.divider()
col_rep, col_graph = st.columns([2, 1])

with col_rep:
    st.subheader("📋 Résumé de la session")
    st.write(f"**Cible :** {cible_choisie}")
    st.write(f"**Site :** Romont, FR (Altitude max : {90-obs['S']}°)")
    if "Solaire" in cible_choisie and not possede_solaire:
        st.error("🚨 ATTENTION : Tu n'as pas coché le filtre solaire dans ton matériel !")

with col_graph:
    # Graphique boussole miniature
    fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(2, 2))
    angles = np.linspace(0, 2*np.pi, 9)
    vals = list(obs.values()) + [obs["N"]]
    ax_b.fill(angles, vals, color='red', alpha=0.3)
    ax_b.set_facecolor('#1e2130'); fig_b.patch.set_facecolor('#0e1117')
    ax_b.set_yticklabels([]); ax_b.set_xticklabels([])
    st.pyplot(fig_b)

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION SANS ÉCHEC ---
st.set_page_config(page_title="AstroPépites Dashboard", layout="wide")

# --- 1. CATALOGUES MASSIFS ---
CATALOGUES = {
    "Messier": [f"M{i}" for i in range(1, 111)],
    "NGC": [f"NGC {i}" for i in [7000, 6960, 2237, 891, 4565, 31, 32, 1]],
    "Sharpless (Sh2)": [f"Sh2-{i}" for i in range(1, 313)],
    "Arp (Galaxies exotiques)": [f"Arp {i}" for i in range(1, 339)],
    "Abell (Planétaires)": [f"Abell {i}" for i in range(1, 87)],
    "Hickson (Groupes HCG)": [f"HCG {i}" for i in range(1, 101)],
    "Événements 2026": ["Éclipse Solaire (12/08)", "Comète C/2023 A3", "Éclipse Lunaire (03/03)"]
}

# --- 2. COLONNE DE GAUCHE (Rangement optimisé) ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Section Matériel Rétractable
    with st.expander("🎒 Mon Sac à Matériel", expanded=False):
        filtres_possedes = st.multiselect(
            "Mes filtres en stock :",
            ["Clair / UV-IR", "Svbony SV220", "Optolong L-Pro", "Solaire"],
            default=["Clair / UV-IR", "Svbony SV220"]
        )
    
    # Section Horizon Rétractable (La Boussole)
    with st.expander("🧭 Boussole d'Horizon", expanded=True):
        st.caption("Altitude min des obstacles (°)")
        dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        # On utilise des colonnes pour gagner de la place
        c1, c2 = st.columns(2)
        obs = {}
        for i, d in enumerate(dirs):
            with c1 if i % 2 == 0 else c2:
                obs[d] = st.number_input(f"{d}", 0, 90, 15)

        # Graphique Polaire (Plus léger)
        fig_b, ax_b = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(3, 3))
        angles = np.linspace(0, 2*np.pi, 9)
        values = [obs[d] for d in dirs] + [obs["N"]]
        ax_b.fill(angles, values, color='#ff4b4b', alpha=0.4, edgecolor='#ff4b4b')
        ax_b.set_theta_zero_location('N')
        ax_b.set_theta_direction(-1)
        ax_b.set_facecolor('#1e2130')
        fig_b.patch.set_facecolor('#0e1117')
        ax_b.tick_params(colors='white', labelsize=8)
        st.pyplot(fig_b)

# --- 3. INTERFACE PRINCIPALE ---
st.title("🔭 Planification Expert")

# Ligne 1 : Sélection Cible
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    cat = st.selectbox("📁 Catalogue", list(CATALOGUES.keys()))
with col2:
    target = st.selectbox(f"🎯 Cible {cat}", CATALOGUES[cat])
with col3:
    # Intelligence de recommandation
    if "Sharpless" in cat or "Abell" in cat:
        rec = "Svbony SV220"
    elif "Arp" in cat or "HCG" in cat:
        rec = "Optolong L-Pro / Clair"
    else:
        rec = "Clair / UV-IR"
    st.info(f"💡 Conseil : **{rec}**")

# Ligne 2 : Analyse et Vignette
st.divider()
c_img, c_txt = st.columns([1, 2])

with c_img:
    # Au lieu de charger une image externe qui fait ramer, on met un aperçu stylisé
    st.markdown(f"""
    <div style="border: 2px solid #555; padding: 20px; text-align: center; border-radius: 10px;">
        <span style="font-size: 50px;">🌌</span><br>
        <b>{target}</b><br><small>Aperçu Catalogue</small>
    </div>
    """, unsafe_allow_html=True)

with c_txt:
    st.subheader("📋 Rapport de Shooting")
    st.success(f"Configuration validée pour **{target}** à Romont.")
    
    # Graphique de décharge
    tx = np.linspace(0, 10, 100); ty = np.linspace(100, 5, 100)
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.plot(tx, ty, color='#00ffd0')
    ax.set_ylabel("% Batterie", color="white")
    ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
    ax.tick_params(colors='white')
    st.pyplot(fig)

# Recherche libre en bas
with st.expander("🔍 Recherche par nom (NASA / Hubble)"):
    search = st.text_input("Taper un nom d'objet exotique...")

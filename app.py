import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy import units as u
from astropy.time import Time

# --- CONFIGURATION PRO ---
st.set_page_config(page_title="AstroPépites v6 : Deep Sky Hunter", layout="wide")

# --- BASES DE DONNÉES ÉTENDUES ---
FILTERS_DB = {
    "Svbony SV220 (Dual Band)": {"factor": 3.5, "type": "Narrowband"},
    "Optolong L-Pro": {"factor": 1.5, "type": "RGB/L"},
    "Sans filtre / UV-IR Cut": {"factor": 1.0, "type": "RGB"}
}

TARGETS_PRO = [
    {"name": "Arp 188 (Têtard)", "rarity": 95, "type": "Galaxie", "desc": "Quasi jamais vue en amateur.", "exposure": 600},
    {"name": "Abell 31", "rarity": 88, "type": "Nébuleuse P.", "desc": "Extrêmement diffuse, défi OIII.", "exposure": 300},
    {"name": "Ou4 (Le Calmar)", "rarity": 98, "type": "Nébuleuse", "desc": "La cible la plus dure du ciel boréal.", "exposure": 900},
    {"name": "Sh2-129", "rarity": 82, "type": "Nébuleuse", "desc": "Nécessite beaucoup de Ha.", "exposure": 300},
    {"name": "M31 (Andromède)", "rarity": 5, "type": "Galaxie", "desc": "L'objet le plus photographié.", "exposure": 120}
]

# --- SIDEBAR : CALCUL DE CHARGE & MATÉRIEL ---
st.sidebar.title("🚀 SETUP LOGISTIQUE")
sel_ps = st.sidebar.selectbox("Batterie Nomade", ["Bluetti EB3A (268Wh)", "Jackery 500"])
sel_scope = st.sidebar.selectbox("Optique", ["Sky-Watcher Evolux 62ED"])

st.sidebar.subheader("⚖️ Poids sur la GTi")
poids_tube = 2.5 # Evolux 62ED
poids_cam = 0.5  # ASI 183MC
poids_accessoires = st.sidebar.slider("Accessoires (Guide, Cables, EAF) kg", 0.5, 3.0, 1.2)
poids_total = poids_tube + poids_cam + poids_accessoires

max_gti = 5.0
charge_utile = (poids_total / max_gti) * 100

if charge_utile > 90:
    st.sidebar.error(f"⚠️ CHARGE : {poids_total:.1f}kg ({charge_utile:.0f}%) - Trop lourd !")
else:
    st.sidebar.success(f"✅ CHARGE : {poids_total:.1f}kg ({charge_utile:.0f}%)")

# --- INTERFACE PRINCIPALE ---
st.title("🌌 AstroPépites : Planificateur de Raretés")

# --- SÉLECTION CIBLE & SCORE DE RARETÉ ---
st.header("🎯 Analyse de la cible")
sel_obj_name = st.selectbox("Sélectionner une cible", [t["name"] for t in TARGETS_PRO])
t_data = next(t for t in TARGETS_PRO if t["name"] == sel_obj_name)

col_rarity, col_desc = st.columns([1, 2])

with col_rarity:
    # Score de rareté (simulant un index Astrobin)
    rarity_color = "red" if t_data['rarity'] > 80 else "orange" if t_data['rarity'] > 50 else "green"
    st.markdown(f"""
        <div style="text-align:center; border:2px solid {rarity_color}; padding:20px; border-radius:15px;">
            <h1 style="color:{rarity_color}; margin:0;">{t_data['rarity']}%</h1>
            <p style="margin:0;">SCORE DE RARETÉ</p>
        </div>
    """, unsafe_allow_html=True)

with col_desc:
    st.subheader(t_data['name'])
    st.write(f"**Type :** {t_data['type']}")
    st.info(f"**L'avis de l'expert :** {t_data['desc']}")

# --- CALCULATEUR D'EXPOSITION (ASIAIR) ---
st.divider()
st.subheader("📸 Paramètres d'acquisition (ASIAIR)")
sel_filter = st.selectbox("Filtre utilisé pour cette session", list(FILTERS_DB.keys()))

base_exp = t_data['exposure']
filter_mult = FILTERS_DB[sel_filter]['factor']
final_exp = base_exp * filter_mult

c1, c2, c3 = st.columns(3)
c1.metric("Pose Unitaire conseillée", f"{int(final_exp)} s")
c2.metric("Gain ASIAIR (ASI183)", "111 (Unity)")
c3.metric("Température Capteur", "-10°C")

st.warning(f"💡 Avec le filtre **{sel_filter}**, vous devez poser **{filter_mult}x plus longtemps** qu'en RGB pour obtenir un signal propre sur cette cible rare.")

# --- HORIZON & ÉNERGIE ---
st.divider()
st.subheader("🔋 Logistique Bluetti & Horizon")

# Consommation estimée
amps = 3.5 # Consommation moyenne avec ASIAIR + Monture + 183MC + Chauffage
autonomie = 22 / amps # Pour la Bluetti EB3A (22Ah)

col_batt, col_graph = st.columns([1, 2])

with col_batt:
    st.write(f"**Batterie :** Bluetti EB3A")
    st.write(f"**Conso estimée :** {amps} A")
    st.metric("Autonomie totale", f"{autonomie:.1f} h")
    st.progress(min(1.0, autonomie/10), "Capacité de nuit")

with col_graph:
    # Simulation graphique de visibilité
    h_data = np.linspace(0, 10, 50)
    alt_data = 30 + 40 * np.sin(h_data/2) # Courbe bidon pour illustration
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(h_data, alt_data, color="#00ffcc")
    ax.axhline(20, color="red", linestyle="--", label="Horizon")
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")
    st.pyplot(fig)

# --- EXPORT FINAL ---
st.divider()
st.subheader("📲 Envoyer la séquence vers l'ASIAIR")
if st.button("Générer le récapitulatif de session"):
    recap = f"""
    CONFIG SESSION :
    Cible : {sel_obj_name}
    RA/DEC : {t_data['name']}
    Filtre : {sel_filter}
    Pose : {int(final_exp)}s
    Autonomie : {autonomie:.1f}h
    """
    st.code(recap)
    st.success("Copié dans le journal ! Prêt pour le collage dans l'app ASIAIR.")

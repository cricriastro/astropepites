import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="AstroPépites Pro", layout="wide")

# --- FONCTION MÉTÉO ---
def get_weather():
    api_key = "16f68f1e07fea20e39f52de079037925"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat=46.65&lon=6.91&appid={api_key}&units=metric"
    try:
        return requests.get(url).json()['list'][:8]
    except: return None

# --- SIDEBAR : TÉLÉMÉTRIE & RÉGLAGES (Inspiration ASIAIR) ---
st.sidebar.title("🛰️ ASIAIR Control Panel")

# 1. Météo Vignette
with st.sidebar.expander("☁️ Météo (Romont)", expanded=True):
    forecast = get_weather()
    if forecast:
        # Affichage compact en liste
        for s in forecast[:4]: # Les 12 prochaines heures
            h = datetime.fromtimestamp(s['dt']).strftime('%H:%M')
            n = s['clouds']['all']
            st.write(f"**{h}** : {'🟢' if n<20 else '🔴'} {n}% nuages")

# 2. Énergie & Batterie
with st.sidebar.expander("🔋 Power Management", expanded=True):
    w_total = st.sidebar.slider("Conso Totale (W)", 5, 60, 25)
    autonomie = (268 * 0.85) / w_total
    h_fin = datetime.now() + timedelta(hours=autonomie)
    st.metric("Autonomie EB3A", f"{autonomie:.1f}h")
    st.caption(f"Coupure prévue à : {h_fin.strftime('%H:%M')}")

# 3. Boussole Horizon (Compacte)
with st.sidebar.expander("🧭 Horizon Local", expanded=False):
    h_n = st.number_input("Nord (°)", 0, 90, 20)
    h_s = st.number_input("Sud (°)", 0, 90, 15)
    st.write("Configuré pour Romont (46.65, 6.91)")

# --- INTERFACE PRINCIPALE ---
st.title("🔭 Planification Expert")

# SELECTION CIBLE : ACCÈS TOTAL
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    cat = st.selectbox("Catalogue", ["Messier", "NGC", "IC", "Spécial/Comètes"])
with c2:
    if cat in ["Messier", "NGC", "IC"]:
        target_num = st.number_input(f"Numéro {cat}", 1, 8000, 31)
        target = f"{cat[0] if cat=='Messier' else cat} {target_num}"
    else:
        target = st.selectbox("Événement", ["C/2023 A3", "Éclipse Solaire", "Perséides"])
with c3:
    filtre = st.selectbox("Filtre", ["Sans Filtre / Clair", "Svbony SV220 (Dual-Band)", "Optolong L-Pro", "UV/IR Cut"])

st.divider()

# ZONE DE VUE & ALERTES
col_img, col_info = st.columns([1, 2])

with col_img:
    # Vignette photo discrète
    st.image("https://via.placeholder.com/200x150.png?text=Target+View", caption=target)
    # Calcul échantillonnage
    focale = 400 # Valeur par défaut
    pixel = 3.76
    echantillon = (pixel / focale) * 206.265
    st.info(f"📐 Échantillonnage : {echantillon:.2f}\"/px")

with col_info:
    st.subheader("📋 Rapport d'Analyse")
    
    # ALERTES INTELLIGENTES
    if "SV220" in filtre:
        if "M 31" in target or "M 51" in target or "NGC" in target:
            st.warning("⚠️ **Mode Mixte recommandé** : Le SV220 isole le H-alpha. Capturez aussi des poses 'Sans Filtre' pour les détails galactiques.")
        elif "C/" in target or cat == "Spécial/Comètes":
            st.error("❌ **Alerte** : Le filtre Dual-Band bloque la queue de la comète. Utilisez un filtre clair.")
    
    elif "Sans Filtre" in filtre:
        if "Éclipse" in target or "Solaire" in target:
            st.error("🔥 **DANGER** : Pas de shoot solaire sans filtre frontal certifié !")
        else:
            st.success(f"✅ **Signal Continu** : Configuration idéale pour {target}.")

# Graphique de session (Profil de batterie)
st.write("📈 Courbe de décharge théorique")
tx = np.linspace(0, autonomie, 100); ty = np.linspace(100, 10, 100)
fig, ax = plt.subplots(figsize=(12, 2))
ax.plot(tx, ty, color='#00ffd0', lw=2)
ax.fill_between(tx, ty, color='#00ffd0', alpha=0.1)
ax.set_facecolor("#0e1117"); fig.patch.set_facecolor("#0e1117")
ax.tick_params(colors='white')
st.pyplot(fig)

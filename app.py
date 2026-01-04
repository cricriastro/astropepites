Skip to content
Navigation Menu
cricriastro
astropepites

Type / to search
Code
Issues
Pull requests
Actions
Projects
Wiki
Security
Insights
Settings
Commit 0018cfc
cricriastro
cricriastro
authored
31 minutes ago
Verified
Update app.py
main
1 parent 
d92736f
 commit 
0018cfc
File tree
Filter files…
app.py
1 file changed
+112
-14
lines changed
Search within code
 
‎app.py‎
+112
-14
Lines changed: 112 additions & 14 deletions
Original file line number	Diff line number	Diff line change
@@ -9,7 +9,7 @@
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval
import json 
from tzlocal import get_localzone # Importe le nouvel outil de fuseau horaire
from tzlocal import get_localzone 

# =========================
# CONFIGURATION API SÉCURISÉE (via st.secrets)
@@ -52,14 +52,41 @@
lon = st.sidebar.number_input("Longitude", value=st.session_state.get("lon", default_lon), format="%.4f")
location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
now = Time.now()
# Détermine le fuseau horaire local automatiquement
local_timezone = get_localzone()

# =========================
# MASQUE HORIZON (placeholders)
# MASQUE HORIZON
# =========================
def get_horizon_limit(az): return 15 
st.sidebar.header("🌲 Masque Horizon")
use_csv = st.sidebar.checkbox("Importer un CSV horizon")
csv_horizon = None
if use_csv:
    file = st.sidebar.file_uploader("Fichier (azimuth,altitude)", type="csv")
    if file: csv_horizon = pd.read_csv(file)
with st.sidebar.expander("Réglage manuel", expanded=not use_csv):
    m_vals = [st.slider(f"{d}", 0, 90, 15) for d in ["Nord", "NE", "Est", "SE", "Sud", "SW", "Ouest", "NW"]]
def get_horizon_limit(az):
    if csv_horizon is not None:
        return np.interp(az, csv_horizon.iloc[:,0], csv_horizon.iloc[:,1])
    idx = int(((az + 22.5) % 360) // 45)
    return m_vals[idx]
# Boussole Horizon (Corrigée et Robuste)
angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
fig_pol, ax_pol = plt.subplots(figsize=(3,3), subplot_kw={"projection":"polar"})
ax_pol.set_theta_zero_location("N")
ax_pol.set_theta_direction(-1)
angles_closed, m_vals_closed = np.append(angles, angles), np.append(m_vals, m_vals)
ax_pol.fill(angles_closed, m_vals_closed, color="red", alpha=0.4)
ax_pol.fill_between(angles_closed, m_vals_closed, 90, color="green", alpha=0.2)
ax_pol.set_yticklabels([])
ax_pol.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
ax_pol.set_facecolor("black")
fig_pol.patch.set_facecolor("black")
st.sidebar.pyplot(fig_pol)

# =========================
# CATALOGUES PRO & BASE DE DONNÉES D'OBJETS
@@ -72,14 +99,41 @@ def get_horizon_limit(az): return 15
]
popular_targets = ["M31 Andromède", "M42 Orion"]

# ... (TELESCOPES_DB, CAMERAS_DB, etc.) ...
# =========================
# BASES DE DONNÉES MATÉRIEL
# =========================
TELESCOPES_DB = {"SW Evolux 62 ED + Reducteur 0.85x": {"focal_length": 340, "aperture": 62}}
TELESCOPE_OPTIONS = list(TELESCOPES_DB.keys())
CAMERAS_DB = {"ZWO ASI 183 MC Pro": {"sensor_width_mm": 13.2, "sensor_height_mm": 8.8, "pixel_size_um": 2.4}}
CAMERA_OPTIONS = list(CAMERAS_DB.keys())
def calculate_fov(focal_length_mm, sensor_size_mm): return 1.0 

# ... (FONCTIONS API D'IMAGES (NASA) ici) ...
# =========================
# FONCTIONS UTILITAIRES
# =========================
def calculate_fov(focal_length_mm, sensor_size_mm):
    """Calcule le champ de vision en degrés."""
    return (sensor_size_mm / focal_length_mm) * (180 / np.pi)
# =========================
# FONCTIONS API D'IMAGES (NASA)
# =========================
def get_nasa_image_url(target_name):
    params = {'q': target_name, 'media_type': 'image'}
    try:
        response = requests.get('images-api.nasa.gov', params=params)
        data = response.json()
        if data['collection']['metadata']['total_hits'] > 0:
            image_links_url = data['collection']['items'][0]['href']
            links_response = requests.get(image_links_url)
            links_data = links_response.json()
            for link in links_data:
                if link.endswith('.jpg') or link.endswith('.png'):
                    return link
    except requests.exceptions.RequestException as e: st.sidebar.error(f"Erreur NASA API: {e}")
    except (IndexError, KeyError) as e: st.sidebar.error(f"Erreur de parsing NASA API: {e}")
    return None

# =========================
# CONFIGURATION CIBLES (Sidebar)
@@ -106,7 +160,6 @@ def calculate_fov(focal_length_mm, sensor_size_mm): return 1.0
                coord = SkyCoord(o["ra"], o["dec"], unit=(u.hourangle,u.deg))
                altaz = coord.transform_to(AltAz(obstime=now,location=location))
                o["visible_now"] = altaz.alt.deg > get_horizon_limit(altaz.az.deg)
                # Utilise maintenant le fuseau horaire local correct
                o["rise_time"] = now.to_datetime(timezone=local_timezone).strftime("%H:%M") 
                o["set_time"] = (now + 12*u.hour).to_datetime(timezone=local_timezone).strftime("%H:%M") 
                filtered_objects.append(o)
@@ -123,14 +176,50 @@ def calculate_fov(focal_length_mm, sensor_size_mm): return 1.0
        st.write(f"Altitude actuelle : {altaz.alt:.1f} | Azimut : {altaz.az:.1f}")
        st.write(f"Se lève vers : **{obj['rise_time']}**")
        st.write(f"Se couche vers : **{obj['set_time']}**")
    # ... (Reste de l'onglet 1) ...
# --- TAB 2, 3, 4, 5 (inchangés) ---
# ... (Vos onglets Astrophoto Infos, Matériel, Météo, Exports) ...
    with col2:
        times = now + np.linspace(0,12,30)*u.hour
        alts=[coord.transform_to(AltAz(obstime=t,location=location)).alt.deg for t in times]
        chart_data = pd.DataFrame({"Altitude":alts}) 
        st.line_chart(chart_data)
# --- TAB 2 : ASTROPHOTO INFOS & IMAGES RÉELLES ---
with tab2:
    st.subheader(f"Conseils d'imagerie pour {target_name}")
    st.info(f"{obj['conseil']}")
    st.subheader(f"Images réelles de {target_name} (Source NASA)")
    image_url = get_nasa_image_url(target_name)
    if image_url: st.image(image_url, caption=f"Image de {target_name} (Source NASA API)", use_column_width=True)
    else: st.warning("Pas d'image disponible pour cette cible via l'API NASA.")
# --- TAB 3 : MATÉRIEL & FOV ---
with tab3:
    st.subheader("Configuration d'imagerie et Champ de Vision (FOV)")
    col_scope, col_cam = st.columns(2)
    with col_scope: selected_scope = st.selectbox("Télescope principal", TELESCOPE_OPTIONS, index=0)
    with col_cam: selected_camera = st.selectbox("Caméra principale", CAMERA_OPTIONS, index=0)
    scope_data = TELESCOPES_DB[selected_scope]
    cam_data = CAMERAS_DB[selected_camera]
    focal_length = scope_data["focal_length"]
    fov_width_deg = calculate_fov(focal_length, cam_data["sensor_width_mm"])
    fov_height_deg = calculate_fov(focal_length, cam_data["sensor_height_mm"])
    st.markdown(f"**Focale utilisée :** `{focal_length}mm`")
    col_fov1, col_fov2 = st.columns(2)
    with col_fov1: st.metric("FOV Largeur", f"{fov_width_deg:.2f}° / {fov_width_deg*60:.0f}'")
    with col_fov2: st.metric("FOV Hauteur", f"{fov_height_deg:.2f}° / {fov_height_deg*60:.0f}'")
    target_size_arcmin = obj["size_arcmin"]
    st.subheader(f"Recommandation Mosaïque pour {target_name}")
    if target_size_arcmin > (fov_width_deg * 60) * 1.5: st.warning(f"⚠️ La cible est grande ({round(target_size_arcmin/60,1)}°)! Mosaïque 2x2 ou plus.")
    else: st.success(f"✅ La cible devrait rentrer sans problème dans votre champ de vision actuel.")
# --- TAB 4 : MÉTÉO ---
with tab4:
    st.subheader("Prévisions Météo (5 jours)")
    try:
        # CORRECTION DE L'URL : Ajout de "https://"
        weather_url = f"api.openweathermap.org{lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=fr"
        response = requests.get(weather_url)
        weather_data = response.json()
@@ -141,3 +230,12 @@ def calculate_fov(focal_length_mm, sensor_size_mm): return 1.0
            st.dataframe(df_weather)
        else: st.error(f"Erreur API météo: {weather_data['message']}")
    except requests.exceptions.RequestException as e: st.error(f"Erreur de connexion météo: {e}")
# --- TAB 5 : EXPORTS ---
with tab5:
    st.subheader("📋 Coordonnées pour votre monture")
    st.code(f"TARGET: {target_name}\nRA: {coord.ra.to_string(unit=u.hour)}\nDEC = {coord.dec.to_string(unit=u.deg)}")
    df = pd.DataFrame([{"name":target_name, "ra":coord.ra.deg, "dec":coord.dec.deg, "alt":round(altaz.alt.deg,1), "az":round(altaz.az.deg,1)}])
    st.download_button("Télécharger CSV", df.to_csv(index=False), file_name="astropepites_target.csv")
0 commit comments
Comments
0
 (0)
Comment
You're not receiving notifications from this thread.

 

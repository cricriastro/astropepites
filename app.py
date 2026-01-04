`python
-- coding: utf-8 --
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timedelta
from streamlitjseval import streamlitjseval
import json
from tzlocal import get_localzone
import math
-------------------------
INIT session_state safe
-------------------------
if "lat" not in st.session_state:
st.session_state.lat = 46.8
if "lon" not in st.session_state:
st.session_state.lon = 7.1
=========================
CONFIGURATION API SÉCURISÉE (via st.secrets)
=========================
try:
OPENWEATHERAPIKEY = st.secrets["openweather"]["api_key"]
NASAAPIKEY = st.secrets["nasa"]["api_key"] # pas utilisé dans images-api mais ok si besoin
except Exception as e:
st.error(f"Erreur de configuration des secrets: {e}. Avez-vous configuré secrets.toml ?")
st.stop()
=========================
CONFIG PAGE & STYLE
=========================
st.setpageconfig(page_title="AstroPépites Pro – Pro Edition", layout="wide")
st.markdown(
"""

""", unsafeallowhtml=True
)
=========================
GÉOLOCALISATION GPS AUTOMATIQUE
=========================
st.sidebar.title("🔭 AstroPépites Pro")
attempt to get browser geolocation; may be None if user refuses or script not available
try:
loc = streamlitjseval(datakey="geo", functionname="getCurrentPosition", delay=100)
except Exception:
loc = None

defaultlat, defaultlon = 46.8, 7.1
if loc and isinstance(loc, dict) and "coords" in loc:
st.sessionstate.lat = loc["coords"].get("latitude", st.sessionstate.lat)
st.sessionstate.lon = loc["coords"].get("longitude", st.sessionstate.lon)

lat = st.sidebar.numberinput("Latitude", value=float(st.sessionstate.get("lat", default_lat)), format="%.4f")
lon = st.sidebar.numberinput("Longitude", value=float(st.sessionstate.get("lon", default_lon)), format="%.4f")
location = EarthLocation(lat=lat u.deg, lon=lon u.deg)
now = Time.now()
localtimezone = getlocalzone()
=========================
MASQUE HORIZON
=========================
st.sidebar.header("🌲 Masque Horizon")
use_csv = st.sidebar.checkbox("Importer un CSV horizon")
csv_horizon = None
if use_csv:
file = st.sidebar.file_uploader("Fichier (azimuth,altitude)", type="csv")
if file:
try:
csvhorizon = pd.readcsv(file, header=None)
ensure columns: az, alt
if csv_horizon.shape[1] >= 2:
csvhorizon = csvhorizon.iloc[:, :2]
else:
st.sidebar.warning("CSV doit contenir au moins 2 colonnes: azimuth, altitude")
csv_horizon = None
except Exception as e:
st.sidebar.error(f"Impossible de lire le CSV: {e}")
csv_horizon = None

with st.sidebar.expander("Réglage manuel", expanded=not use_csv):
m_vals = [
st.slider(f"{d}", 0, 90, 15, key=f"h_{d}") for d in
["Nord", "NE", "Est", "SE", "Sud", "SW", "Ouest", "NW"]
]

def gethorizonlimit(az):
"""Retourne l'altitude limite du horizon pour un azimut en degrés."""
if csv_horizon is not None:
try:
azs = csv_horizon.iloc[:, 0].values
alts = csv_horizon.iloc[:, 1].values
return float(np.interp(az % 360, azs, alts))
except Exception:
return float(m_vals[int(((az + 22.5) % 360) // 45)])
idx = int(((az + 22.5) % 360) // 45)
return float(m_vals[idx])
Polar horizon plot
angles = np.linspace(0, 2 * np.pi, 8, endpoint=False)
figpol, axpol = plt.subplots(figsize=(3, 3), subplot_kw={"projection": "polar"})
axpol.setthetazerolocation("N")
axpol.settheta_direction(-1)
angles_closed = np.append(angles, angles[0])
mvalsradial = np.array(m_vals)
mvalsclosed = np.append(mvalsradial, mvalsradial[0])
axpol.fill(anglesclosed, mvalsclosed, color="red", alpha=0.4)
axpol.fillbetween(anglesclosed, mvals_closed, 90, color="green", alpha=0.2)
axpol.setyticklabels([])
axpol.setxticks(angles)
axpol.setxticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
axpol.setfacecolor("black")
figpol.patch.setfacecolor("black")
st.sidebar.pyplot(fig_pol)
=========================
CATALOGUES PRO & BASE DE DONNÉES D'OBJETS
=========================
catalog_pro = [
{"name": "M31 Andromède", "ra": "00:42:44", "dec": "+41:16:09", "type": "Galaxie", "size_arcmin": 180 * 60,
"conseil": "Idéale pour grande focale."},
{"name": "M42 Orion", "ra": "05:35:17", "dec": "-05:23:28", "type": "Nébuleuse", "size_arcmin": 60 * 60,
"conseil": "Centre très lumineux."},
{"name": "M51 Whirlpool", "ra": "13:29:52", "dec": "+47:11:43", "type": "Galaxie", "size_arcmin": 11 * 60,
"conseil": "Nécessite une bonne focale."},
{"name": "NGC 891", "ra": "02:22:33", "dec": "+42:20:50", "type": "Galaxie", "size_arcmin": 13 * 60,
"conseil": "Galaxie de profil, peu lumineuse."},
]
popular_targets = ["M31 Andromède", "M42 Orion"]
=========================
BASES DE DONNÉES MATÉRIEL
=========================
TELESCOPESDB = {"SW Evolux 62 ED + Reducteur 0.85x": {"focallength": 340, "aperture": 62}}
TELESCOPEOPTIONS = list(TELESCOPESDB.keys())
CAMERASDB = {"ZWO ASI 183 MC Pro": {"sensorwidthmm": 13.2, "sensorheightmm": 8.8, "pixelsize_um": 2.4}}
CAMERAOPTIONS = list(CAMERASDB.keys())
=========================
FONCTIONS UTILITAIRES
=========================
def calculatefov(focallengthmm, sensorsize_mm):
"""Calcule le champ de vision en degrés (formule géométrique exacte)."""
angle = 2 arctan(sensor / (2 focal))
fovrad = 2.0 np.arctan((sensorsizemm) / (2.0 focallength_mm))
return float(np.degrees(fov_rad))

def getnasaimageurl(targetname):
"""Recherche une image via l'API images-api.nasa.gov et retourne un href d'image si trouvé."""
url = "https://images-api.nasa.gov/search"
params = {"q": targetname, "mediatype": "image"}
try:
resp = requests.get(url, params=params,
Le chatbot a écrit :as e:
st.sidebar.error(f"Erreur NASA API: {e}")
return None
except Exception as e:
st.sidebar.error(f"Parsing NASA API: {e}")
return None

def getopenweatherforecast(lat, lon, api_key, units="metric"):
"""Retourne un dict simple de prévisions (One Call v2)."""
url = "https://api.openweathermap.org/data/2.5/onecall"
params = {"lat": lat, "lon": lon, "appid": api_key, "units": units, "exclude": "minutely,alerts"}
try:
r = requests.get(url, params=params, timeout=8)
r.raiseforstatus()
return r.json()
except Exception as e:
st.warning(f"Erreur météo: {e}")
return None

def computeriseset(coord, location, horizon_deg=0.0, hours=24, steps=144):
"""
Approximate rise/set times in the next hours hours by sampling.
Retourne (risetimedt or None, settimedt or None).
"""
ts = now + np.linspace(0, hours, steps) * u.hour
alts = np.array([coord.transform_to(AltAz(obstime=t, location=location)).alt.deg for t in ts])
above = alts > horizon_deg
find rising edge: False->True, falling: True->False
rise_idx = None
set_idx = None
for i in range(len(above) - 1):
if (not above[i]) and above[i + 1]:
rise_idx = i
break
for i in range(len(above) - 1):
if above[i] and (not above[i + 1]):
set_idx = i
break
def interp_time(i):
if i is None:
return None
a0, a1 = alts[i], alts[i + 1]
t0, t1 = ts[i], ts[i + 1]
linear interp on altitude
if a1 == a0:
frac = 0.0
else:
frac = (horizon_deg - a0) / (a1 - a0)
t = t0 + frac * (t1 - t0)
return t.todatetime(timezone=localtimezone)
risedt = interptime(rise_idx)
setdt = interptime(set_idx)
return risedt, setdt
=========================
CONFIGURATION CIBLES (Sidebar)
=========================
st.sidebar.header("🔭 Catalogues & Cibles")
use_messier = st.sidebar.checkbox("Afficher Messier", value=True)
use_ngc = st.sidebar.checkbox("Afficher NGC/IC", value=True)
filter_rare = st.sidebar.checkbox("🎯 Cibles peu communes uniquement", value=False)
=========================
TABS
=========================
st.title("🔭 AstroPépites Pro – Pro Edition")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎞️ Cibles & Radar", "🖼️ Astrophoto Infos", "⚙️ Mon Matériel & FOV", "🌤️ Météo", "🗂 Exports"])
--- TAB 1 : RADAR ---
with tab1:
filtered_objects = []
for o in catalog_pro:
is_messier = o["name"].startswith("M")
is_ngc = o["name"].startswith("NGC") or o["name"].startswith("IC")
if (usemessier and ismessier) or (usengc and isngc) or (not (ismessier or isngc)):
if not filterrare or (o["name"] not in populartargets):
try:
coord = SkyCoord(o["ra"], o["dec"], unit=(u.hourangle, u.deg))
altaz = coord.transform_to(AltAz(obstime=now, location=location))
horizonlimit = gethorizon_limit(altaz.az.deg)
o["visiblenow"] = float(altaz.alt.deg) > float(horizonlimit)
risedt, setdt = computeriseset(coord, location, horizondeg=horizonlimit, hours=24, steps=240)
o["risetime"] = risedt.strftime("%Y-%m-%d %H:%M") if rise_dt else "—"
o["settime"] = setdt.strftime("%Y-%m-%d %H:%M") if set_dt else "—"
o["alt_deg"] = float(altaz.alt.deg)
o["az_deg"] = float(altaz.az.deg)
filtered_objects.append(o)
except Exception as e:
st.error(f"Erreur calcul position pour {o['name']}: {e}")
filteredobjects.sort(key=lambda x: x.get("visiblenow", False), reverse=True)
if filtered_objects:
targetname = st.selectbox("Choisir une cible", [o["name"] for o in filteredobjects])
obj = next(o for o in filteredobjects if o["name"] == targetname)
coord = SkyCoord(obj["ra"], obj["dec"], unit=(u.hourangle, u.deg))
altaz = coord.transform_to(AltAz(obstime=now, location=location))
status = "VISIBLE" if obj["visible_now"] else "MASQUÉ"
st.subheader(f"{target_name} – {status}")
col1, col2 = st.columns(2)
with col1:
st.write(f"Altitude actuelle : {altaz.alt:.1f}° | Azimut : {altaz.az:.1f}°")
st.write(f"Se lève vers : {obj['rise_time']}")
st.write(f"Se couche vers : {obj['set_time']}")
with col2:
times = now + np.linspace(0, 12, 30) * u.hour
alts = [coord.transform_to(AltAz(obstime=t, location=location)).alt.deg for t in times]
chart_data = pd.DataFrame({"Altitude": alts})
st.linechart(chartdata)
else:
st.info("Aucun objet filtré à afficher.")
--- TAB 2 : ASTROPHOTO INFOS & IMAGES RÉELLES ---
with tab2:
st.subheader("Conseils d'imagerie")
if 'obj' in locals():
st.info(f"{obj.get('conseil','')}")
st.subheader(f"Images réelles de {obj['name']} (Source NASA)")
imageurl = getnasaimageurl(obj['name'])
if image_url:
st.image(imageurl, caption=f"Image de {obj['name']} (Source NASA API)", usecolumn_width=True)
else:
st.warning("Pas d'image disponible pour cette cible via l'API NASA.")
else:
st.info("Sélectionne d'abord une cible dans l'onglet Cibles & Radar.")
--- TAB 3 : MATÉRIEL & FOV ---
with tab3:
st.subheader("Configuration d'imagerie et Champ de Vision (FOV)")
colscope, colcam = st.columns(2)
with col_scope:
selectedscope = st.selectbox("Télescope principal", TELESCOPEOPTIONS, index=0)
with col_cam:
selectedcamera = st.selectbox("Caméra principale", CAMERAOPTIONS, index=0)
scopedata = TELESCOPESDB[selected_scope]
camdata = CAMERASDB[selected_camera]
focallength = scopedata["focal_length"]
fovwidthdeg = calculatefov(focallength, camdata["sensorwidth_mm"])
fovheightdeg = calculatefov(focallength, camdata["sensorheight_mm"])
st.markdown(f"Focale utilisée : {focal_length} mm")
colfov1, colfov2 = st.columns(2)
with col_fov1:
st.metric("FOV Largeur", f"{fovwidthdeg:.2f}° / {fovwidthdeg*60:.0f}'")
with col_fov2:
st.metric("FOV Hauteur", f"{fovheightdeg:.2f}° / {fovheightdeg*60:.0f}'")
if 'obj' in locals():
targetsizearcmin = obj["size_arcmin"]
st.subheader(f"Recommandation Mosaïque pour {obj['name']}")
if targetsizearcmin > (fovwidthdeg 60) 1.5:
st.warning(f"⚠️ La cible est grande ({round(targetsizearcmin/60,1)}°)! Mosaïque 2x2 ou plus.")
else:
st.success("⭐ La cible devrait rentrer sans problème dans votre champ de vision actuel.")
else:
st.info("Sélectionne d'abord une cible.")
--- TAB 4 : MÉTÉO ---
with tab4:
st.subheader("Prévisions Météo (OpenWeather)")
forecast = getopenweatherforecast(lat, lon, OPENWEATHERAPIKEY)
if forecast:
résumé simple jour par jour (daily)
daily = forecast.get("daily", [])
df = []
for d in daily[:5]:
dt = datetime.fromtimestamp(int(d["dt"]), tz=local_timezone)
temp = d.get("temp", {})
weather = d.get("weather", [{}])[0].get("description", "")
clouds = d.get("clouds", 0)
df.append({"date": dt.strftime("%Y-%m-%d"), "min": temp.get("min"), "max": temp.get("max"), "clouds%": clouds, "desc": weather})
st.table(pd.DataFrame(df))
else:
st.info("Prévisions météo indisponibles.")
--- TAB 5 : EXPORTS / UTILITAIRES ---
with tab5:
st.subheader("Exports")
if 'filteredobjects' in locals() and filteredobjects:
dfexport = pd.DataFrame(filteredobjects)
st.downloadbutton("Télécharger la liste CSV", dfexport.to_csv(index=False).encode('utf-8'), "cibles.csv")
else:
st.info("Aucune donnée à exporter.")
`

Remarques pratiques
- Assure-toi d’avoir installé les dépendances sur ton environnement Streamlit (requirements.txt) : streamlit, astropy, streamlit-js-eval, tzlocal, re

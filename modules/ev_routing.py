import math
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
from streamlit_folium import st_folium
import folium

ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
OCM_URL = "https://api.openchargemap.io/v3/poi/"


def _get_secret(name: str) -> Optional[str]:
    try:
        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:
        return None


def _http_debug(r: requests.Response) -> str:
    # Keep it short and safe
    txt = ""
    try:
        txt = r.text
    except Exception:
        txt = ""
    txt = (txt or "")[:800]
    return f"HTTP {r.status_code}\n{txt}"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


@st.cache_data(show_spinner=False)
def ors_geocode(text: str, country: str = "") -> Optional[Tuple[float, float, str]]:
    """
    Returns (lat, lon, label) using ORS geocoder.
    Robust:
    - tries with country filter if provided
    - falls back to no country filter
    """
    api_key = _get_secret("ORS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ORS_API_KEY in secrets.")

    def _call(params: dict) -> requests.Response:
        return requests.get(ORS_GEOCODE_URL, params=params, timeout=25)

    base_params = {
        "api_key": api_key,
        "text": text,
        "size": 1,
    }

    # attempt 1: with country filter
    if country:
        p1 = dict(base_params)
        p1["boundary.country"] = country
        r = _call(p1)
        if r.status_code == 200:
            data = r.json()
            feats = data.get("features", [])
            if feats:
                f0 = feats[0]
                lon, lat = f0["geometry"]["coordinates"]
                label = f0["properties"].get("label", text)
                return float(lat), float(lon), label

    # attempt 2: no country filter
    r2 = _call(base_params)
    if r2.status_code != 200:
        raise requests.HTTPError(_http_debug(r2), response=r2)

    data2 = r2.json()
    feats2 = data2.get("features", [])
    if not feats2:
        return None
    f0 = feats2[0]
    lon, lat = f0["geometry"]["coordinates"]
    label = f0["properties"].get("label", text)
    return float(lat), float(lon), label


@st.cache_data(show_spinner=False)
def ors_directions(start_lonlat: Tuple[float, float], end_lonlat: Tuple[float, float]) -> Dict[str, Any]:
    api_key = _get_secret("ORS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ORS_API_KEY in secrets.")

    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    body = {"coordinates": [[start_lonlat[0], start_lonlat[1]], [end_lonlat[0], end_lonlat[1]]]}

    r = requests.post(ORS_DIRECTIONS_URL, headers=headers, json=body, timeout=35)
    if r.status_code != 200:
        raise requests.HTTPError(_http_debug(r), response=r)

    data = r.json()
    feat = data["features"][0]
    summary = feat["properties"]["summary"]

    distance_km = float(summary["distance"]) / 1000.0
    duration_min = float(summary["duration"]) / 60.0

    line = feat["geometry"]["coordinates"]  # [lon, lat]
    coords_latlon = [(float(lat), float(lon)) for lon, lat in line]

    # optional steps (turn-by-turn)
    steps = []
    try:
        seg = feat["properties"]["segments"][0]
        for s in seg.get("steps", []):
            steps.append(
                {
                    "instruction": s.get("instruction", ""),
                    "distance_m": s.get("distance", 0),
                    "duration_s": s.get("duration", 0),
                }
            )
    except Exception:
        steps = []

    return {
        "distance_km": distance_km,
        "duration_min": duration_min,
        "coords_latlon": coords_latlon,
        "steps": steps,
    }


@st.cache_data(show_spinner=False)
def ocm_chargers_near(lat: float, lon: float, radius_km: float = 10.0, max_results: int = 30) -> List[Dict[str, Any]]:
    key = _get_secret("OCM_API_KEY")
    params = {
        "output": "json",
        "latitude": lat,
        "longitude": lon,
        "distance": radius_km,
        "distanceunit": "KM",
        "maxresults": max_results,
        "compact": "true",
        "verbose": "false",
    }
    if key:
        params["key"] = key

    r = requests.get(OCM_URL, params=params, timeout=35)
    if r.status_code != 200:
        # Don't fail routing if chargers fail
        return []
    return r.json()


def _pick_midpoint(coords_latlon: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not coords_latlon:
        return 0.0, 0.0
    return coords_latlon[len(coords_latlon) // 2]


def _best_charger(chargers: List[Dict[str, Any]], target_lat: float, target_lon: float) -> Optional[Dict[str, Any]]:
    best = None
    best_d = 1e9
    for c in chargers:
        addr = c.get("AddressInfo", {})
        lat = addr.get("Latitude")
        lon = addr.get("Longitude")
        if lat is None or lon is None:
            continue
        d = _haversine_km(target_lat, target_lon, float(lat), float(lon))
        if d < best_d:
            best_d = d
            best = c
    return best


def _render_map(
    start: Tuple[float, float],
    end: Tuple[float, float],
    route_coords: List[Tuple[float, float]],
    chargers: List[Dict[str, Any]],
    recommended: Optional[Dict[str, Any]],
):
    center = _pick_midpoint(route_coords) if route_coords else start
    m = folium.Map(location=center, zoom_start=12, control_scale=True, tiles="CartoDB dark_matter")

    folium.Marker(location=start, tooltip="Start", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(location=end, tooltip="Destination", icon=folium.Icon(color="red", icon="stop")).add_to(m)

    if route_coords:
        folium.PolyLine(route_coords, weight=5, opacity=0.85).add_to(m)

    for c in chargers:
        addr = c.get("AddressInfo", {})
        lat = addr.get("Latitude")
        lon = addr.get("Longitude")
        if lat is None or lon is None:
            continue
        title = addr.get("Title", "Charging Station")
        town = addr.get("Town", "")
        pop = f"<b>{title}</b><br/>{town}"

        folium.CircleMarker(
            location=(float(lat), float(lon)),
            radius=6,
            opacity=0.9,
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(pop, max_width=320),
        ).add_to(m)

    if recommended:
        addr = recommended.get("AddressInfo", {})
        rlat = addr.get("Latitude")
        rlon = addr.get("Longitude")
        if rlat is not None and rlon is not None:
            title = addr.get("Title", "Recommended Stop")
            folium.Marker(
                location=(float(rlat), float(rlon)),
                tooltip="Recommended Charging Stop",
                popup=title,
                icon=folium.Icon(color="blue", icon="flash"),
            ).add_to(m)

    st_folium(m, width="100%", height=520)


def render():
    st.markdown("## EV Smart Routing")
    st.caption("Routing + map + EV charger overlay using OpenRouteService and OpenChargeMap.")

    if not _get_secret("ORS_API_KEY"):
        st.error("Missing ORS_API_KEY. Add it to .streamlit/secrets.toml or Streamlit Cloud Secrets.")
        return

    left, right = st.columns([2, 1], vertical_alignment="top")

    with left:
        st.markdown("### Route inputs")
        start_text = st.text_input("Start location", value="Quezon City, Metro Manila")
        end_text = st.text_input("Destination", value="Makati, Metro Manila")
        country = st.text_input("Country code (optional)", value="PH", help="ISO country code (PH). Leave blank for global.")

    with right:
        st.markdown("### EV settings (optional)")
        range_km = st.number_input("Estimated range (km)", min_value=0.0, value=250.0, step=10.0)
        charger_radius = st.slider("Charger search radius (km)", min_value=2, max_value=30, value=10)
        max_chargers = st.slider("Max chargers to show", min_value=5, max_value=60, value=25)

    st.divider()

    if st.button("Compute Route", use_container_width=True):
        try:
            with st.spinner("Geocoding start/destination..."):
                start = ors_geocode(start_text, country=country.strip())
                end = ors_geocode(end_text, country=country.strip())
        except Exception as e:
            st.error("Geocoding failed.")
            st.code(str(e))
            st.info("Most common causes: wrong/expired ORS key, rate limit, or ORS service issue.")
            return

        if not start or not end:
            st.error("Could not geocode one or both locations. Try more specific addresses.")
            return

        start_lat, start_lon, start_label = start
        end_lat, end_lon, end_label = end

        try:
            with st.spinner("Computing route..."):
                route = ors_directions((start_lon, start_lat), (end_lon, end_lat))
        except Exception as e:
            st.error("Routing failed.")
            st.code(str(e))
            return

        distance_km = route["distance_km"]
        duration_min = route["duration_min"]
        coords_latlon = route["coords_latlon"]
        steps = route.get("steps", [])

        s1, s2, s3 = st.columns(3)
        s1.metric("Distance (km)", f"{distance_km:.1f}")
        s2.metric("ETA (minutes)", f"{duration_min:.0f}")
        s3.metric("Range check", "OK" if (range_km <= 0 or distance_km <= range_km) else "Needs charge")

        mid_lat, mid_lon = _pick_midpoint(coords_latlon)

        with st.spinner("Loading EV chargers near route..."):
            chargers = ocm_chargers_near(mid_lat, mid_lon, radius_km=float(charger_radius), max_results=int(max_chargers))

        recommended = None
        if range_km > 0 and distance_km > range_km and chargers:
            recommended = _best_charger(chargers, mid_lat, mid_lon)

        st.markdown("### Map")
        _render_map(
            start=(start_lat, start_lon),
            end=(end_lat, end_lon),
            route_coords=coords_latlon,
            chargers=chargers,
            recommended=recommended,
        )

        if steps:
            st.markdown("### Turn-by-turn (ORS)")
            for i, s in enumerate(steps[:20], start=1):
                st.write(f"{i}. {s['instruction']} — {s['distance_m']:.0f} m")

        st.markdown("### Charger list (near route midpoint)")
        if chargers:
            rows = []
            for c in chargers:
                addr = c.get("AddressInfo", {})
                rows.append(
                    {
                        "name": addr.get("Title", "Charging Station"),
                        "town": addr.get("Town", ""),
                        "address": addr.get("AddressLine1", ""),
                        "lat": addr.get("Latitude", ""),
                        "lon": addr.get("Longitude", ""),
                    }
                )
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("No chargers returned (or OpenChargeMap request failed). Increase radius or try another route.")

import math
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
from streamlit_folium import st_folium
import folium

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
OCM_URL = "https://api.openchargemap.io/v3/poi/"


def _get_secret(name: str) -> Optional[str]:
    try:
        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:
        return None


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
def geocode_nominatim(text: str, country_codes: str = "ph") -> Optional[Tuple[float, float, str]]:
    headers = {"User-Agent": "ToyotaDSS/1.0 (student project)"}
    params = {"q": text, "format": "json", "limit": 1}
    if country_codes:
        params["countrycodes"] = country_codes

    r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=25)
    if r.status_code != 200:
        return None
    data = r.json()
    if not data:
        return None

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    label = data[0].get("display_name", text)
    return lat, lon, label


@st.cache_data(show_spinner=False)
def route_osrm(start: Tuple[float, float], end: Tuple[float, float]) -> Dict[str, Any]:
    lat1, lon1 = start
    lat2, lon2 = end
    url = OSRM_ROUTE_URL.format(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
    params = {"overview": "full", "geometries": "geojson", "steps": "true"}

    r = requests.get(url, params=params, timeout=35)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"OSRM routing failed: {data.get('message', 'unknown')}")

    route = data["routes"][0]
    distance_km = float(route["distance"]) / 1000.0
    duration_min = float(route["duration"]) / 60.0

    coords = route["geometry"]["coordinates"]  # [lon, lat]
    coords_latlon = [(float(lat), float(lon)) for lon, lat in coords]

    steps_out = []
    try:
        legs = route.get("legs", [])
        if legs:
            for step in legs[0].get("steps", [])[:30]:
                man = step.get("maneuver", {})
                inst = man.get("instruction", "")
                dist = float(step.get("distance", 0.0))
                steps_out.append({"instruction": inst, "distance_m": dist})
    except Exception:
        steps_out = []

    return {
        "distance_km": distance_km,
        "duration_min": duration_min,
        "coords_latlon": coords_latlon,
        "steps": steps_out,
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


def _render_map(payload: Dict[str, Any]) -> None:
    start = payload["start"]          # (lat, lon)
    end = payload["end"]              # (lat, lon)
    route_coords = payload["route_coords"]  # [(lat, lon), ...]
    chargers = payload["chargers"]
    recommended = payload.get("recommended")

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

    # key keeps the widget stable across reruns
    st_folium(m, width="100%", height=520, key="ev_map")


def render():
    st.markdown("## EV Smart Routing")
    st.caption("OSRM (routing) + Nominatim (geocoding) + OpenChargeMap (chargers). Map persists after compute.")

    # init storage
    st.session_state.setdefault("ev_route_payload", None)

    left, right = st.columns([2, 1], vertical_alignment="top")

    with left:
        st.markdown("### Route inputs")
        start_text = st.text_input("Start location", value="Quezon City, Metro Manila")
        end_text = st.text_input("Destination", value="Makati, Metro Manila")
        country_codes = st.text_input("Country codes (optional)", value="ph", help="e.g., 'ph'. Leave blank for global.")

    with right:
        st.markdown("### EV settings (optional)")
        range_km = st.number_input("Estimated range (km)", min_value=0.0, value=250.0, step=10.0)
        charger_radius = st.slider("Charger search radius (km)", min_value=2, max_value=30, value=10)
        max_chargers = st.slider("Max chargers to show", min_value=5, max_value=60, value=25)

    c1, c2 = st.columns([1, 1])
    with c1:
        compute = st.button("Compute Route", use_container_width=True)
    with c2:
        if st.button("Clear Route", use_container_width=True):
            st.session_state["ev_route_payload"] = None
            st.rerun()

    if compute:
        with st.spinner("Geocoding..."):
            start = geocode_nominatim(start_text, country_codes=country_codes.strip())
            end = geocode_nominatim(end_text, country_codes=country_codes.strip())

        if not start or not end:
            st.error("Geocoding failed. Use more specific locations (city + area).")
            return

        start_lat, start_lon, _ = start
        end_lat, end_lon, _ = end

        try:
            with st.spinner("Computing route (OSRM)..."):
                route = route_osrm((start_lat, start_lon), (end_lat, end_lon))
        except Exception as e:
            st.error("Routing failed.")
            st.code(str(e))
            return

        distance_km = route["distance_km"]
        duration_min = route["duration_min"]
        coords_latlon = route["coords_latlon"]
        steps = route.get("steps", [])

        mid_lat, mid_lon = _pick_midpoint(coords_latlon)

        with st.spinner("Loading EV chargers near route..."):
            chargers = ocm_chargers_near(mid_lat, mid_lon, radius_km=float(charger_radius), max_results=int(max_chargers))

        recommended = None
        if range_km > 0 and distance_km > range_km and chargers:
            recommended = _best_charger(chargers, mid_lat, mid_lon)

        # store for persistence
        st.session_state["ev_route_payload"] = {
            "start": (start_lat, start_lon),
            "end": (end_lat, end_lon),
            "distance_km": distance_km,
            "duration_min": duration_min,
            "route_coords": coords_latlon,
            "steps": steps,
            "chargers": chargers,
            "recommended": recommended,
            "range_km": float(range_km),
        }
        st.rerun()

    # render persisted output
    payload = st.session_state.get("ev_route_payload")
    if payload:
        s1, s2, s3 = st.columns(3)
        s1.metric("Distance (km)", f"{payload['distance_km']:.1f}")
        s2.metric("ETA (minutes)", f"{payload['duration_min']:.0f}")
        s3.metric("Range check", "OK" if (payload["range_km"] <= 0 or payload["distance_km"] <= payload["range_km"]) else "Needs charge")

        st.markdown("### Map")
        _render_map(payload)

        steps = payload.get("steps") or []
        if steps:
            st.markdown("### Turn-by-turn (OSRM)")
            for i, s in enumerate(steps[:20], start=1):
                st.write(f"{i}. {s.get('instruction','')} — {float(s.get('distance_m',0)):.0f} m")

        chargers = payload.get("chargers") or []
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

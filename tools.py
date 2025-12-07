# backend/tools.py
import requests
from datetime import datetime, timedelta

class POIToolError(Exception):
    pass

def find_pois_osm(city: str, limit=10):
    """
    Return a list of POIs for the city using Nominatim & Overpass queries (simple approach).
    Each POI: {name, category, lat, lon, short_desc}
    """
    # 1) Geocode city to lat/lon
    geocode_url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    r = requests.get(geocode_url, params=params, headers={"User-Agent":"travel-agent/1.0"})
    if r.status_code != 200 or not r.json():
        raise POIToolError("City geocoding failed")
    geo = r.json()[0]
    lat, lon = float(geo["lat"]), float(geo["lon"])

    # 2) Use Overpass API to get POIs around the city center (amenity/tourism nodes)
    overpass_url = "https://overpass-api.de/api/interpreter"
    # Search within 10km radius for common POI tags
    radius = 10000
    query = f"""
    [out:json][timeout:25];
    (
      node["tourism"](around:{radius},{lat},{lon});
      node["historic"](around:{radius},{lat},{lon});
      node["amenity"="restaurant"](around:{radius},{lat},{lon});
      node["shop"](around:{radius},{lat},{lon});
    );
    out center {limit};
    """
    r2 = requests.post(overpass_url, data=query, headers={"User-Agent":"travel-agent/1.0"})
    if r2.status_code != 200:
        raise POIToolError("Overpass API failed")
    data = r2.json()
    pois = []
    seen = set()
    for el in data.get("elements", []):
        name = el.get("tags", {}).get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        category = el.get("tags", {}).get("tourism") or el.get("tags", {}).get("historic") or el.get("tags", {}).get("amenity") or el.get("tags", {}).get("shop","")
        pois.append({
            "name": name,
            "category": category or "attraction",
            "lat": el.get("lat") or el.get("center",{}).get("lat"),
            "lon": el.get("lon") or el.get("center",{}).get("lon"),
            "short_desc": el.get("tags", {}).get("description") or el.get("tags", {}).get("note","")
        })
        if len(pois) >= limit:
            break
    if not pois:
        raise POIToolError("No POIs found")
    return {"city": city, "center": {"lat": lat, "lon": lon}, "pois": pois}


class WeatherToolError(Exception):
    pass

def get_weather_open_meteo(lat: float, lon: float, start_date: str, end_date: str):
    """
    Query Open-Meteo for daily weather summary between start_date and end_date (YYYY-MM-DD).
    Returns [{'date':..., 'summary': 'Sunny, 34°C', 'max_temp':..., 'min_temp':...}, ...]
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "timezone": "UTC"
    }
    r = requests.get(url, params=params, headers={"User-Agent":"travel-agent/1.0"})
    if r.status_code != 200:
        raise WeatherToolError("Open-Meteo API request failed")
    data = r.json()
    daily = []
    dates = data.get("daily", {}).get("time", [])
    temps_max = data.get("daily", {}).get("temperature_2m_max", [])
    temps_min = data.get("daily", {}).get("temperature_2m_min", [])
    codes = data.get("daily", {}).get("weathercode", [])
    # Map weather code to text (simple)
    wc_map = {
        0: "Clear",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        61: "Rain",
        63: "Rain showers",
        71: "Snow",
        80: "Rain showers",
    }
    for i,d in enumerate(dates):
        code = codes[i] if i < len(codes) else None
        summary = wc_map.get(code, "Mixed")
        max_t = temps_max[i] if i < len(temps_max) else None
        min_t = temps_min[i] if i < len(temps_min) else None
        daily.append({
            "date": d,
            "summary": f"{summary}, max {max_t}°C, min {min_t}°C" if max_t is not None else summary,
            "max_temp": max_t,
            "min_temp": min_t,
            "weathercode": code
        })
    return {"lat": lat, "lon": lon, "daily": daily}

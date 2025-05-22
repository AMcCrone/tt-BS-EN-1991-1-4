import folium
import requests
from streamlit_folium import st_folium
from geopy.distance import geodesic


def render_map(
    center_lat: float = 51.5,
    center_lon: float = -0.1,
    zoom_start: int = 6,
    width: int = 700,
    height: int = 450,
) -> dict:
    """
    Renders a Folium map in Streamlit and returns the click event data.
    """
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    return st_folium(m, width=width, height=height)


def get_elevation(lat: float, lon: float) -> float:
    """
    Fetches elevation (in meters) for given coordinates using Open-Elevation API.
    """
    url = "https://api.open-elevation.com/api/v1/lookup"
    params = {"locations": f"{lat},{lon}"}
    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()["results"][0]["elevation"]


def compute_distance(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """
    Computes the great-circle distance (in kilometers) between two (lat, lon) pairs.
    """
    return geodesic(coord1, coord2).kilometers

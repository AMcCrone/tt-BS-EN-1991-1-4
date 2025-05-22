import folium
import requests
from streamlit_folium import st_folium
from geopy.distance import geodesic


def render_map_with_markers(
    markers: list,
    center_lat: float = 51.5,
    center_lon: float = -0.1,
    zoom_start: int = 6,
    width: int = 700,
    height: int = 450,
) -> dict:
    """
    Renders a Folium map in Streamlit with existing markers and returns the click event data.
    """
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    
    # Add existing markers
    for idx, (lat, lon) in enumerate(markers, start=1):
        folium.Marker(
            location=[lat, lon],
            popup=f"Point {idx}: ({lat:.5f}, {lon:.5f})",
            tooltip=f"Point {idx}",
            icon=folium.Icon(color='red' if idx == 1 else 'blue', icon='info-sign')
        ).add_to(m)
    
    # If we have markers, adjust the map view to show them
    if markers:
        if len(markers) == 1:
            # Center on the single marker
            m.location = list(markers[0])
            m.zoom_start = 10
        else:
            # Fit bounds to show both markers
            bounds = [[lat, lon] for lat, lon in markers]
            m.fit_bounds(bounds, padding=(20, 20))
    
    return st_folium(m, width=width, height=height, key="map")


def get_elevation(lat: float, lon: float) -> float:
    """
    Fetches elevation (in meters) for given coordinates using Open-Elevation API.
    """
    url = "https://api.open-elevation.com/api/v1/lookup"
    params = {"locations": f"{lat},{lon}"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()["results"][0]["elevation"]


def compute_distance(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """
    Computes the great-circle distance (in kilometers) between two (lat, lon) pairs.
    """
    return geodesic(coord1, coord2).kilometers

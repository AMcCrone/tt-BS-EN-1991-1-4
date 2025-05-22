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
    # Define colors
    TT_Orange = "rgb(211,69,29)"
    TT_DarkBlue = "rgb(0,48,60)"
    TT_LightBlue = "rgb(136,219,223)"
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, tiles="Cartodb Positron")
    
    # Add existing markers
    for idx, (lat, lon) in enumerate(markers, start=1):
        if idx == 1:
            # Project Location marker (building symbol)
            folium.Marker(
                location=[lat, lon],
                popup=f"Project Location: ({lat:.5f}, {lon:.5f})",
                tooltip="Project Location",
                icon=folium.Icon(color='orange', icon='home', prefix='fa')
            ).add_to(m)
        elif idx == 2:
            # Closest Sea Location marker (water symbol)
            folium.Marker(
                location=[lat, lon],
                popup=f"Closest Sea Location: ({lat:.5f}, {lon:.5f})",
                tooltip="Closest Sea Location",
                icon=folium.Icon(color='darkblue', icon='ship', prefix='fa')
            ).add_to(m)
    
    # Add dashed line connecting the two points if we have exactly 2 markers
    if len(markers) == 2:
        # Calculate distance
        distance_km = geodesic(markers[0], markers[1]).kilometers
        
        # Add the dashed line
        folium.PolyLine(
            locations=markers,
            color=TT_LightBlue,
            weight=3,
            opacity=0.8,
            dash_array='10, 5'  # Creates dashed line pattern
        ).add_to(m)
        
        # Add distance label at the midpoint
        midpoint_lat = (markers[0][0] + markers[1][0]) / 2
        midpoint_lon = (markers[0][1] + markers[1][1]) / 2
        
        folium.Marker(
            location=[midpoint_lat, midpoint_lon],
            popup=f"Distance to Sea: {distance_km:.2f} km",
            tooltip=f"Distance to Sea: {distance_km:.2f} km",
            icon=folium.DivIcon(
                html=f'<div style="background-color: {TT_LightBlue}; color: black; padding: 5px; border-radius: 5px; font-weight: bold; font-size: 12px; white-space: nowrap;">Distance to Sea: {distance_km:.2f} km</div>',
                icon_size=(150, 30),
                icon_anchor=(75, 15)
            )
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

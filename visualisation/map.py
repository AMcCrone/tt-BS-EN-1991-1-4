import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from geopy.distance import geodesic
from educational import text_content


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
    TT_MidBlue = "rgb(0,163,173)"
    
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
                icon=folium.Icon(color='darkorange', icon='home', prefix='fa')
            ).add_to(m)
        elif idx == 2:
            # Closest Sea Location marker (water symbol)
            folium.Marker(
                location=[lat, lon],
                popup=f"Closest Sea Location: ({lat:.5f}, {lon:.5f})",
                tooltip="Closest Sea Location",
                icon=folium.Icon(color='darkblue', icon='ship', prefix='fa')
            ).add_to(m)
    
    # Add dashed circle centered at point 1 with radius = distance to point 2
    if len(markers) == 2:
        # Calculate distance from point 1 to point 2
        distance_km = geodesic(markers[0], markers[1]).kilometers
        # Convert distance to meters for the circle radius
        radius_meters = distance_km * 1000
        
        # Add the dashed circle centered at point 1
        folium.Circle(
            location=markers[0],  # Center at point 1 (Project Location)
            radius=radius_meters,
            color=TT_LightBlue,
            weight=3,
            opacity=0.8,
            fill=False,  # No fill, just the outline
            dashArray='10, 5'  # Creates dashed line pattern
        ).add_to(m)
        
        # Add solid line connecting the two points
        folium.PolyLine(
            locations=markers,
            color=TT_MidBlue,
            weight=3,
            opacity=0.8
        ).add_to(m)
    
    # If we have markers, adjust the map view to show them
    if markers:
        if len(markers) == 1:
            # Center on the single marker
            m.location = list(markers[0])
            m.zoom_start = 10
        else:
            # Fit bounds to show both markers and the circle
            # Calculate bounds that include the circle
            center_lat, center_lon = markers[0]
            distance_km = geodesic(markers[0], markers[1]).kilometers
            
            # Approximate bounds (rough conversion from km to degrees)
            lat_offset = distance_km / 111.0  # Roughly 111 km per degree latitude
            lon_offset = distance_km / (111.0 * abs(center_lat / 90.0))  # Adjust for longitude
            
            bounds = [
                [center_lat - lat_offset, center_lon - lon_offset],
                [center_lat + lat_offset, center_lon + lon_offset]
            ]
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

def interactive_map_ui():
    # === MAP MODE ===
    if st.session_state.get("show_educational", False):
        st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
        with st.expander("How Do I Use The Map?", expanded=False):
            st.markdown(f'<div class="educational-content">{text_content.map_help}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    map_col, info_col = st.columns([3, 1])

    with map_col:
        map_data = render_map_with_markers(st.session_state.markers)

    with info_col:
        if st.button("Clear Markers", type="secondary"):
            st.session_state.markers = []
            st.session_state.inputs["altitude_factor"] = 20.0
            st.session_state.inputs["d_sea"] = 60.0
            st.rerun()

        calculate_btn = st.button(
            "Calculate Data", 
            type="primary",
            disabled=len(st.session_state.markers) == 0
        )

        if st.session_state.markers:
            st.write("**Current Markers:**")
            for idx, (lat, lon) in enumerate(st.session_state.markers, start=1):
                marker_name = "Project Location" if idx == 1 else "Closest Sea Location"
                st.write(f"**{marker_name}:** {lat:.5f}°, {lon:.5f}°")

        altitude_val = st.session_state.inputs.get("altitude_factor", 20.0)
        d_sea_val = st.session_state.inputs.get("d_sea", 60.0)
        st.write("**Current Values:**")
        st.write(f"Altitude: {altitude_val:.1f} m")
        st.write(f"Distance to sea: {d_sea_val:.1f} km")

    # Handle map clicks
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        if len(st.session_state.markers) < 2:
            st.session_state.markers.append((lat, lon))
        else:
            st.session_state.markers = [(lat, lon)]
        if len(st.session_state.markers) == 1:
            st.session_state.inputs["altitude_factor"] = 20.0
            st.session_state.inputs["d_sea"] = 60.0
        st.rerun()

    # Calculate results
    if calculate_btn and st.session_state.markers:
        with st.spinner("Calculating geospatial data..."):
            try:
                elevations = []
                for lat, lon in st.session_state.markers:
                    altitude_factor = get_elevation(lat, lon)
                    elevations.append(altitude_factor)

                if len(elevations) >= 1:
                    st.session_state.inputs["altitude_factor"] = float(elevations[0])

                if len(st.session_state.markers) == 2:
                    d_sea = compute_distance(st.session_state.markers[0], st.session_state.markers[1])
                    st.session_state.inputs["d_sea"] = float(d_sea)

                st.rerun()
            except Exception as e:
                st.error(f"Error calculating data: {str(e)}")


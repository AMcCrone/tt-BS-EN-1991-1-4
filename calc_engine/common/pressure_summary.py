import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.colors as pc
from typing import List, Tuple

def get_direction_factor(rotation_angle, use_direction_factor=False):
    """
    Get the directional factor (c_dir) based on the building rotation angle.
    
    Parameters:
    -----------
    rotation_angle : int
        Building rotation angle in degrees clockwise from north
    use_direction_factor : bool
        Whether to use directional factor or not
        
    Returns:
    --------
    dict
        Dictionary mapping each cardinal direction to its c_dir value
    """
    if not use_direction_factor:
        # If not using directional factor, return 1.0 for all directions
        return {
            "North": 1.0,
            "East": 1.0,
            "South": 1.0,
            "West": 1.0
        }
    
    # UK directional factors by angle (clockwise from north)
    uk_direction_factors = {
        0: 0.78,
        30: 0.73,
        60: 0.73,
        90: 0.74,
        120: 0.73,
        150: 0.80,
        180: 0.85,
        210: 0.93,
        240: 1.00,
        270: 0.99,
        300: 0.91,
        330: 0.82
    }
    
    # Map each cardinal direction to an angle after considering building rotation
    direction_angles = {
        "North": (0 + rotation_angle) % 360,
        "East": (90 + rotation_angle) % 360,
        "South": (180 + rotation_angle) % 360,
        "West": (270 + rotation_angle) % 360
    }
    
    # Get the nearest defined angle for each direction
    direction_factors = {}
    for direction, angle in direction_angles.items():
        # Find the nearest angle in the UK factors table
        nearest_angle = min(uk_direction_factors.keys(), key=lambda x: min(abs(x - angle), abs(x - angle + 360), abs(x - angle - 360)))
        direction_factors[direction] = uk_direction_factors[nearest_angle]
    
    return direction_factors

def calculate_pressure_data(session_state, results_by_direction):
    """
    Calculate pressure data for all zones and directions.

    - Summary rows include only zones that are present on that elevation (using
      the d/e rules used for plotting), and Zone E is included only for the elevations
      where detect_zone_E indicated zone_E present. The cp,e for zone E is always -2.0.
    """
    # Extract dimensions and peak velocity pressure
    h = session_state.inputs.get("z", 10.0)  # Building height
    qp_value = session_state.inputs.get("qp_value", 1000.0)  # Peak velocity pressure in N/m²

    # Plan dimensions (needed to determine which zones appear)
    NS_dimension = session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = session_state.inputs.get("EW_dimension", 40.0)

    # Get directional factors
    use_direction_factor = session_state.inputs.get("use_direction_factor", False)
    rotation_angle = session_state.inputs.get("building_rotation", 0)
    direction_factors = get_direction_factor(rotation_angle, use_direction_factor)

    # Define cp,i values
    cp_i_positive = 0.2
    cp_i_negative = -0.3

    # Initialize data structures
    summary_data = []
    zone_pressures_by_direction = {}
    global_max_pressure = float("-inf")
    global_min_pressure = float("inf")

    def zones_for_elevation(width, height, crosswind_dim):
        # ... same as your existing function ...
        e = min(crosswind_dim, 2 * height)
        zone_names = []
        if e < width:
            if width < 2 * e:
                if width <= 2 * (e / 5):
                    zone_names = ['A']
                else:
                    zone_names = ['A', 'B', 'A']
            else:
                if width - 2 * e <= 0:
                    zone_names = ['A', 'B', 'A']
                else:
                    zone_names = ['A', 'B', 'C', 'B', 'A']
        elif e >= width and e < 5 * width:
            if width <= 2 * (e / 5):
                zone_names = ['A']
            else:
                zone_names = ['A', 'B', 'A']
        else:
            zone_names = ['A']
        return zone_names

    # Process each direction (elevation)
    for direction, cp_df in results_by_direction.items():
        c_dir = direction_factors.get(direction, 1.0)
        adjusted_qp = qp_value * c_dir

        # Choose width and crosswind dimension depending on direction
        if direction in ["North", "South"]:
            width = NS_dimension
            crosswind_dim = EW_dimension
        else:  # East or West
            width = EW_dimension
            crosswind_dim = NS_dimension

        zone_pressures_by_direction[direction] = {}

        # 1) First pass: compute/store pressures for any A-D rows present in cp_df
        for _, row in cp_df.iterrows():
            zone = row.get('Zone')
            if zone not in ['A', 'B', 'C', 'D']:
                continue  # skip unknown zones here
            cp_e = round(row.get('cp,e', 0.0), 2)
            we = adjusted_qp * cp_e
            cp_i_used = cp_i_positive if cp_e < 0 else cp_i_negative
            wi = adjusted_qp * cp_i_used
            net_pressure = we - wi

            if net_pressure > global_max_pressure:
                global_max_pressure = net_pressure
            if net_pressure < global_min_pressure:
                global_min_pressure = net_pressure

            zone_pressures_by_direction[direction][zone] = {
                'net_pressure': net_pressure,
                'net_pressure_kpa': round(net_pressure / 1000, 2),
                'cp_e': cp_e,
                'cp_i_used': round(cp_i_used, 2),
                'We_kPa': round(we / 1000, 2),
                'Wi_kPa': round(wi / 1000, 2)
            }

        # ----- Include Zone E if detect reports it for this elevation -----
        detect_res = session_state.get("inset_results", None)
        zone_e_present = False
        if isinstance(detect_res, dict) and detect_res.get(direction):
            dr = detect_res[direction]
            zone_e_present = bool(dr.get("zone_E", False) or
                                  dr.get("east_zone_E", False) or dr.get("west_zone_E", False) or
                                  dr.get("north_zone_E", False) or dr.get("south_zone_E", False))
        if zone_e_present and 'E' not in zone_pressures_by_direction[direction]:
            cp_e = -2.0
            we = adjusted_qp * cp_e
            cp_i_used = cp_i_positive if cp_e < 0 else cp_i_negative
            wi = adjusted_qp * cp_i_used
            net_pressure = we - wi

            if net_pressure > global_max_pressure:
                global_max_pressure = net_pressure
            if net_pressure < global_min_pressure:
                global_min_pressure = net_pressure

            zone_pressures_by_direction[direction]['E'] = {
                'net_pressure': net_pressure,
                'net_pressure_kpa': round(net_pressure / 1000, 2),
                'cp_e': cp_e,
                'cp_i_used': round(cp_i_used, 2),
                'We_kPa': round(we / 1000, 2),
                'Wi_kPa': round(wi / 1000, 2)
            }

        # 2) Determine which zones are present on this elevation (may contain repeats)
        present_zone_sequence = zones_for_elevation(width, h, crosswind_dim)

        # 3) Convert sequence to an ordered unique list (preserve first occurrence order)
        unique_present_zones = []
        for zn in present_zone_sequence:
            if zn not in unique_present_zones:
                unique_present_zones.append(zn)

        # Ensure Zone D is included if computed
        if 'D' in zone_pressures_by_direction[direction] and 'D' not in unique_present_zones:
            unique_present_zones.append('D')

        # Append E only if computed/present for this elevation
        if 'E' in zone_pressures_by_direction[direction] and 'E' not in unique_present_zones:
            unique_present_zones.append('E')

        # 4) Build summary rows only for zones in unique_present_zones and only if
        #    that zone was actually computed in the first pass (or added above)
        for zone in unique_present_zones:
            zdata = zone_pressures_by_direction[direction].get(zone)
            if not zdata:
                continue

            we_kpa = zdata.get('We_kPa', 0.0)
            wi_kpa = zdata.get('Wi_kPa', 0.0)
            net_kpa = zdata.get('net_pressure_kpa', 0.0)
            cp_e = zdata.get('cp_e', 0.0)
            cp_i_used = zdata.get('cp_i_used', 0.0)
            action_type = "Pressure" if net_kpa > 0 else "Suction"

            summary_data.append({
                "Direction": direction,
                "Zone": zone,
                "c_dir": round(c_dir, 2),
                "cp,e": cp_e,
                "cp,i (used)": cp_i_used,
                "We (kPa)": we_kpa,
                "Wi (kPa)": wi_kpa,
                "Net (kPa)": net_kpa,
                "Action": action_type
            })

    # Fallbacks and range handling (unchanged)
    if global_max_pressure == float("-inf") and global_min_pressure == float("inf"):
        global_max_pressure = 0.0
        global_min_pressure = 0.0
    if global_max_pressure == global_min_pressure:
        global_max_pressure = global_min_pressure + 1.0

    global_pressure_range = (global_min_pressure / 1000, global_max_pressure / 1000)
    return summary_data, global_pressure_range, zone_pressures_by_direction


def create_pressure_summary(session_state, results_by_direction):
    """
    Create a summary DataFrame with pressure/suction values for each elevation.
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions and qp value
    results_by_direction : dict
        Dictionary of DataFrames with cp,e values for each direction
    
    Returns:
    --------
    pd.DataFrame
        Summary of pressure/suction values for all elevations
    """
    # Calculate pressure data for all zones
    summary_data, _, _ = calculate_pressure_data(session_state, results_by_direction)
    
    # Create DataFrame
    summary_df = pd.DataFrame(summary_data)
    
    return summary_df

def plot_elevation_with_pressures(session_state, results_by_direction):
    """
    Create plots for all four elevations showing wind zones A, B, C with constant pressure
    values based on the building's height. Each zone annotation shows:
      - the zone suction/pressure (e.g. "-1.36 kPa")
      - on the next line, the wind pressure taken from Zone D for the same elevation,
        displayed with a leading '+' for non-negative values (and '-' for negative).
    "Zone D" is never mentioned in the text — only the numeric value is shown.
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions
    results_by_direction : dict
        Dictionary of DataFrames with cp,e values for each direction
    
    Returns:
    --------
    dict
        Dictionary of plotly figures for each elevation
    """
    # Extract dimensions
    h = session_state.inputs.get("z", 10.0)  # Building height
    NS_dimension = session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = session_state.inputs.get("EW_dimension", 40.0)
    
    # Get directional factors
    use_direction_factor = session_state.inputs.get("use_direction_factor", False)
    rotation_angle = session_state.inputs.get("building_rotation", 0)
    direction_factors = get_direction_factor(rotation_angle, use_direction_factor)
    
    # Create a continuous color scale for pressure
    colorscale = pc.sequential.Teal_r
    
    # Get pre-calculated pressure data
    _, global_pressure_range, zone_pressures_by_direction = calculate_pressure_data(
        session_state, results_by_direction
    )
    
    # Unpack global pressure range (they are already in kPa)
    global_min_suction_kpa, global_max_suction_kpa = global_pressure_range
    
    # Storage for all figures
    figures = {}
    
    # Process each direction (elevation)
    for direction, cp_df in results_by_direction.items():
        # Get directional factor for this direction
        c_dir = direction_factors.get(direction, 1.0)
        
        # Set up width and height based on direction
        if direction in ["North", "South"]:
            width = NS_dimension
            height = h
            crosswind_dim = EW_dimension
            title = f"{direction} Elevation - Wind Suction Zones (c_dir: {c_dir:.2f})"
        else:  # East or West
            width = EW_dimension
            height = h
            crosswind_dim = NS_dimension
            title = f"{direction} Elevation - Wind Suction Zones (c_dir: {c_dir:.2f})"
        
        # Calculate parameter e according to Eurocode
        e = min(crosswind_dim, 2 * height)
        
        # Create figure
        fig = go.Figure()
        
        # Initialize zone boundaries and names
        zone_boundaries = []
        zone_names = []
        
        # Determine zones based on relation between e and d (width)
        if e < width:  # Three zones: A, B, C (or variants)
            # Check if zones would overlap
            if width < 2*e:  # Zones would overlap in the middle
                # If e/5 from both ends would overlap (very narrow building)
                if width <= 2*(e/5):
                    # Single zone A for the whole width
                    zone_boundaries = [(0, width)]
                    zone_names = ['A']
                else:
                    # A-B-A pattern (simplified from A-B-B-A)
                    b_width = width - 2*(e/5)
                    zone_boundaries = [
                        (0, e/5),                  # Left A
                        (e/5, width - e/5),        # Middle B
                        (width - e/5, width)       # Right A
                    ]
                    zone_names = ['A', 'B', 'A']
            else:
                if width - 2*e <= 0:  # If C zone would have zero or negative width
                    # Use A-B-A pattern instead
                    zone_boundaries = [
                        (0, e/5),                  # Left A
                        (e/5, width - e/5),        # Middle B
                        (width - e/5, width)       # Right A
                    ]
                    zone_names = ['A', 'B', 'A']
                else:
                    # Standard case with A, B, C, B, A
                    zone_boundaries = [
                        (0, e/5),                      # Left A
                        (e/5, e),                      # Left B
                        (e, width - e),                # Middle C
                        (width - e, width - e/5),      # Right B
                        (width - e/5, width)           # Right A
                    ]
                    zone_names = ['A', 'B', 'C', 'B', 'A']
        
        elif e >= width and e < 5*width:  # Two zones: A, B (or A only)
            # For e >= d but < 5d, we have A zones on each end, B in middle
            zone_a_width = e/5
            if width <= 2*(e/5):
                zone_boundaries = [(0, width)]
                zone_names = ['A']
            else:
                zone_boundaries = [
                    (0, e/5),              # Left A
                    (e/5, width-e/5),      # Middle B
                    (width-e/5, width)     # Right A
                ]
                zone_names = ['A', 'B', 'A']
        else:  # e >= 5*width, One zone: A
            zone_boundaries = [(0, width)]
            zone_names = ['A']
        
        # Get the pre-calculated zone pressures for this direction (kPa values)
        direction_zone_pressures = zone_pressures_by_direction.get(direction, {})
        
        # Get the Zone D pressure for this direction (kPa) if available
        # We will show this numeric value below each zone's value in the annotation.
        zone_d_pressure_kpa = None
        if isinstance(direction_zone_pressures, dict):
            # Use .get safely; net_pressure_kpa is expected to be a float
            zone_d_pressure_kpa = direction_zone_pressures.get('D', {}).get('net_pressure_kpa', None)
            # If it's present but not a number, coerce to None
            if zone_d_pressure_kpa is not None:
                try:
                    zone_d_pressure_kpa = float(zone_d_pressure_kpa)
                except Exception:
                    zone_d_pressure_kpa = None
        
        # For each zone, create a single colored rectangle with constant pressure
        for i, ((x0, x1), zone_name) in enumerate(zip(zone_boundaries, zone_names)):
            # Get the pressure value for this zone from pre-calculated data (kPa)
            zone_data = direction_zone_pressures.get(zone_name, {'net_pressure_kpa': 0})
            zone_pressure = zone_data.get('net_pressure_kpa', 0.0)
            try:
                zone_pressure = float(zone_pressure)
            except Exception:
                zone_pressure = 0.0
            
            # Normalize the pressure value for color mapping (kPa domain)
            if global_max_suction_kpa == global_min_suction_kpa:
                normalized_value = 0.5  # Default to middle of colorscale if no range
            else:
                normalized_value = (zone_pressure - global_min_suction_kpa) / (global_max_suction_kpa - global_min_suction_kpa)
            normalized_value = max(0.0, min(1.0, normalized_value))  # Clamp between 0 and 1
            
            # Sample color from colorscale
            sample_list = [normalized_value]
            sampled = pc.sample_colorscale(colorscale, sample_list)
            if sampled:
                zone_color = sampled[0]
            else:
                if isinstance(colorscale, (list, tuple)) and len(colorscale):
                    zone_color = colorscale[-1][1]
                else:
                    zone_color = "rgb(200,200,200)"
            
            # Add colored rectangle for the zone
            fig.add_shape(
                type="rect",
                x0=x0,
                y0=0,
                x1=x1,
                y1=height,
                fillcolor=zone_color,
                opacity=1.0,
                line=dict(width=0),
                layer="below"
            )
            
            # Add colorbar to figure (only once)
            if i == 0:
                dummy_z = [[global_min_suction_kpa, global_min_suction_kpa], 
                           [global_max_suction_kpa, global_max_suction_kpa]]
                fig.add_trace(go.Heatmap(
                    z=dummy_z,
                    x=[0, 0.1],  # Outside visible area
                    y=[0, 0.1],  # Outside visible area
                    colorscale=colorscale,
                    showscale=True,
                    colorbar=dict(
                        title="Pressure (kPa)",
                        x=1.05,
                        y=0.5,
                        lenmode="fraction",
                        len=0.9
                    ),
                    visible=False
                ))
            
            # Build label text with zone value (suction/pressure) and Zone D pressure line
            # Format: "Zone A\n-1.36 kPa\n+1.08 kPa" (using <br> for plotly)
            # For Zone D pressure: prefix '+' when non-negative, otherwise show negative sign.
            label_lines = []
            # First line: Zone name
            label_lines.append(f"Zone {zone_name}")
            # Second line: the zone's numeric value (will show negative sign if negative)
            label_lines.append(f"{zone_pressure:.2f} kPa")
            # Third line: the Zone D pressure numeric value if available
            if zone_d_pressure_kpa is not None:
                # Use explicit '+' for non-negative values, keep '-' for negative values
                if zone_d_pressure_kpa >= 0:
                    d_text = f"+{zone_d_pressure_kpa:.2f} kPa"
                else:
                    d_text = f"{zone_d_pressure_kpa:.2f} kPa"
                label_lines.append(d_text)
            
            # Join lines with HTML line breaks for plotly annotation
            label_text = "<br>".join(label_lines)
            
            # Add annotation for the zone
            fig.add_annotation(
                x=(x0 + x1)/2,
                y=height/2,
                text=label_text,
                showarrow=False,
                font=dict(size=16, color="white"),
                bgcolor="rgba(0,0,0,0.3)",
                bordercolor="white",
                borderwidth=1,
                borderpad=4,
                opacity=0.8
            )
        
        # Add building outline
        fig.add_shape(
            type="rect",
            x0=0,
            y0=0,
            x1=width,
            y1=height,
            line=dict(width=2, color="black"),
            fillcolor="rgba(0,0,0,0)",
            opacity=1,
            layer="above"
        )
        
        # Add zone boundary lines
        # note: boundaries[0] is leftmost start; we want subsequent boundaries as vertical splits
        for x_boundary in [boundary[0] for boundary in zone_boundaries[1:]]:
            fig.add_shape(
                type="line",
                x0=x_boundary,
                y0=0,
                x1=x_boundary,
                y1=height,
                line=dict(width=1.5, color="black", dash="solid"),
                layer="above"
            )
        
        # Add ground line
        fig.add_shape(
            type="line",
            x0=-0.1*width,
            y0=0,
            x1=1.1*width,
            y1=0,
            line=dict(width=3, color="black"),
            layer="above"
        )
        
        # Add reference height line and annotation
        fig.add_shape(
            type="line",
            x0=-0.05*width, y0=height, 
            x1=0, y1=height,
            line=dict(color="black", width=1)
        )
        fig.add_annotation(
            x=-0.02*width, y=height,
            text=f"h = {height:.1f}m",
            showarrow=False,
            font=dict(size=12),
            xanchor="right",
            yanchor="middle"
        )
        
        # Add e and d dimensions as annotations
        fig.add_annotation(
            x=width/2,
            y=-0.05*height,
            text=f"d = {width:.2f}m",
            showarrow=False,
            font=dict(size=12)
        )
        
        # Add annotation for e value
        fig.add_annotation(
            x=width/2,
            y=1.05*height,
            text=f"e = {e:.2f}m ({'<' if e < width else '≥'} d)",
            showarrow=False,
            font=dict(size=12, color="black")
        )
        
        # Add title and layout tweaks
        fig.update_layout(
            title=f"{title}",
            showlegend=False,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-0.1*width, 1.1*width]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-0.1*height, 1.1*height],
                scaleanchor="x",
                scaleratio=1
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor="white",
            height=600
        )
        
        # Store the figure
        figures[direction] = fig
    
    return figures


def create_3d_wind_visualization(session_state, results_by_direction, mode="suction"):
    """
    Create an interactive 3D visualization of the building with wind zones and pressure values.
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions and wind parameters
    results_by_direction : dict
        Dictionary of DataFrames with cp,e values for each direction
    mode : str
        "suction" for zones A,B,C visualization or "pressure" for zone D visualization
    
    Returns:
    --------
    plotly.graph_objects.Figure
        3D visualization of the building with wind zones and pressure values
    """
    import plotly.graph_objects as go
    import numpy as np
    import plotly.colors as colors
    
    # Extract building dimensions
    NS_dimension = session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = session_state.inputs.get("EW_dimension", 40.0)
    h = session_state.inputs.get("z", 10.0)  # Building height
    qp_value = session_state.inputs.get("qp_value", 1000.0)  # Peak velocity pressure in N/m²
    
    # Calculate aspect ratio to maintain proportions
    max_dim = max(NS_dimension, EW_dimension, h)
    scale_factor = 1.0
    
    # Scale factors to maintain visual proportions
    scaled_NS = NS_dimension / max_dim * scale_factor
    scaled_EW = EW_dimension / max_dim * scale_factor
    scaled_h = h / max_dim * scale_factor
    
    # Get directional factors
    use_direction_factor = session_state.inputs.get("use_direction_factor", False)
    rotation_angle = session_state.inputs.get("building_rotation", 0)
    direction_factors = get_direction_factor(rotation_angle, use_direction_factor)
    
    # Create a figure
    fig = go.Figure()
    
    # Use the built-in Teal colorscale from plotly
    blues_colorscale = "Teal"
    
    # Add a ground plane
    ground_extension = max(NS_dimension, EW_dimension) * 0.5
    fig.add_trace(go.Mesh3d(
        x=[-ground_extension, NS_dimension + ground_extension, NS_dimension + ground_extension, -ground_extension],
        y=[-ground_extension, -ground_extension, EW_dimension + ground_extension, EW_dimension + ground_extension],
        z=[0, 0, 0, 0],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color='rgb(240,240,240)',  # Light grey ground
        opacity=0.7,
        showlegend=False,
        hoverinfo='none'
    ))
    
    # Get pressure summary data
    pressure_summary = create_pressure_summary(session_state, results_by_direction)
    
    # Get all pressure data to determine global scale
    all_pressure_data = pressure_summary.copy()
    
    # Find the maximum absolute pressure value across all zones
    if len(all_pressure_data) > 0:
        max_abs_pressure = max(abs(all_pressure_data['Net (kPa)'].min()), 
                              abs(all_pressure_data['Net (kPa)'].max()))
        
        # Set global min to 0 and max to the absolute maximum 
        global_min_pressure = 0.0
        global_max_pressure = max_abs_pressure
        
        # Ensure we have a range to avoid division by zero
        if global_max_pressure == 0:
            global_max_pressure = 1.0
    else:
        global_min_pressure = 0.0
        global_max_pressure = 1.0
    
    # Filter based on mode
    if mode == "suction":
        # Only include zones A, B, C (suction zones)
        pressure_data = pressure_summary[pressure_summary['Zone'].isin(['A', 'B', 'C'])]
        colorbar_title = "Suction (kPa)"
    else:  # pressure
        # Only include zone D (pressure zone)
        pressure_data = pressure_summary[pressure_summary['Zone'] == 'D']
        colorbar_title = "Pressure (kPa)"
    
    # Get the elevation plots to access zone boundaries and names
    elevation_plots = plot_elevation_with_pressures(session_state, results_by_direction)
    
    # Create a colorbar using a separate trace
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(
            colorscale=blues_colorscale,
            showscale=True,
            cmin=0,
            cmax=global_max_pressure,
            colorbar=dict(
                title=colorbar_title,
                thickness=20,
                outlinewidth=1,
                outlinecolor='black',
                x=1.05
            )
        ),
        showlegend=False
    ))
    
    # Dictionary to map direction to face coordinates with scaled dimensions
    direction_to_face = {
        "North": {
            "x": [0, NS_dimension, NS_dimension, 0],
            "y": [0, 0, 0, 0],
            "z": [0, 0, h, h]
        },
        "South": {
            "x": [0, NS_dimension, NS_dimension, 0],
            "y": [EW_dimension, EW_dimension, EW_dimension, EW_dimension],
            "z": [0, 0, h, h]
        },
        "East": {
            "x": [0, 0, 0, 0],
            "y": [0, EW_dimension, EW_dimension, 0],
            "z": [0, 0, h, h]
        },
        "West": {
            "x": [NS_dimension, NS_dimension, NS_dimension, NS_dimension],
            "y": [0, EW_dimension, EW_dimension, 0],
            "z": [0, 0, h, h]
        }
    }
    
    # Add direction labels (N, E, S, W) on the ground with increased offset
    offset_factor = max(NS_dimension, EW_dimension) * 0.35  # push labels further out
    center_x = NS_dimension / 2
    center_y = EW_dimension / 2
    
    direction_labels = {
        "North": {"pos": [center_x, -offset_factor, 0], "text": "N"},
        "South": {"pos": [center_x, EW_dimension + offset_factor, 0], "text": "S"},
        "East":  {"pos": [-offset_factor, center_y, 0], "text": "E"},
        "West":  {"pos": [NS_dimension + offset_factor, center_y, 0], "text": "W"}
    }

    # Add direction labels
    for direction, label_info in direction_labels.items():
        fig.add_trace(go.Scatter3d(
            x=[label_info["pos"][0]],
            y=[label_info["pos"][1]],
            z=[label_info["pos"][2]],
            text=[label_info["text"]],
            mode='text',
            textfont=dict(size=24, color='black'),
            showlegend=False
        ))
    
    # Helper function to add a face with specified zone data
    def add_zone_face(x, y, z, zone_name, net_pressure):
        # Get absolute pressure value for color mapping (since 0 is white)
        abs_pressure = abs(net_pressure)
        
        # Normalize pressure for color mapping
        normalized_value = abs_pressure / global_max_pressure
        normalized_value = max(0, min(1, normalized_value))  # Clamp between 0 and 1
        
        # Get color from the Teal colorscale
        zone_color = colors.sample_colorscale(blues_colorscale, [normalized_value])[0]
        
        # Add zone face with appropriate color (single mesh with 2 triangles)
        fig.add_trace(go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color=zone_color,
            opacity=1.0,
            showlegend=False,
            hovertext=f"Zone {zone_name}<br>Net Pressure: {net_pressure:.2f} kPa",
            hoverinfo='text'
        ))
        
        # Add black border around zone (using line segments)
        fig.add_trace(go.Scatter3d(
            x=[x[0], x[1], x[2], x[3], x[0]],  # Connect back to first point to close the loop
            y=[y[0], y[1], y[2], y[3], y[0]],
            z=[z[0], z[1], z[2], z[3], z[0]],
            mode='lines',
            line=dict(color='black', width=2),
            showlegend=False,
            hoverinfo='none'
        ))
    
    # Process each direction (North, South, East, West)
    for direction in ["North", "South", "East", "West"]:
        # Skip if we don't have data for this direction
        if direction not in elevation_plots:
            continue
        
        # Get direction-specific pressure data
        direction_data = pressure_data[pressure_data['Direction'] == direction]
        
        # Skip if no data for this direction based on mode
        if len(direction_data) == 0:
            continue
        
        # Get directional factor
        c_dir = direction_factors.get(direction, 1.0)
        
        # Extract base coordinates for this face
        face_coords = direction_to_face[direction]
        
        # Set up width based on direction
        if direction in ["North", "South"]:
            width = NS_dimension
        else:  # East or West
            width = EW_dimension
        
        # Calculate parameter e according to Eurocode
        if direction in ["North", "South"]:
            crosswind_dim = EW_dimension
        else:  # East or West
            crosswind_dim = NS_dimension
        
        e = min(crosswind_dim, 2 * h)
        
        # Determine zone boundaries based on relation between e and width
        zone_boundaries = []
        zone_names = []
        
        if e < width:  # Three zones: A, B, C
            # Check if zones would overlap
            if width < 2*e:  # Zones would overlap in the middle
                # If e/5 from both ends would overlap (very narrow building)
                if width <= 2*(e/5):
                    # Single zone A for the whole width
                    zone_boundaries = [(0, width)]
                    zone_names = ['A']
                else:
                    # A-B-A pattern (simplified from A-B-B-A)
                    # Calculate width for zone B
                    b_width = width - 2*(e/5)
                    
                    zone_boundaries = [
                        (0, e/5),                  # Left A
                        (e/5, width - e/5),        # Middle B
                        (width - e/5, width)       # Right A
                    ]
                    zone_names = ['A', 'B', 'A']
            else:
                if width - 2*e <= 0:  # If C zone would have zero or negative width
                    # Use A-B-A pattern instead
                    zone_boundaries = [
                        (0, e/5),                  # Left A
                        (e/5, width - e/5),        # Middle B
                        (width - e/5, width)       # Right A
                    ]
                    zone_names = ['A', 'B', 'A']
                else:
                    # Standard case with A, B, C, B, A
                    zone_boundaries = [
                        (0, e/5),                      # Left A
                        (e/5, e),                      # Left B
                        (e, width - e),                # Middle C
                        (width - e, width - e/5),      # Right B
                        (width - e/5, width)           # Right A
                    ]
                    zone_names = ['A', 'B', 'C', 'B', 'A']
        
        elif e >= width and e < 5*width:  # Two zones: A, B
            # For e >= d but < 5d, we have A zones on each end, B in middle
            zone_a_width = e/5
            
            # If building is narrow compared to e, A zones might overlap
            if width <= 2*(e/5):
                # Only zone A across entire width
                zone_boundaries = [(0, width)]
                zone_names = ['A']
            else:
                # Normal case with A-B-A
                zone_boundaries = [
                    (0, e/5),              # Left A
                    (e/5, width-e/5),      # Middle B
                    (width-e/5, width)     # Right A
                ]
                zone_names = ['A', 'B', 'A']
            
        else:  # e >= 5*width, One zone: A
            zone_boundaries = [(0, width)]
            zone_names = ['A']
        
        if mode == "suction":
            # Process each zone
            for (x_start, x_end), zone_name in zip(zone_boundaries, zone_names):
                # Skip if we don't have pressure data for this zone
                zone_data = direction_data[direction_data['Zone'] == zone_name]
                if len(zone_data) == 0:
                    continue
                
                # Get the pressure value
                net_pressure = zone_data['Net (kPa)'].values[0]
                
                # Calculate the vertices for this zone
                if direction == "North":
                    x = [x_start, x_end, x_end, x_start]
                    y = [0, 0, 0, 0]
                    z = [0, 0, h, h]
                elif direction == "South":
                    x = [width - x_end, width - x_start, width - x_start, width - x_end]
                    y = [EW_dimension, EW_dimension, EW_dimension, EW_dimension]
                    z = [0, 0, h, h]
                elif direction == "East":
                    x = [0, 0, 0, 0]
                    y = [width - x_end, width - x_start, width - x_start, width - x_end]
                    z = [0, 0, h, h]
                elif direction == "West":
                    x = [NS_dimension, NS_dimension, NS_dimension, NS_dimension]
                    y = [x_start, x_end, x_end, x_start]
                    z = [0, 0, h, h]
                
                # Add zone face with border
                add_zone_face(x, y, z, zone_name, net_pressure)
                
        else:  # pressure mode
            # For pressure mode (zone D), use the whole face
            zone_data = direction_data[direction_data['Zone'] == 'D']
            if len(zone_data) > 0:
                # Get the pressure value
                net_pressure = zone_data['Net (kPa)'].values[0]
                
                # Use the whole face for zone D
                x = face_coords["x"]
                y = face_coords["y"]
                z = face_coords["z"]
                
                # Add zone face with border
                add_zone_face(x, y, z, 'D', net_pressure)
    
    # Add the roof (top face) as a solid light grey color
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, EW_dimension, EW_dimension],
        z=[h, h, h, h],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color='rgb(220,220,220)',  # Light grey
        opacity=1.0,
        showlegend=False,
        hovertext="Roof",
        hoverinfo='text'
    ))
    
    # Set camera position to get a good isometric view
    camera = dict(
        eye=dict(x=1.5, y=1.5, z=1.0)
    )
    
    # Apply hover mode and camera settings
    fig.update_layout(
        scene_camera=camera,
        hovermode='closest',
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        # Turn off all axes
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False),
            zaxis=dict(visible=False, showgrid=False, zeroline=False),
            aspectmode='data',  # Use the actual data dimensions
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig

def create_wind_visualization_ui(session_state, results_by_direction):
    """
    Create an interactive UI for toggling between pressure and suction visualization modes
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions
    results_by_direction : dict
        Dictionary of DataFrames with cp,e values for each direction
    
    Returns:
    --------
    None (renders UI components directly)
    """
    import streamlit as st
    
    # Create toggle for pressure/suction mode
    mode = st.radio(
        "Visualization Mode:",
        ["Suction", "Pressure"],
        horizontal=True
    )
    
    # Set the mode based on selection
    if "Suction" in mode:
        viz_mode = "suction"
    else:
        viz_mode = "pressure"
    
    # Create 3D visualization
    fig = create_3d_wind_visualization(session_state, results_by_direction, mode=viz_mode)
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def generate_pressure_summary_paragraphs(session_state, results_by_direction) -> List[str]:
    """
    Generate human-readable summary paragraphs from the pressure results.
    Returns a list of paragraphs (strings).
    """
    summary_data, _, zone_pressures_by_direction = calculate_pressure_data(session_state, results_by_direction)
    summary_df = pd.DataFrame(summary_data)

    paragraphs: List[str] = []

    # Empty-data fallback
    if summary_df.empty:
        paragraphs.append("No pressure/suction results are available to summarise.")
        # still include stateful flags
        consider_funnelling = (session_state.inputs.get("consider_funnelling")
                               if hasattr(session_state, "inputs") else session_state.get("consider_funnelling", False))
        paragraphs.append("Funnelling has been considered." if consider_funnelling else "Funnelling has not been considered.")
        inset_enabled = (bool(session_state.inputs.get("inset_enabled", False))
                         if hasattr(session_state, "inputs") else bool(session_state.get("inset_enabled", False)))
        paragraphs.append("Inset zone has been considered." if inset_enabled else "Inset zone has not been considered.")
        paragraphs.append("No design value can be recommended because no results are present.")
        return paragraphs

    all_elevations = set(summary_df["Direction"].unique())

    # -------- Maximum positive wind pressure (pressure is always zone D) --------
    pos_df = summary_df[summary_df["Net (kPa)"] > 0]
    if not pos_df.empty:
        max_pos_val = pos_df["Net (kPa)"].max()
        max_pos_rows = pos_df[pos_df["Net (kPa)"] == max_pos_val]
        pos_dirs = set(max_pos_rows["Direction"].unique())
        if pos_dirs == all_elevations:
            elevation_text = "all elevations"
        else:
            elevation_text = ", ".join(sorted(pos_dirs))
        # Pressure is always zone D (per your rule) so don't report zone
        paragraphs.append(f"Maximum wind pressure: {max_pos_val:.2f} kPa — present on {elevation_text}.")
    else:
        paragraphs.append("No positive wind pressure (net > 0) was found in the results.")

    # -------- Maximum wind suction (most negative) --------
    neg_df = summary_df[summary_df["Net (kPa)"] < 0]
    if not neg_df.empty:
        min_neg_val = neg_df["Net (kPa)"].min()  # most negative
        min_neg_rows = neg_df[neg_df["Net (kPa)"] == min_neg_val]
        neg_dirs = set(min_neg_rows["Direction"].unique())
        neg_zones = sorted(set(min_neg_rows["Zone"].unique()))
        if neg_dirs == all_elevations:
            elevation_text_neg = "all elevations"
        else:
            elevation_text_neg = ", ".join(sorted(neg_dirs))

        # Describe zones: if single zone mention it, otherwise list
        zones_text = neg_zones[0] if len(neg_zones) == 1 else ", ".join(neg_zones)
        paragraphs.append(f"Maximum wind suction: {min_neg_val:.2f} kPa — {zones_text} on {elevation_text_neg}.")
    else:
        paragraphs.append("No wind suction (net negative pressures) was found in the results.")

    # -------- Funnelling (friendly phrasing) --------
    consider_funnelling = (session_state.inputs.get("consider_funnelling")
                           if hasattr(session_state, "inputs") else session_state.get("consider_funnelling", False))
    if bool(consider_funnelling):
        paragraphs.append("Funnelling has been considered.")
    else:
        paragraphs.append("Funnelling has not been considered.")

    # -------- Inset zone and Zone E presence --------
    inset_enabled = (bool(session_state.inputs.get("inset_enabled", False))
                     if hasattr(session_state, "inputs") else bool(session_state.get("inset_enabled", False)))

    # Collect Zone E entries (direction + value)
    zone_e_entries = []
    for direction, zd in zone_pressures_by_direction.items():
        e = zd.get("E")
        if e is not None:
            zone_e_entries.append({
                "Direction": direction,
                "Net (kPa)": e.get("net_pressure_kpa"),
                "cp,e": e.get("cp_e")
            })

    if zone_e_entries:
        entries_txt = "; ".join([f"{ent['Direction']} = {ent['Net (kPa)']:.2f} kPa (cp,e={ent['cp,e']})"
                                 for ent in zone_e_entries])
        if inset_enabled:
            inset_phrase = "Inset zone has been considered."
        else:
            inset_phrase = "Inset zone has not been considered."
        paragraphs.append(f"{inset_phrase} Zone E is present on the following elevation(s): {entries_txt}.")
    else:
        if inset_enabled:
            paragraphs.append("Inset zone has been considered. Zone E was not present on any elevation.")
        else:
            paragraphs.append("Inset zone has not been considered. Zone E was not present on any elevation.")

    # -------- Final design recommendation --------
    # design value = maximum absolute net pressure across all rows (kPa)
    summary_df["abs_Net"] = summary_df["Net (kPa)"].abs()
    max_abs_val = summary_df["abs_Net"].max()
    max_abs_rows = summary_df[summary_df["abs_Net"] == max_abs_val]

    # Determine whether driver is pressure or suction (use Net (kPa) sign)
    # If there are multiple driver rows, try to present concisely
    unique_dirs = set(max_abs_rows["Direction"].unique())
    unique_zones = set(max_abs_rows["Zone"].unique())
    # determine phrase for elevations
    if unique_dirs == all_elevations:
        elev_phrase = "all elevations"
    else:
        elev_phrase = ", ".join(sorted(unique_dirs))
    # determine zone phrase
    if len(unique_zones) == 1:
        zone_phrase = next(iter(unique_zones))
    else:
        zone_phrase = ", ".join(sorted(unique_zones))

    # Determine whether driver is pressure or suction for wording
    # If some rows are positive and some negative (unlikely), report generically as "wind suction/pressure"
    signs = set(max_abs_rows["Net (kPa)"].apply(lambda x: "pressure" if x > 0 else ("suction" if x < 0 else "zero")))
    if len(signs) == 1:
        driver_kind = next(iter(signs))
    else:
        driver_kind = "wind suction/pressure"

    paragraphs.append(
        f'TT recommend a design value of **{max_abs_val:.2f} kPa** to be adopted for the building. '
        f'This is driven by {driver_kind} from Zone {zone_phrase} on {elev_phrase}.'
    )

    return paragraphs

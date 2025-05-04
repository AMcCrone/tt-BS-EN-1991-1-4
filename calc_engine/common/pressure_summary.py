import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.colors as pc

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
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions and qp value
    results_by_direction : dict
        Dictionary of DataFrames with cp,e values for each direction
    
    Returns:
    --------
    tuple
        (summary_data, global_pressure_range, zone_pressures_by_direction)
        - summary_data: List of dictionaries with pressure data for each zone
        - global_pressure_range: Tuple of (min_pressure_kpa, max_pressure_kpa)
        - zone_pressures_by_direction: Dict with pressure values by direction and zone
    """
    # Extract dimensions and peak velocity pressure
    h = session_state.inputs.get("z", 10.0)  # Building height
    qp_value = session_state.inputs.get("qp_value", 1000.0)  # Peak velocity pressure in N/m²
    
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
    global_max_pressure = 0
    global_min_pressure = 0
    
    # Process each direction (elevation)
    for direction, cp_df in results_by_direction.items():
        # Get directional factor for this direction
        c_dir = direction_factors.get(direction, 1.0)
        
        # Apply directional factor to qp
        adjusted_qp = qp_value * c_dir
        
        # Initialize pressure data for this direction
        zone_pressures_by_direction[direction] = {}
        
        # For each zone in this direction
        for _, row in cp_df.iterrows():
            zone = row['Zone']
            
            # Skip Zone E for summary table but still calculate for plotting
            if zone in ['A', 'B', 'C', 'D']:
                cp_e = row['cp,e']
                
                # Round cp,e to 2 decimal places
                cp_e = round(cp_e, 2)
                
                # Calculate external pressure with directional factor
                we = adjusted_qp * cp_e
                
                # Determine which internal pressure coefficient to use based on cp,e
                # If cp,e is negative (suction), use positive cp,i to maximize net pressure
                # If cp,e is positive (pressure), use negative cp,i to maximize net pressure
                if cp_e < 0:
                    cp_i_used = cp_i_positive
                else:
                    cp_i_used = cp_i_negative
                
                # Calculate internal pressure
                wi = adjusted_qp * cp_i_used
                
                # Calculate net pressure as the difference between external and internal pressure
                net_pressure = we - wi
                
                # Update global pressure range (for plotting)
                global_max_pressure = max(global_max_pressure, net_pressure)
                global_min_pressure = min(global_min_pressure, net_pressure)
                
                # Round cp,i to 2 decimal places
                cp_i_used = round(cp_i_used, 2)
                
                # Convert N/m² to kPa and round to 2 decimal places
                we_kpa = round(we / 1000, 2)
                wi_kpa = round(wi / 1000, 2)
                net_kpa = round(net_pressure / 1000, 2)
                
                # Store zone pressure data for plotting
                zone_pressures_by_direction[direction][zone] = {
                    'net_pressure': net_pressure,
                    'net_pressure_kpa': net_kpa,
                    'cp_e': cp_e,
                    'cp_i_used': cp_i_used
                }
                
                # Determine action type based on net pressure
                action_type = "Pressure" if net_pressure > 0 else "Suction"
                
                # For zones A, B, C, D (not E), add to summary data
                if zone != 'E':
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
    
    # Ensure we have some range to avoid division by zero
    if global_max_pressure == global_min_pressure:
        global_max_pressure = global_min_pressure + 1
    
    # Convert global pressure range from N/m² to kPa
    global_pressure_range = (
        global_min_pressure / 1000,  # Min pressure (usually negative/suction)
        global_max_pressure / 1000   # Max pressure (usually positive/pressure)
    )
    
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
    values based on the building's height.
    
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
    
    # Unpack global pressure range
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
        
        # Determine zones based on relation between e and d
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
        
        # Get the pre-calculated zone pressures for this direction
        direction_zone_pressures = zone_pressures_by_direction.get(direction, {})
        
        # For each zone, create a single colored rectangle with constant pressure
        for i, ((x0, x1), zone_name) in enumerate(zip(zone_boundaries, zone_names)):
            # Get the pressure value for this zone from pre-calculated data
            zone_data = direction_zone_pressures.get(zone_name, {'net_pressure_kpa': 0})
            zone_pressure = zone_data.get('net_pressure_kpa', 0)
            
            # Normalize the pressure value for color mapping
            if global_max_suction_kpa == global_min_suction_kpa:
                normalized_value = 0.5  # Default to middle of colorscale if no range
            else:
                normalized_value = (zone_pressure - global_min_suction_kpa) / (global_max_suction_kpa - global_min_suction_kpa)
            normalized_value = max(0, min(1, normalized_value))  # Clamp between 0 and 1
            
            # 1) Make sure we pass a list of sample points
            sample_list = [normalized_value]
            
            # 2) Try to sample
            sampled = pc.sample_colorscale(colorscale, sample_list)
            
            # 3) If successful, grab the first color; otherwise pick a fallback
            if sampled:
                zone_color = sampled[0]
            else:
                # if colorscale is a sequence of [t, color] pairs, pick end stops
                if isinstance(colorscale, (list, tuple)) and len(colorscale):
                    # take the last defined color
                    zone_color = colorscale[-1][1]
                else:
                    # fallback to a hard-coded neutral grey
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
                # Create a dummy heatmap just for the colorbar
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
            
            # Add zone label with pressure value
            fig.add_annotation(
                x=(x0 + x1)/2,
                y=height/2,
                text=f"Zone {zone_name}<br>{zone_pressure:.2f} kPa",
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
        
        # Add title
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
            "x": [NS_dimension, NS_dimension, NS_dimension, NS_dimension],
            "y": [0, EW_dimension, EW_dimension, 0],
            "z": [0, 0, h, h]
        },
        "West": {
            "x": [0, 0, 0, 0],
            "y": [0, EW_dimension, EW_dimension, 0],
            "z": [0, 0, h, h]
        }
    }
    
    # Add direction labels (N, E, S, W) on the ground with increased offset
    offset_factor = max(NS_dimension, EW_dimension) * 0.25  # 25% of the maximum dimension
    direction_labels = {
        "North": {"pos": [NS_dimension/2, -offset_factor, 0], "text": "N"},
        "South": {"pos": [NS_dimension/2, EW_dimension + offset_factor, 0], "text": "S"},
        "East": {"pos": [NS_dimension + offset_factor, EW_dimension/2, 0], "text": "E"},
        "West": {"pos": [-offset_factor, EW_dimension/2, 0], "text": "W"}
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
                    x = [NS_dimension, NS_dimension, NS_dimension, NS_dimension]
                    y = [x_start, x_end, x_end, x_start]
                    z = [0, 0, h, h]
                elif direction == "West":
                    x = [0, 0, 0, 0]
                    y = [width - x_end, width - x_start, width - x_start, width - x_end]
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

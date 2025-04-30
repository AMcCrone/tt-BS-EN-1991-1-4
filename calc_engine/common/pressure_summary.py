import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.colors as pc

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
    # Extract dimensions and peak velocity pressure
    h = session_state.inputs.get("z", 10.0)  # Building height
    qp_value = session_state.inputs.get("qp_value", 1000.0)  # Peak velocity pressure in N/m²
    
    # Define cp,i values
    cp_i_positive = 0.2
    cp_i_negative = -0.3
    
    # Initialize summary data
    summary_data = []
    
    # Process each direction (elevation)
    for direction, cp_df in results_by_direction.items():
        # For each zone in this direction
        for _, row in cp_df.iterrows():
            zone = row['Zone']
            
            # Skip Zone E
            if zone == 'E':
                continue
                
            cp_e = row['cp,e']
            
            # Round cp,e to 2 decimal places
            cp_e = round(cp_e, 2)
            
            # Calculate external pressure
            we = qp_value * cp_e
            
            # Calculate internal pressures
            wi_positive = qp_value * cp_i_positive
            wi_negative = qp_value * cp_i_negative
            
            # Calculate net pressures - most onerous combination
            net_positive = max(we + wi_positive, we - wi_negative)  # Maximum positive pressure
            net_negative = min(we + wi_negative, we - wi_positive)  # Maximum negative pressure
            
            # Determine the governing case (maximum absolute value)
            if abs(net_positive) > abs(net_negative):
                net_pressure = net_positive
                # Determine which internal pressure was used
                if net_positive == (we + wi_positive):
                    cp_i_used = cp_i_positive
                    wi_used = wi_positive
                else:
                    cp_i_used = cp_i_negative
                    wi_used = wi_negative
            else:
                net_pressure = net_negative
                # Determine which internal pressure was used
                if net_negative == (we + wi_negative):
                    cp_i_used = cp_i_negative
                    wi_used = wi_negative
                else:
                    cp_i_used = cp_i_positive
                    wi_used = wi_positive
            
            # Round cp,i to 2 decimal places
            cp_i_used = round(cp_i_used, 2)
            
            # Convert N/m² to kPa and round to 2 decimal places
            we_kpa = round(we / 1000, 2)
            wi_kpa = round(wi_used / 1000, 2)
            net_kpa = round(net_pressure / 1000, 2)
            
            # Determine action type based on net pressure
            action_type = "Pressure" if net_pressure > 0 else "Suction"
            
            # Add to summary data
            summary_data.append({
                "Direction": direction,
                "Zone": zone,
                "cp,e": cp_e,
                "cp,i (used)": cp_i_used,
                "We (kPa)": we_kpa,
                "Wi (kPa)": wi_kpa,
                "Net (kPa)": net_kpa,
                "Action": action_type
            })
    
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
    # Extract dimensions and peak velocity pressure
    h = session_state.inputs.get("z", 10.0)  # Building height
    NS_dimension = session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = session_state.inputs.get("EW_dimension", 40.0)
    qp_value = session_state.inputs.get("qp_value", 1000.0)  # Peak velocity pressure at building height
    
    # Create a continuous color scale for pressure
    colorscale = pc.sequential.Blues_r
    
    # Define cp,i values
    cp_i_positive = 0.2
    cp_i_negative = -0.3
    
    # Storage for all figures
    figures = {}
    
    # Find global pressure range across all directions for consistent colorscale
    global_max_suction = 0
    global_min_suction = 0
    
    # First pass to find global pressure range
    for direction, cp_df in results_by_direction.items():
        # Check all zones
        for zone_name in ['A', 'B', 'C']:
            # Only process if this zone exists in this direction
            if zone_name in cp_df['Zone'].values:
                cp_e = cp_df[cp_df['Zone'] == zone_name]['cp,e'].values[0]
                we = qp_value * cp_e
                
                # Calculate internal pressures
                wi_positive = qp_value * cp_i_positive
                wi_negative = qp_value * cp_i_negative
                
                # Calculate net pressures (minimum of two internal pressure cases)
                net_pressure = min(we + wi_positive, we + wi_negative)
                
                global_max_suction = min(global_max_suction, net_pressure)
                global_min_suction = max(global_min_suction, net_pressure)
    
    # Ensure we have some range to avoid division by zero
    if global_max_suction == global_min_suction:
        global_max_suction = global_min_suction - 1
    
    # Convert pressure range from N/m² to kPa
    global_max_suction_kpa = global_max_suction / 1000
    global_min_suction_kpa = global_min_suction / 1000
    
    # Process each direction (elevation)
    for direction, cp_df in results_by_direction.items():
        # Filter for just the A, B, C zones
        suction_zones = cp_df[cp_df['Zone'].isin(['A', 'B', 'C'])]
        
        # Set up width and height based on direction
        if direction in ["North", "South"]:
            width = EW_dimension
            height = h
            crosswind_dim = NS_dimension
            title = f"{direction} Elevation - Wind Suction Zones"
        else:  # East or West
            width = NS_dimension
            height = h
            crosswind_dim = EW_dimension
            title = f"{direction} Elevation - Wind Suction Zones"
        
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
        
        # Store the pressure values for each zone
        zone_pressures = {}
        
        for zone_name in set(zone_names):
            # Only calculate if this zone exists in this direction
            if zone_name in cp_df['Zone'].values:
                cp_e = cp_df[cp_df['Zone'] == zone_name]['cp,e'].values[0]
                we = qp_value * cp_e
                
                # Calculate internal pressures
                wi_positive = qp_value * cp_i_positive
                wi_negative = qp_value * cp_i_negative
                
                # Calculate net pressure (minimum of two internal pressure cases for suction)
                net_pressure = min(we + wi_positive, we + wi_negative)
                
                # Convert to kPa and round to 2 decimal places
                net_pressure_kpa = round(net_pressure / 1000, 2)
                
                # Store the pressure for this zone
                zone_pressures[zone_name] = net_pressure_kpa
        
        # For each zone, create a single colored rectangle with constant pressure
        for i, ((x0, x1), zone_name) in enumerate(zip(zone_boundaries, zone_names)):
            # Get the pressure value for this zone
            zone_pressure = zone_pressures.get(zone_name, 0)
            
            # Normalize the pressure value for color mapping
            if global_max_suction_kpa == global_min_suction_kpa:
                normalized_value = 0.5  # Default to middle of colorscale if no range
            else:
                normalized_value = (zone_pressure - global_max_suction_kpa) / (global_min_suction_kpa - global_max_suction_kpa)
            normalized_value = max(0, min(1, normalized_value))  # Clamp between 0 and 1
            
            # Get color from colorscale
            color_func = pc.get_colorscale(colorscale)
            zone_color = color_func(normalized_value)[0]
            
            # Add colored rectangle for the zone
            fig.add_shape(
                type="rect",
                x0=x0,
                y0=0,
                x1=x1,
                y1=height,
                fillcolor=zone_color,
                opacity=0.8,
                line=dict(width=0),
                layer="below"
            )
            
            # Add colorbar to figure (only once)
            if i == 0:
                # Create a dummy heatmap just for the colorbar
                dummy_z = [[global_max_suction_kpa, global_max_suction_kpa], 
                          [global_min_suction_kpa, global_min_suction_kpa]]
                fig.add_trace(go.Heatmap(
                    z=dummy_z,
                    x=[0, 0.1],  # Outside visible area
                    y=[0, 0.1],  # Outside visible area
                    colorscale=colorscale,
                    showscale=True,
                    colorbar=dict(
                        title="Suction (kPa)",
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

def visualize_wind_pressures(session_state):
    """
    Create and display wind pressure visualizations including summary table and elevation plots.
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions and other inputs
    
    Returns:
    --------
    tuple
        (summary_df, elevation_figures) - Summary DataFrame and dictionary of plotly figures
    """
    import streamlit as st
    
    # First calculate the cp,e values considering funnelling effects
    results_by_direction = calculate_cpe()
    
    # Create the summary DataFrame
    summary_df = create_pressure_summary(session_state, results_by_direction)
    
    # Create elevation plots
    elevation_figures = plot_elevation_with_pressures(session_state, results_by_direction)
    
    # Display the summary table
    st.subheader("Wind Pressure Summary")
    st.dataframe(summary_df)
    
    # Add download button for the summary table
    csv = summary_df.to_csv(index=False)
    st.download_button(
        label="Download Summary CSV",
        data=csv,
        file_name="wind_pressure_summary.csv",
        mime="text/csv"
    )
    
    # Display elevation plots
    st.subheader("Elevation Wind Pressure Zones")
    
    # Create two columns for North-South elevations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(elevation_figures["North"], use_container_width=True)
    
    with col2:
        st.plotly_chart(elevation_figures["South"], use_container_width=True)
    
    # Create two columns for East-West elevations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(elevation_figures["East"], use_container_width=True)
    
    with col2:
        st.plotly_chart(elevation_figures["West"], use_container_width=True)
    
    return summary_df, elevation_figures

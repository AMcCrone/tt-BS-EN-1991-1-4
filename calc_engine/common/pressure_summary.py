import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

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
    Create plots for all four elevations showing wind zones A, B, C with pressure gradients
    that vary with height according to the building's height-to-width ratio.
    
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
    import numpy as np
    import plotly.graph_objects as go
    import plotly.colors as pc
    
    # Extract dimensions and peak velocity pressure
    h = session_state.inputs.get("z", 10.0)  # Building height
    NS_dimension = session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = session_state.inputs.get("EW_dimension", 40.0)
    qp_reference = session_state.inputs.get("qp_value", 1000.0)  # Reference peak velocity pressure in N/m²
    
    # Create a continuous color scale for pressure
    colorscale = pc.sequential.Blues_r
    
    # Define cp,i values
    cp_i_positive = 0.2
    cp_i_negative = -0.3
    
    # Storage for all figures
    figures = {}
    
    # Process each direction (elevation)
    for direction, cp_df in results_by_direction.items():
        # Filter for just the A, B, C zones
        suction_zones = cp_df[cp_df['Zone'].isin(['A', 'B', 'C'])]
        
        # Set up width and height based on direction
        if direction in ["North", "South"]:
            width = EW_dimension
            height = h
            building_width = EW_dimension  # Width perpendicular to wind direction
            crosswind_dim = NS_dimension
            title = f"{direction} Elevation - Wind Suction Zones"
        else:  # East or West
            width = NS_dimension
            height = h
            building_width = NS_dimension  # Width perpendicular to wind direction
            crosswind_dim = EW_dimension
            title = f"{direction} Elevation - Wind Suction Zones"
        
        # Calculate parameter e according to Eurocode
        e = min(crosswind_dim, 2 * height)
        
        # Determine profile case based on building dimensions
        if height <= building_width:
            profile_case = "Case 1: h ≤ b"
        elif building_width < height <= 2 * building_width:
            profile_case = "Case 2: b < h ≤ 2b"
        else:
            profile_case = "Case 3: h > 2b"
        
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
        
        # Define a function to get pressure at a specific height
        def get_qp_at_height(z, h, b, qp_reference):
            """Calculate qp at height z for a building with height h and width b."""
            if h <= b:  # Case 1
                return qp_reference  # Constant for entire height
            elif b < h <= 2*b:  # Case 2
                if z <= b:
                    return qp_reference
                else:
                    # Linear interpolation between qp_reference and qp_reference*1.2
                    return qp_reference + (qp_reference*0.2) * (z - b) / (h - b)
            else:  # Case 3: h > 2b
                if z <= b:
                    return qp_reference
                elif b < z <= (h - b):
                    # Middle section: linear from qp_reference to qp_reference*1.35
                    return qp_reference + (qp_reference*0.35) * (z - b) / ((h - b) - b)
                else:
                    # Top section: linear from qp_reference*1.35 to qp_reference*1.5
                    return qp_reference*1.35 + (qp_reference*0.15) * (z - (h - b)) / (h - (h - b))
        
        # Find the maximum and minimum pressure values across all heights for color scaling
        max_suction = 0
        min_suction = 0
        height_samples = 20  # Number of vertical segments to check
        
        # Store the maximum pressure values for each zone (at maximum height)
        zone_max_pressures = {}
        
        for zone_name in set(zone_names):
            # Calculate pressure at maximum height (h) for this zone
            qp_value = get_qp_at_height(height, height, building_width, qp_reference)
            cp_e = cp_df[cp_df['Zone'] == zone_name]['cp,e'].values[0]
            we = qp_value * cp_e
            
            # Calculate internal pressures
            wi_positive = qp_value * cp_i_positive
            wi_negative = qp_value * cp_i_negative
            
            # Calculate net pressure (minimum of two internal pressure cases)
            net_pressure = min(we + wi_positive, we + wi_negative)
            
            # Store the maximum pressure for this zone
            zone_max_pressures[zone_name] = net_pressure
        
        # Calculate the range of pressures for all heights
        for z in np.linspace(0, height, height_samples):
            qp_value = get_qp_at_height(z, height, building_width, qp_reference)
            
            for zone_name in set(zone_names):
                cp_e = cp_df[cp_df['Zone'] == zone_name]['cp,e'].values[0]
                we = qp_value * cp_e
                
                # Calculate internal pressures
                wi_positive = qp_value * cp_i_positive
                wi_negative = qp_value * cp_i_negative
                
                # Calculate net pressures (we're only interested in suction for A, B, C)
                net_pressure = min(we + wi_positive, we + wi_negative)
                
                max_suction = min(max_suction, net_pressure)
                min_suction = max(min_suction, net_pressure)
        
        # Ensure we have some range to avoid division by zero
        if max_suction == min_suction:
            max_suction = min_suction - 1
        
        # For each zone, create a heatmap to show pressure variation with height
        for i, ((x0, x1), zone_name) in enumerate(zip(zone_boundaries, zone_names)):
            # Get the cp_e value for this zone
            cp_e = cp_df[cp_df['Zone'] == zone_name]['cp,e'].values[0]
            
            # Create a grid for the heatmap
            x_steps = 10  # horizontal resolution
            y_steps = 50  # vertical resolution
            
            # Create slightly inset boundaries to avoid overlapping the building outline
            # Inset by a very small amount (0.5% of width) to avoid overlapping the building edge
            inset = width * 0.005
            x_vals = np.linspace(x0 + inset, x1 - inset, x_steps)
            y_vals = np.linspace(inset, height - inset, y_steps)
            
            # Create meshgrid for heatmap
            X, Y = np.meshgrid(x_vals, y_vals)
            Z = np.zeros((y_steps, x_steps))
            
            # Fill Z with pressure values that vary with height
            for j, y in enumerate(y_vals):
                qp_value = get_qp_at_height(y, height, building_width, qp_reference)
                we = qp_value * cp_e
                
                # Calculate internal pressures
                wi_positive = qp_value * cp_i_positive
                wi_negative = qp_value * cp_i_negative
                
                # Calculate net pressure (minimum of two internal pressure cases)
                net_pressure = min(we + wi_positive, we + wi_negative)
                
                # Fill the entire row with the same pressure value
                Z[j, :] = net_pressure
            
            # Create heatmap for this zone
            fig.add_trace(go.Heatmap(
                z=Z,
                x=x_vals,
                y=y_vals,
                colorscale=colorscale,
                showscale=(i == 0),  # Only show colorbar for the first zone
                colorbar=dict(
                    title="Suction (N/m²)",
                    x=1.05,
                    y=0.5,
                    lenmode="fraction",
                    len=0.9
                ),
                zmin=max_suction,
                zmax=min_suction,
                name=f"Zone {zone_name}"
            ))
            
            # Add zone label with maximum pressure value
            max_pressure = zone_max_pressures[zone_name]
            fig.add_annotation(
                x=(x0 + x1)/2,
                y=height/2,
                text=f"Zone {zone_name}<br>{max_pressure:.0f} N/m²",
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
        
        # Add reference height lines and annotations
        if height <= building_width:
            # Case 1: Only mark h
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
            
        elif building_width < height <= 2*building_width:
            # Case 2: Mark b and h
            fig.add_shape(
                type="line",
                x0=-0.05*width, y0=building_width, 
                x1=0, y1=building_width,
                line=dict(color="black", width=1)
            )
            fig.add_shape(
                type="line",
                x0=-0.05*width, y0=height, 
                x1=0, y1=height,
                line=dict(color="black", width=1)
            )
            fig.add_annotation(
                x=-0.02*width, y=building_width,
                text=f"b = {building_width:.1f}m",
                showarrow=False,
                font=dict(size=12),
                xanchor="right",
                yanchor="middle"
            )
            fig.add_annotation(
                x=-0.02*width, y=height,
                text=f"h = {height:.1f}m",
                showarrow=False,
                font=dict(size=12),
                xanchor="right",
                yanchor="middle"
            )
            
        else:  # h > 2*b
            # Case 3: Mark b, h-b, and h
            z_strip = height - building_width
            fig.add_shape(
                type="line",
                x0=-0.05*width, y0=building_width, 
                x1=0, y1=building_width,
                line=dict(color="black", width=1)
            )
            fig.add_shape(
                type="line",
                x0=-0.05*width, y0=z_strip, 
                x1=0, y1=z_strip,
                line=dict(color="black", width=1)
            )
            fig.add_shape(
                type="line",
                x0=-0.05*width, y0=height, 
                x1=0, y1=height,
                line=dict(color="black", width=1)
            )
            fig.add_annotation(
                x=-0.02*width, y=building_width,
                text=f"b = {building_width:.1f}m",
                showarrow=False,
                font=dict(size=12),
                xanchor="right",
                yanchor="middle"
            )
            fig.add_annotation(
                x=-0.02*width, y=z_strip,
                text=f"h-b = {z_strip:.1f}m",
                showarrow=False,
                font=dict(size=12),
                xanchor="right",
                yanchor="middle"
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
        
        # Add title with profile case
        fig.update_layout(
            title=f"{title}<br><sup>{profile_case}</sup>",
            showlegend=False,  # No legend needed since hatches are removed
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

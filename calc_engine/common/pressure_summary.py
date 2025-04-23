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
    Create plots for all four elevations showing wind zones A, B, C with pressure gradients.
    
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
    qp_value = session_state.inputs.get("qp_value", 1000.0)  # Peak velocity pressure in N/m²
    
    # Define colors for pressure gradient (suction)
    import plotly.colors as pc
    
    # Create a continuous color scale for pressure
    # We'll use a blue color scale from light to dark for increasing suction
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
            title = f"{direction} Elevation - Wind Suction Zones"
        else:  # East or West
            width = NS_dimension
            height = h
            title = f"{direction} Elevation - Wind Suction Zones"
        
        # Calculate parameter e according to Eurocode
        if direction in ["North", "South"]:
            crosswind_dim = NS_dimension
        else:
            crosswind_dim = EW_dimension
        
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
        
        # Find the maximum suction (most negative) for color scaling
        max_suction = 0
        min_suction = 0
        
        # Calculate external pressures and find max suction
        for zone_name in set(zone_names):
            cp_e = cp_df[cp_df['Zone'] == zone_name]['cp,e'].values[0]
            we = qp_value * cp_e
            
            # Calculate internal pressures
            wi_positive = qp_value * cp_i_positive
            wi_negative = qp_value * cp_i_negative
            
            # Calculate net pressures (we're only interested in suction for A, B, C)
            net_pressure = min(we + wi_positive, we + wi_negative)
            
            # Update max suction
            max_suction = min(max_suction, net_pressure)
            if net_pressure > min_suction:
                min_suction = net_pressure
        
        # Ensure we have some range to avoid division by zero
        if max_suction == min_suction:
            max_suction = min_suction - 1
        
        # Create a zone-pattern mapping to ensure we can distinguish zones
        # even with color gradient
        zone_patterns = {
            'A': '/',    # Forward slash pattern for zone A
            'B': '\\',   # Backslash pattern for zone B
            'C': 'x'     # Cross-hatch pattern for zone C
        }
        
        # Draw the zones
        for i, ((x0, x1), zone_name) in enumerate(zip(zone_boundaries, zone_names)):
            # Get the pressure value for this zone
            cp_e = cp_df[cp_df['Zone'] == zone_name]['cp,e'].values[0]
            we = qp_value * cp_e
            
            # Calculate net pressure (minimum of two internal pressure cases)
            net_positive = we + qp_value * cp_i_positive
            net_negative = we + qp_value * cp_i_negative
            net_pressure = min(net_positive, net_negative)
            
            # Calculate color intensity based on pressure
            # Normalize to 0-1 range for color mapping
            if max_suction == min_suction:
                color_intensity = 0.5
            else:
                # More negative (stronger suction) = darker color
                color_intensity = (net_pressure - min_suction) / (max_suction - min_suction)
            
            # Convert to RGB color
            color_rgb = pc.sample_colorscale(colorscale, [1-color_intensity])[0]
            
            # Draw zone rectangle
            fig.add_shape(
                type="rect",
                x0=x0,
                y0=0,
                x1=x1,
                y1=height,
                line=dict(width=1, color="black"),
                fillcolor=color_rgb,
                opacity=0.8,
                layer="below"
            )
            
            # Add zone label with pressure value
            fig.add_annotation(
                x=(x0 + x1)/2,
                y=height/2,
                text=f"Zone {zone_name}<br>{net_pressure:.0f} N/m²",
                showarrow=False,
                font=dict(size=16, color="white")
            )
            
            # Add pattern overlay to help distinguish zones
            # We can simulate this with a scatter plot using a marker
            x_points = np.linspace(x0, x1, int((x1-x0)+1))
            y_points = np.linspace(0, height, int(height+1))
            x_grid, y_grid = np.meshgrid(x_points, y_points)
            x_flat = x_grid.flatten()
            y_flat = y_grid.flatten()
            
            # Only show every nth point to avoid overcrowding
            step = max(1, int(len(x_flat) / 500))
            
            # Define a mapping of zone names to valid Plotly marker symbols
            zone_symbol_map = {
                'A': 'circle',
                'B': 'square',
                'C': 'diamond'
            }
            
            fig.add_trace(go.Scatter(
                x=x_flat[::step],
                y=y_flat[::step],
                mode='markers',
                marker=dict(
                    symbol=zone_symbol_map.get(zone_name, 'circle'),  # Use valid symbol based on zone
                    size=8,
                    color='white',
                    opacity=0.3,
                    line=dict(width=0)
                ),
                name=f"Zone {zone_name} Pattern",
                hoverinfo='none',
                showlegend=False
            ))
        
        # Add building outline
        fig.add_shape(
            type="rect",
            x0=0,
            y0=0,
            x1=width,
            y1=height,
            line=dict(width=2, color="black"),
            fillcolor=None,
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
        
        # Add colorbar for pressure gradient
        fig.add_trace(go.Contour(
            z=[[min_suction, max_suction], [min_suction, max_suction]],
            x=[0, 0.01],  # Small dummy x range
            y=[0, 0.01],  # Small dummy y range
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title="Suction (N/m²)",
                x=1.05,
                y=0.5,
                lenmode="fraction",
                len=0.9
            ),
            zmin=max_suction,
            zmax=min_suction
        ))
        
        # Add e and d dimensions as annotations
        fig.add_annotation(
            x=width/2,
            y=-0.05*height,
            text=f"d = {width:.2f}",
            showarrow=False,
            font=dict(size=12)
        )
        
        fig.add_annotation(
            x=-0.05*width,
            y=height/2,
            text=f"h = {height:.2f}",
            showarrow=False,
            font=dict(size=12),
            textangle=-90
        )
        
        fig.add_annotation(
            x=width/2,
            y=1.05*height,
            text=f"e = {e:.2f} ({'<' if e < width else '≥'} d)",
            showarrow=False,
            font=dict(size=12, color="black")
        )
        
        # Add a legend for the zone patterns
        for zone in ['A', 'B', 'C']:
            if zone in set(zone_names):
                fig.add_trace(go.Scatter(
                    x=[None],
                    y=[None],
                    mode='markers',
                    marker=dict(
                        size=10,
                        symbol=zone_symbol_map.get(zone, 'circle'),  # Use valid symbol based on zone
                        color='white',
                        line=dict(color='black', width=1)
                    ),
                    name=f"Zone {zone}",
                    showlegend=True
                ))
        
        # Update layout
        fig.update_layout(
            title=title,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
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

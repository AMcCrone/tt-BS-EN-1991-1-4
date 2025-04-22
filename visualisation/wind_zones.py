import plotly.graph_objects as go

def plot_wind_zones(session_state):
    """
    Create plots showing wind zones on building elevations according to Eurocode 1991-1-4.
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions
    
    Returns:
    --------
    tuple
        (NS_elevation_fig, EW_elevation_fig) - Plotly figures for N-S and E-W elevations
    """
    # Extract building dimensions from session state
    NS_dimension = session_state.inputs["NS_dimension"]
    EW_dimension = session_state.inputs["EW_dimension"]
    z = session_state.inputs["z"]  # Building height
    
    # Zone colors with gradient from darkest (A) to lightest (C)
    zone_colors = {
        'A': 'rgb(0,48,60)',      # Darkest - Zone A
        'B': 'rgb(0,163,173)',    # Medium - Zone B
        'C': 'rgb(136,219,223)'   # Lightest - Zone C
    }
    
    # Create figures for both elevations
    NS_elevation_fig = create_elevation_plot(
        width=NS_dimension,
        height=z,
        crosswind_dim=EW_dimension,
        zone_colors=zone_colors,
        title="North-South Elevation Wind Zones"
    )
    
    EW_elevation_fig = create_elevation_plot(
        width=EW_dimension,
        height=z,
        crosswind_dim=NS_dimension,
        zone_colors=zone_colors,
        title="East-West Elevation Wind Zones"
    )
    
    return NS_elevation_fig, EW_elevation_fig

def create_elevation_plot(width, height, crosswind_dim, zone_colors, title):
    """
    Create a single elevation plot with wind zones.
    
    Parameters:
    -----------
    width : float
        Width of elevation (d)
    height : float
        Height of elevation (h)
    crosswind_dim : float
        Crosswind dimension (b)
    zone_colors : dict
        Dictionary of colors for each zone
    title : str
        Plot title
    
    Returns:
    --------
    plotly.graph_objects.Figure
        Figure with the elevation and wind zones
    """
    # Calculate parameter e according to Eurocode
    e = min(crosswind_dim, 2 * height)
    
    # Create figure
    fig = go.Figure()
    
    # Determine zones based on relation between e and d
    if e < width:  # Three zones: A, B, C
        # Calculate zone boundaries from left to right
        zone_boundaries = []
        zone_names = []
        
        # Left wind direction (from left to right)
        # Zone A (left)
        zone_boundaries.append((0, e/5))
        zone_names.append('A')
        
        # Zone B (left)
        zone_boundaries.append((e/5, e))
        zone_names.append('B')
        
        # Zone C (middle)
        zone_boundaries.append((e, width-e))
        zone_names.append('C')
        
        # Zone B (right)
        zone_boundaries.append((width-e, width-e/5))
        zone_names.append('B')
        
        # Zone A (right)
        zone_boundaries.append((width-e/5, width))
        zone_names.append('A')
        
        # Check and fix any overlapping zones
        # If e/5 from both ends would overlap
        if width < 2*(e/5):
            # Single zone A for the whole width
            zone_boundaries = [(0, width)]
            zone_names = ['A']
        # If zones B would overlap with C
        elif width < 2*e:
            # We have A zones at both ends, B zones meet in middle
            zone_boundaries = [
                (0, e/5),              # Left A
                (e/5, width/2),        # Left B
                (width/2, width-e/5),  # Right B
                (width-e/5, width)     # Right A
            ]
            zone_names = ['A', 'B', 'B', 'A']
        
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
    
    # Draw the zones
    for i, ((x0, x1), zone_name) in enumerate(zip(zone_boundaries, zone_names)):
        # Draw zone rectangle
        fig.add_shape(
            type="rect",
            x0=x0,
            y0=0,
            x1=x1,
            y1=height,
            line=dict(width=1, color="black"),
            fillcolor=zone_colors[zone_name],
            opacity=0.7,
            layer="below"
        )
        
        # Add zone label
        zone_width = x1 - x0
        fig.add_annotation(
            x=(x0 + x1)/2,
            y=height/2,
            text=zone_name,
            showarrow=False,
            font=dict(size=24, color="white")
        )
        
        # Add zone width label
        if zone_width > 0.05 * width:  # Only add label if zone is wide enough
            fig.add_annotation(
                x=(x0 + x1)/2,
                y=height/4,
                text=f"{zone_width:.2f}",
                showarrow=False,
                font=dict(size=12, color="white")
            )
    
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
    
    # Update layout
    fig.update_layout(
        title=title,
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
        height=400
    )
    
    return fig

def integrate_with_streamlit(session_state):
    """
    Example of how to integrate with Streamlit
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions
    """
    import streamlit as st
    
    # Get the elevation plots
    ns_fig, ew_fig = plot_wind_zones(session_state)
    
    # Display in Streamlit
    st.subheader("Wind Zones - North-South Elevation")
    st.plotly_chart(ns_fig, use_container_width=True)
    
    st.subheader("Wind Zones - East-West Elevation")
    st.plotly_chart(ew_fig, use_container_width=True)

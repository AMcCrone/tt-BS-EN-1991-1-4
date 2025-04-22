import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    
    # Define colors - using the same color scheme as in the example
    TT_LightBlue = "rgb(136,219,223)"
    TT_MidBlue = "rgb(0,163,173)"
    TT_DarkBlue = "rgb(0,48,60)"
    
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
        zone_widths = [e/5, 4*e/5, width-e]
        zone_names = ['A', 'B', 'C', 'B', 'A']
        
        # Left side (wind from left)
        x_positions = [0]
        for w in zone_widths:
            x_positions.append(x_positions[-1] + w)
        
        # Right side (wind from right) - mirror the zones
        x_positions_right = [width - x for x in x_positions]
        x_positions_right.reverse()
        
        # If zones overlap in the middle, adjust them
        if e > width/2:
            # Calculate the midpoint
            mid = width / 2
            # Find where zone B starts on the left side
            left_b_start = e/5
            # Find where zone B starts on the right side (coming from the right)
            right_b_start = width - e/5
            
            # If zones overlap
            if left_b_start < mid and right_b_start > mid:
                # Simplified: just meet at the middle
                zone_names = ['A', 'B', 'B', 'A']
                x_positions = [0, e/5, mid, width-e/5, width]
            else:
                # Non-overlapping case
                x_positions = x_positions + x_positions_right[1:]
        else:
            # Non-overlapping case
            x_positions = x_positions + x_positions_right[1:]
        
    elif e >= width and e < 5*width:  # Two zones: A, B
        # Calculate zone widths
        zone_a_width = e/5
        zone_b_width = width - 2*(e/5) if width - 2*(e/5) > 0 else 0
        
        x_positions = [0, zone_a_width, zone_a_width + zone_b_width, width]
        zone_names = ['A', 'B', 'A']
        
    else:  # One zone: A
        x_positions = [0, width]
        zone_names = ['A']
    
    # Draw the zones
    for i in range(len(zone_names)):
        if i < len(x_positions) - 1:  # Check if there's a corresponding position segment
            fig.add_shape(
                type="rect",
                x0=x_positions[i],
                y0=0,
                x1=x_positions[i+1],
                y1=height,
                line=dict(width=1, color="black"),
                fillcolor=zone_colors[zone_names[i]],
                opacity=0.7,
                layer="below"
            )
            
            # Add zone label
            fig.add_annotation(
                x=(x_positions[i] + x_positions[i+1])/2,
                y=height/2,
                text=zone_names[i],
                showarrow=False,
                font=dict(size=24, color="white")
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
    
    # Add wind arrows on both sides
    # Left side arrow
    fig.add_annotation(
        x=-0.05*width,
        y=height/2,
        ax=0.05*width,
        ay=height/2,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text="",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2,
        arrowcolor="black"
    )
    
    # Right side arrow
    fig.add_annotation(
        x=1.05*width,
        y=height/2,
        ax=0.95*width,
        ay=height/2,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text="",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2,
        arrowcolor="black"
    )
    
    # Add e and d dimensions as annotations
    fig.add_annotation(
        x=width/2,
        y=-0.1*height,
        text=f"d = {width:.2f}",
        showarrow=False,
        font=dict(size=12)
    )
    
    fig.add_annotation(
        x=-0.15*width,
        y=height/2,
        text=f"h = {height:.2f}",
        showarrow=False,
        font=dict(size=12),
        textangle=-90
    )
    
    fig.add_annotation(
        x=width/2,
        y=1.1*height,
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
            range=[-0.2*width, 1.2*width]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.2*height, 1.2*height],
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

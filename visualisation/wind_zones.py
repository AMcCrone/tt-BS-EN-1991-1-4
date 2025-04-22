import plotly.graph_objects as go
import numpy as np

def create_3d_wind_zones(session_state):
    """
    Create a 3D visualization of the building with wind zones.
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions
    
    Returns:
    --------
    plotly.graph_objects.Figure
        3D figure showing the building with wind zones
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
    
    # Calculate parameter e according to Eurocode for both directions
    e_NS = min(EW_dimension, 2 * z)  # For North-South face, crosswind is EW
    e_EW = min(NS_dimension, 2 * z)  # For East-West face, crosswind is NS
    
    # Create figure
    fig = go.Figure()
    
    # Create the base building
    # Bottom face
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, EW_dimension, EW_dimension],
        z=[0, 0, 0, 0],
        i=[0], j=[1], k=[2],
        color='white',
        opacity=0.7,
        showlegend=False,
        hoverinfo='none'
    ))
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, 0],
        y=[EW_dimension, EW_dimension, 0],
        z=[0, 0, 0],
        i=[0], j=[1], k=[2],
        color='white',
        opacity=0.7,
        showlegend=False,
        hoverinfo='none'
    ))
    
    # Top face
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, EW_dimension, EW_dimension],
        z=[z, z, z, z],
        i=[0], j=[1], k=[2],
        color='white',
        opacity=0.7,
        showlegend=False,
        hoverinfo='none'
    ))
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, 0],
        y=[EW_dimension, EW_dimension, 0],
        z=[z, z, z],
        i=[0], j=[1], k=[2],
        color='white',
        opacity=0.7,
        showlegend=False,
        hoverinfo='none'
    ))
    
    # Calculate zone boundaries for North-South elevations (front and back)
    NS_zone_data = calculate_zone_data(NS_dimension, z, e_NS)
    
    # Calculate zone boundaries for East-West elevations (left and right)
    EW_zone_data = calculate_zone_data(EW_dimension, z, e_EW)
    
    # Draw North face (y=0) zones
    for zone in NS_zone_data:
        zone_name, x_start, x_end = zone
        
        fig.add_trace(go.Mesh3d(
            x=[x_start, x_end, x_end, x_start],
            y=[0, 0, 0, 0],
            z=[0, 0, z, z],
            i=[0], j=[1], k=[2],
            color=zone_colors[zone_name],
            opacity=0.9,
            showlegend=False,
            hoverinfo='text',
            hovertext=f"Zone {zone_name}: Width={x_end-x_start:.2f}"
        ))
        
        # Add zone label for North face
        if x_end - x_start > 0.1 * NS_dimension:  # Only add label if zone is wide enough
            fig.add_trace(go.Scatter3d(
                x=[(x_start + x_end) / 2],
                y=[0],
                z=[z / 2],
                mode='text',
                text=[zone_name],
                textfont=dict(size=18, color='white'),
                showlegend=False
            ))
    
    # Draw South face (y=EW_dimension) zones
    for zone in NS_zone_data:
        zone_name, x_start, x_end = zone
        
        fig.add_trace(go.Mesh3d(
            x=[x_start, x_end, x_end, x_start],
            y=[EW_dimension, EW_dimension, EW_dimension, EW_dimension],
            z=[0, 0, z, z],
            i=[0], j=[1], k=[2],
            color=zone_colors[zone_name],
            opacity=0.9,
            showlegend=False,
            hoverinfo='text',
            hovertext=f"Zone {zone_name}: Width={x_end-x_start:.2f}"
        ))
        
        # Add zone label for South face
        if x_end - x_start > 0.1 * NS_dimension:  # Only add label if zone is wide enough
            fig.add_trace(go.Scatter3d(
                x=[(x_start + x_end) / 2],
                y=[EW_dimension],
                z=[z / 2],
                mode='text',
                text=[zone_name],
                textfont=dict(size=18, color='white'),
                showlegend=False
            ))
    
    # Draw West face (x=0) zones
    for zone in EW_zone_data:
        zone_name, y_start, y_end = zone
        
        fig.add_trace(go.Mesh3d(
            x=[0, 0, 0, 0],
            y=[y_start, y_end, y_end, y_start],
            z=[0, 0, z, z],
            i=[0], j=[1], k=[2],
            color=zone_colors[zone_name],
            opacity=0.9,
            showlegend=False,
            hoverinfo='text',
            hovertext=f"Zone {zone_name}: Width={y_end-y_start:.2f}"
        ))
        
        # Add zone label for West face
        if y_end - y_start > 0.1 * EW_dimension:  # Only add label if zone is wide enough
            fig.add_trace(go.Scatter3d(
                x=[0],
                y=[(y_start + y_end) / 2],
                z=[z / 2],
                mode='text',
                text=[zone_name],
                textfont=dict(size=18, color='white'),
                showlegend=False
            ))
    
    # Draw East face (x=NS_dimension) zones
    for zone in EW_zone_data:
        zone_name, y_start, y_end = zone
        
        fig.add_trace(go.Mesh3d(
            x=[NS_dimension, NS_dimension, NS_dimension, NS_dimension],
            y=[y_start, y_end, y_end, y_start],
            z=[0, 0, z, z],
            i=[0], j=[1], k=[2],
            color=zone_colors[zone_name],
            opacity=0.9,
            showlegend=False,
            hoverinfo='text',
            hovertext=f"Zone {zone_name}: Width={y_end-y_start:.2f}"
        ))
        
        # Add zone label for East face
        if y_end - y_start > 0.1 * EW_dimension:  # Only add label if zone is wide enough
            fig.add_trace(go.Scatter3d(
                x=[NS_dimension],
                y=[(y_start + y_end) / 2],
                z=[z / 2],
                mode='text',
                text=[zone_name],
                textfont=dict(size=18, color='white'),
                showlegend=False
            ))
    
    # Add building edge lines for better visibility
    edges_x = [0, NS_dimension, NS_dimension, 0, 0, 0, NS_dimension, NS_dimension, 0, 0, NS_dimension, NS_dimension]
    edges_y = [0, 0, EW_dimension, EW_dimension, 0, 0, 0, EW_dimension, EW_dimension, 0, 0, EW_dimension]
    edges_z = [0, 0, 0, 0, z, 0, 0, 0, 0, z, z, z]
    
    fig.add_trace(go.Scatter3d(
        x=edges_x,
        y=edges_y,
        z=edges_z,
        mode='lines',
        line=dict(color='black', width=4),
        showlegend=False
    ))
    
    # Add more edge lines
    fig.add_trace(go.Scatter3d(
        x=[0, 0, NS_dimension, NS_dimension],
        y=[EW_dimension, EW_dimension, EW_dimension, EW_dimension],
        z=[0, z, z, 0],
        mode='lines',
        line=dict(color='black', width=4),
        showlegend=False
    ))
    
    # Add title and other information
    fig.update_layout(
        title=dict(
            text="3D Building with Wind Zones",
            x=0.5,
            y=0.95
        ),
        scene=dict(
            xaxis=dict(title="North-South Dimension"),
            yaxis=dict(title="East-West Dimension"),
            zaxis=dict(title="Height"),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        scene_camera=dict(
            eye=dict(x=1.8, y=1.8, z=1.2)
        ),
        height=600
    )
    
    # Add building dimensions annotation
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=f"Building: {NS_dimension:.1f}m × {EW_dimension:.1f}m × {z:.1f}m<br>e_NS = {e_NS:.1f}m, e_EW = {e_EW:.1f}m",
        showarrow=False,
        font=dict(size=12),
        bgcolor="white",
        opacity=0.8,
        bordercolor="black",
        borderwidth=1
    )
    
    return fig

def calculate_zone_data(width, height, e):
    """
    Calculate the zone boundaries and names for a given elevation.
    
    Parameters:
    -----------
    width : float
        Width of elevation (d)
    height : float
        Height of elevation (h)
    e : float
        Parameter e = min(b, 2h)
    
    Returns:
    --------
    list
        List of tuples (zone_name, x_start, x_end)
    """
    zones = []
    
    # Determine zones based on relation between e and width
    if e < width:  # Three zones: A, B, C
        # Check if zones would overlap
        if width < 2*e:  # Zones would overlap in the middle
            # If e/5 from both ends would overlap (very narrow building)
            if width <= 2*(e/5):
                # Single zone A for the whole width
                zones.append(('A', 0, width))
            else:
                # A-B-A pattern (simplified from A-B-B-A)
                zones.append(('A', 0, e/5))
                zones.append(('B', e/5, width - e/5))
                zones.append(('A', width - e/5, width))
        else:
            # Standard case with A, B, C, B, A
            zones.append(('A', 0, e/5))
            zones.append(('B', e/5, e))
            zones.append(('C', e, width - e))
            zones.append(('B', width - e, width - e/5))
            zones.append(('A', width - e/5, width))
    
    elif e >= width and e < 5*width:  # Two zones: A, B
        # If building is narrow compared to e, A zones might overlap
        if width <= 2*(e/5):
            # Only zone A across entire width
            zones.append(('A', 0, width))
        else:
            # Normal case with A-B-A
            zones.append(('A', 0, e/5))
            zones.append(('B', e/5, width - e/5))
            zones.append(('A', width - e/5, width))
        
    else:  # e >= 5*width, One zone: A
        zones.append(('A', 0, width))
    
    return zones

def integrate_3d_with_streamlit(session_state):
    """
    Example of how to integrate the 3D visualization with Streamlit
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions
    """
    import streamlit as st
    
    # Get the 3D plot
    fig_3d = create_3d_wind_zones(session_state)
    
    # Display in Streamlit
    st.subheader("3D Building with Wind Zones")
    st.plotly_chart(fig_3d, use_container_width=True)

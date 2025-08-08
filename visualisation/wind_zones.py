# visualisation/wind_zones.py
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

import plotly.graph_objects as go

import plotly.graph_objects as go

def create_elevation_plot(width, height, crosswind_dim, zone_colors, title):
    """
    Create a single elevation plot with wind zones.
    Width labels now have small white arrows pointing to zone boundaries,
    with adjustable offset and standoff so text and arrows don't overlap.
    """
    # Adjustable settings for dimension arrows
    arrow_offset_factor = 0.25  # proportion of zone width from text to arrow start
    arrow_standoff_px = 0      # extra pixel gap between zone boundary and arrowhead
    arrow_head_size = 0.6      # relative arrowhead size
    arrow_line_width = 1       # arrow line width

    e = min(crosswind_dim, 2 * height)
    fig = go.Figure()

    zone_boundaries = []
    zone_names = []

    if e < width:
        if width < 2*e:
            if width <= 2*(e/5):
                zone_boundaries = [(0, width)]
                zone_names = ['A']
            else:
                zone_boundaries = [
                    (0, e/5),
                    (e/5, width - e/5),
                    (width - e/5, width)
                ]
                zone_names = ['A', 'B', 'A']
        else:
            if width - 2*e <= 0:
                zone_boundaries = [
                    (0, e/5),
                    (e/5, width - e/5),
                    (width - e/5, width)
                ]
                zone_names = ['A', 'B', 'A']
            else:
                zone_boundaries = [
                    (0, e/5),
                    (e/5, e),
                    (e, width - e),
                    (width - e, width - e/5),
                    (width - e/5, width)
                ]
                zone_names = ['A', 'B', 'C', 'B', 'A']
    elif e >= width and e < 5*width:
        if width <= 2*(e/5):
            zone_boundaries = [(0, width)]
            zone_names = ['A']
        else:
            zone_boundaries = [
                (0, e/5),
                (e/5, width-e/5),
                (width-e/5, width)
            ]
            zone_names = ['A', 'B', 'A']
    else:
        zone_boundaries = [(0, width)]
        zone_names = ['A']

    for (x0, x1), zone_name in zip(zone_boundaries, zone_names):
        # Draw zone rectangle
        fig.add_shape(
            type="rect",
            x0=x0, y0=0, x1=x1, y1=height,
            line=dict(width=1, color="black"),
            fillcolor=zone_colors[zone_name],
            opacity=0.7,
            layer="below"
        )

        # Zone label (big letter)
        fig.add_annotation(
            x=(x0 + x1)/2, y=height/2,
            text=zone_name,
            showarrow=False,
            font=dict(size=24, color="white")
        )

        # Dimension-style width label with arrows
        zone_width = x1 - x0
        if zone_width > 0.05 * width:
            label_x = (x0 + x1) / 2
            label_y = height / 4

            # Text (no box)
            fig.add_annotation(
                x=label_x, y=label_y,
                text=f"{zone_width:.2f}",
                showarrow=False,
                font=dict(size=12, color="white")
            )

            # Left arrow
            fig.add_annotation(
                x=x0, y=label_y,
                ax=label_x - arrow_offset_factor * zone_width, ay=label_y,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=arrow_head_size,
                arrowwidth=arrow_line_width,
                arrowcolor="white",
                standoff=arrow_standoff_px
            )
            # Right arrow
            fig.add_annotation(
                x=x1, y=label_y,
                ax=label_x + arrow_offset_factor * zone_width, ay=label_y,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=arrow_head_size,
                arrowwidth=arrow_line_width,
                arrowcolor="white",
                standoff=arrow_standoff_px
            )

    # Building outline
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=width, y1=height,
        line=dict(width=2, color="black"),
        fillcolor=None, opacity=1, layer="above"
    )
    # Ground line
    fig.add_shape(
        type="line",
        x0=-0.1*width, y0=0, x1=1.1*width, y1=0,
        line=dict(width=3, color="black"),
        layer="above"
    )
    # e, d, h labels
    fig.add_annotation(
        x=width/2, y=-0.05*height,
        text=f"d = {width:.2f}", showarrow=False, font=dict(size=12)
    )
    fig.add_annotation(
        x=-0.05*width, y=height/2,
        text=f"h = {height:.2f}", showarrow=False, font=dict(size=12),
        textangle=-90
    )
    fig.add_annotation(
        x=width/2, y=1.05*height,
        text=f"e = {e:.2f} ({'<' if e < width else '≥'} d)",
        showarrow=False, font=dict(size=12, color="black")
    )

    fig.update_layout(
        title=title,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.1*width, 1.1*width]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.1*height, 1.1*height], scaleanchor="x", scaleratio=1),
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

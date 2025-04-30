import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Define TT colors
TT_Orange = "rgb(211,69,29)"
TT_LightBlue = "rgb(136,219,223)" 
TT_MidBlue = "rgb(0,163,173)"
TT_DarkBlue = "rgb(0,48,60)"
TT_Grey = "rgb(99,102,105)"
TT_LightLightBlue = "rgb(207,241,242)"
TT_LightGrey = "rgb(223,224,225)"

def get_qp_at_height(z_height, building_height, building_width, qp_max):
    """Calculate q_p at a given height based on building dimensions.
    Conservative approach: Using the same calculation for all height scenarios."""
    # Conservative approach - use h <= b calculation for all cases
    return qp_max

def get_qp_less_conservative(z_height, building_height, building_width, qp_max):
    """Calculate q_p at a given height based on building dimensions using 
    the less conservative approach from BS EN 1991-1-4."""
    h = building_height
    b = building_width
    
    if h <= b:
        # Case 1: Constant pressure across entire height
        return qp_max
    
    elif b < h <= 2*b:
        # Case 2: Two pressure zones
        if z_height <= b:
            return qp_max * (b / h)  # q_p(b)
        else:
            return qp_max  # q_p(h)
    
    else:  # h > 2*b
        # Case 3: Three pressure zones
        if z_height <= b:
            return qp_max * (b / h)  # q_p(b)
        elif b < z_height <= h - b:
            # Calculate z_strip relative position
            z_strip = b + (z_height - b) / (h - 2*b) * b
            # Linear interpolation between q_p(b) and q_p(h)
            return qp_max * (z_strip / h)
        else:  # z_height > h - b
            return qp_max  # q_p(h)

def get_profile_case(h, b):
    """Determine case based on height-to-width ratio."""
    if h <= b:
        return "Case 1: h ≤ b"
    elif b < h <= 2*b:
        return "Case 2: b < h ≤ 2b"
    else:  # h > 2*b
        return "Case 3: h > 2b"

def create_wind_pressure_plot(building_height, building_width, qp_value, direction):
    """Create wind pressure profile plot using Plotly."""
    # Determine the case based on height-to-width ratio
    profile_case = get_profile_case(building_height, building_width)
    
    # Create height points for plotting
    z_points = np.linspace(0, building_height, 100)
    
    # Conservative approach (constant pressure)
    qp_points = [get_qp_at_height(z, building_height, building_width, qp_value) for z in z_points]
    
    # Less conservative approach (for reference)
    qp_points_less_conservative = [get_qp_less_conservative(z, building_height, building_width, qp_value) for z in z_points]
    
    # Create the figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Define max arrow length and reference point
    max_arrow_length = building_width * 1.5
    ref_x = building_width * 1.5
    arrow_scale = max_arrow_length / qp_value if qp_value > 0 else 1
    
    # Create building outline
    fig.add_trace(
        go.Scatter(
            x=[0, building_width, building_width, 0, 0],
            y=[0, 0, building_height, building_height, 0],
            fill='toself',
            fillcolor=TT_LightGrey,
            line=dict(color=TT_DarkBlue, width=2),
            name='Building'
        )
    )
    
    # Draw pressure profile curve (conservative approach)
    fig.add_trace(
        go.Scatter(
            x=[ref_x + qp * arrow_scale for qp in qp_points],
            y=z_points,
            line=dict(color=TT_MidBlue, width=3),
            name='Conservative Pressure Profile'
        )
    )
    
    # Add less conservative profile curve if applicable (h > b)
    if building_height > building_width:
        fig.add_trace(
            go.Scatter(
                x=[ref_x + qp * arrow_scale for qp in qp_points_less_conservative],
                y=z_points,
                line=dict(color=TT_Grey, width=2, dash='dash'),
                name='Less Conservative Profile (BS EN 1991-1-4)'
            )
        )
    
    # Draw arrows at different heights
    num_arrows = 15
    arrow_heights = np.linspace(0.1*building_height, 0.9*building_height, num_arrows)
    
    for i, z_height in enumerate(arrow_heights):
        qp_at_z = get_qp_at_height(z_height, building_height, building_width, qp_value)
        arrow_length = qp_at_z * arrow_scale
        
        # Draw arrow line
        fig.add_trace(
            go.Scatter(
                x=[ref_x, ref_x + arrow_length],
                y=[z_height, z_height],
                line=dict(color=TT_Orange, width=1),
                showlegend=False
            )
        )
        
        # Draw arrow head (triangle)
        head_size = 0.02 * building_height
        if i % 3 == 0:  # Add pressure text for every 3rd arrow
            fig.add_annotation(
                x=ref_x + arrow_length + 0.1*building_width,
                y=z_height,
                text=f"{qp_at_z:.2f} N/m²",
                showarrow=False,
                font=dict(size=10),
                xanchor="left"
            )
        
        # Add arrowhead annotation
        fig.add_annotation(
            x=ref_x + arrow_length,
            y=z_height,
            text="",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=2,
            arrowcolor=TT_Orange,
            axref="x",
            ayref="y",
            ax=ref_x + arrow_length - 0.05*building_width,
            ay=z_height
        )
    
    # Add reference height lines
    if building_height <= building_width:
        # Case 1: Only mark h
        fig.add_shape(
            type="line",
            x0=0, y0=building_height, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_height,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_annotation(
            x=0, y=building_height,
            text=f"zₑ = h = {building_height} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        
    elif building_width < building_height <= 2*building_width:
        # Case 2: Mark b and h
        fig.add_shape(
            type="line",
            x0=0, y0=building_width, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_width,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_shape(
            type="line",
            x0=0, y0=building_height, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_height,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_annotation(
            x=0, y=building_width,
            text=f"zₑ = b = {building_width} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        fig.add_annotation(
            x=0, y=building_height,
            text=f"zₑ = h = {building_height} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        
        # Add rectangle for upper zone (for reference only)
        fig.add_shape(
            type="rect",
            x0=0, y0=building_width,
            x1=building_width, y1=building_height,
            fillcolor=TT_LightLightBlue,
            opacity=0.2,
            line=dict(width=0)
        )
        
    else:  # h > 2*b
        # Case 3: Mark b, h-b, and h
        z_strip = building_height - building_width
        fig.add_shape(
            type="line",
            x0=0, y0=building_width, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_width,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_shape(
            type="line",
            x0=0, y0=z_strip, 
            x1=ref_x + max_arrow_length * 1.2, y1=z_strip,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_shape(
            type="line",
            x0=0, y0=building_height, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_height,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_annotation(
            x=0, y=building_width,
            text=f"zₑ = b = {building_width} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        fig.add_annotation(
            x=0, y=z_strip,
            text=f"zₑ = z_strip = {z_strip:.1f} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        fig.add_annotation(
            x=0, y=building_height,
            text=f"zₑ = h = {building_height} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        
        # Add rectangle for middle zone (for reference only)
        fig.add_shape(
            type="rect",
            x0=0, y0=building_width,
            x1=building_width, y1=z_strip,
            fillcolor=TT_LightLightBlue,
            opacity=0.2,
            line=dict(width=0)
        )
        
        # Add rectangle for upper zone (for reference only)
        fig.add_shape(
            type="rect",
            x0=0, y0=z_strip,
            x1=building_width, y1=building_height,
            fillcolor=TT_LightBlue,
            opacity=0.2,
            line=dict(width=0)
        )
    
    # Update layout
    fig.update_layout(
        title=f'Wind Pressure Profile - {direction} Direction - {profile_case}',
        xaxis_title='Distance [m]',
        yaxis_title='Height [m]',
        template='plotly_white',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    # Set axes limits
    fig.update_xaxes(range=[-0.5*building_width, ref_x + max_arrow_length * 1.2])
    fig.update_yaxes(range=[-0.1*building_height, 1.1*building_height])
    
    return fig, profile_case

def create_pressure_table(building_height, building_width, qp_value):
    """Create a dataframe with pressure values at key heights for display in Streamlit."""
    key_heights = []
    if building_height <= building_width:
        key_heights = [("Ground level", 0), (f"Top (h = {building_height} m)", building_height)]
    elif building_width < building_height <= 2*building_width:
        key_heights = [("Ground level", 0), (f"Width level (b = {building_width} m)", building_width), (f"Top (h = {building_height} m)", building_height)]
    else:  # h > 2*b
        key_heights = [
            ("Ground level", 0), 
            (f"Lower zone (b = {building_width} m)", building_width),
            (f"Middle zone (z_strip = {building_height-building_width:.1f} m)", building_height-building_width),
            (f"Top (h = {building_height} m)", building_height)
        ]

    # Create the table data - using conservative approach
    data = []
    for label, z_height in key_heights:
        # Apply the same pressure for all heights in conservative approach
        # Ground level has the same pressure as the building top
        qp_at_z = get_qp_at_height(z_height, building_height, building_width, qp_value)
        data.append([label, f"{z_height:.2f}", f"{qp_at_z:.2f}"])
            
    df = pd.DataFrame(data, columns=["Position", "Height (m)", "$q_p(z)$ (N/m²)"])
    
    # Add information about less conservative approach if applicable
    import streamlit as st
    if building_height > building_width:
        if building_width < building_height <= 2*building_width:
            st.write("*Note: A less conservative approach is outlined in BS EN 1991-1-4 for a two part model.*")
        else:  # h > 2*b
            st.write("*Note: A less conservative approach is outlined in BS EN 1991-1-4 for a multiple parts model.*")
    
    return df

def calculate_design_pressure(building_height, building_width, qp_value):
    """Calculate design pressure based on building dimensions.
    Using conservative approach for all cases."""
    # Conservative approach - use the qp_value directly for all cases
    design_pressure = qp_value
    return design_pressure

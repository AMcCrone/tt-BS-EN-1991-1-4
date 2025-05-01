import numpy as np
import plotly.graph_objects as go
import math

# Define color palette
TT_LightBlue = "rgba(136,219,223,0.4)"  # Light blue with transparency
TT_DarkBlue = "rgb(0,48,60)"  # Dark blue for labels

def create_cdir_radial_plot(height=400, width=400):
    """
    Create a simple radial plot of c_dir values.
    
    Parameters:
    -----------
    height : int
        Height of the plot in pixels
    width : int
        Width of the plot in pixels
    
    Returns:
    --------
    plotly.graph_objects.Figure
        A radial plot showing c_dir values
    """
    # UK directional factors
    uk_dir_factors = {
        0: 0.78,    # North
        30: 0.73,
        60: 0.73,
        90: 0.74,   # East
        120: 0.73,
        150: 0.80,
        180: 0.85,  # South
        210: 0.93,
        240: 1.00,  # Maximum value
        270: 0.99,  # West
        300: 0.91,
        330: 0.82
    }
    
    # Create the figure
    fig = go.Figure()
    
    # Get the directions and values
    directions = list(uk_dir_factors.keys())
    r_values = list(uk_dir_factors.values())
    
    # Convert angles to match North at top (0 = North, clockwise)
    # and adjust for Plotly's polar coordinates (0 = East, counterclockwise)
    plot_angles = [(270 - angle) % 360 for angle in directions]
    plot_angles_rad = [math.radians(angle) for angle in plot_angles]
    
    # Scale factor for the plot
    scale = 5
    
    # Calculate x and y coordinates for the radar chart
    radar_x = [scale * r * math.cos(theta) for r, theta in zip(r_values, plot_angles_rad)]
    radar_y = [scale * r * math.sin(theta) for r, theta in zip(r_values, plot_angles_rad)]
    
    # Close the loop by adding the first point again
    radar_x.append(radar_x[0])
    radar_y.append(radar_y[0])
    
    # Add the radial plot
    fig.add_trace(go.Scatter(
        x=radar_x,
        y=radar_y,
        mode='lines',
        line=dict(color=TT_DarkBlue, width=2),
        fill='toself',
        fillcolor=TT_LightBlue,
        showlegend=False
    ))
    
    # Add c_dir value annotations
    for angle, value in uk_dir_factors.items():
        # Convert to plotting coordinates
        plot_angle = math.radians((270 - angle) % 360)
        x = scale * value * math.cos(plot_angle)
        y = scale * value * math.sin(plot_angle)
        
        # Add annotation
        fig.add_annotation(
            x=x,
            y=y,
            text=f"{value:.2f}",
            showarrow=False,
            font=dict(size=10, color=TT_DarkBlue)
        )
    
    # Add cardinal directions at the edges
    max_dim = scale * 1.1
    cardinals = [
        {"dir": "N", "x": 0, "y": max_dim},
        {"dir": "E", "x": max_dim, "y": 0},
        {"dir": "S", "x": 0, "y": -max_dim},
        {"dir": "W", "x": -max_dim, "y": 0}
    ]
    
    for cardinal in cardinals:
        fig.add_annotation(
            x=cardinal["x"],
            y=cardinal["y"],
            text=cardinal["dir"],
            showarrow=False,
            font=dict(size=12, color=TT_DarkBlue, weight="bold")
        )
    
    # Set layout with equal aspect ratio
    fig.update_layout(
        showlegend=False,
        xaxis=dict(
            range=[-max_dim, max_dim],
            zeroline=False,
            showgrid=False,
            showticklabels=False
        ),
        yaxis=dict(
            range=[-max_dim, max_dim],
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        plot_bgcolor='white',
        height=height,
        width=width,
        margin=dict(l=10, r=10, t=10, b=10),
        autosize=False
    )
    
    return fig

# For direct use in Streamlit
def create_direction_viz(rotation_angle=None, NS_dimension=None, EW_dimension=None, height=400, width=400):
    """
    Wrapper function that maintains compatibility with the existing code
    but ignores the building parameters and just returns the c_dir plot.
    
    Parameters:
    -----------
    rotation_angle : int or None
        Building rotation angle (not used in this version)
    NS_dimension : float or None
        North-South dimension (not used in this version)
    EW_dimension : float or None
        East-West dimension (not used in this version)
    height : int
        Height of the plot in pixels
    width : int
        Width of the plot in pixels
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A radial plot showing c_dir values
    """
    return create_cdir_radial_plot(height=height, width=width)

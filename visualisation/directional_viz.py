import numpy as np
import plotly.graph_objects as go
import math

# Define color palette
TT_LightBlue = "rgba(136,219,223,0.5)"  # Light blue with transparency
TT_DarkBlue = "rgb(0,48,60)"  # Dark blue for labels
TT_Orange = "rgb(211,69,29)"  # Orange for the 1.0 line

def create_cdir_radial_plot(height=400, width=400):
    """
    Create a radial plot of c_dir values with concentric circles.
    
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
        0: 0.78,    # North (top)
        30: 0.73,   # NE
        60: 0.73,   # ENE
        90: 0.74,   # East (right)
        120: 0.73,  # ESE
        150: 0.80,  # SE
        180: 0.85,  # South (bottom)
        210: 0.93,  # SW
        240: 1.00,  # WSW (max value)
        270: 0.99,  # West (left)
        300: 0.91,  # WNW
        330: 0.82   # NW
    }
    
    # Create the figure
    fig = go.Figure()
    
    # Get the directions and values
    directions = list(uk_dir_factors.keys())
    r_values = list(uk_dir_factors.values())
    
    # Scale factor for the plot
    scale = 5
    max_dim = scale * 1.1
    
    # Draw concentric circles at 0.1 intervals
    for radius in np.arange(0.1, 1.0, 0.1):
        # Create a circle at this radius
        theta = np.linspace(0, 2*np.pi, 100)
        x = scale * radius * np.cos(theta)
        y = scale * radius * np.sin(theta)
        
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines',
            line=dict(color=TT_LightBlue, width=1),
            showlegend=False
        ))
        
        # Add subtle radius label
        fig.add_annotation(
            x=0,
            y=scale * radius,
            text=f"{radius:.1f}",
            showarrow=False,
            font=dict(size=8, color=TT_LightBlue),
            yshift=8
        )
    
    # Add special circle for 1.0 (maximum value)
    theta = np.linspace(0, 2*np.pi, 100)
    x = scale * np.cos(theta)
    y = scale * np.sin(theta)
    
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        line=dict(color=TT_Orange, width=1.5, dash='dash'),
        showlegend=False
    ))
    
    # Add 1.0 radius label
    fig.add_annotation(
        x=0,
        y=scale,
        text="1.0",
        showarrow=False,
        font=dict(size=10, color=TT_Orange),
        yshift=8
    )
    
    # Convert angles to match top=0, clockwise direction
    # In this system: top=0°, right=90°, bottom=180°, left=270°
    plot_angles_rad = [math.radians(angle) for angle in directions]
    
    # Calculate x and y coordinates for the plot points
    # For clockwise from top: x=r*sin(θ), y=r*cos(θ)
    points_x = [scale * r * math.sin(theta) for r, theta in zip(r_values, plot_angles_rad)]
    points_y = [scale * r * math.cos(theta) for r, theta in zip(r_values, plot_angles_rad)]
    
    # Close the loop by adding the first point again
    points_x.append(points_x[0])
    points_y.append(points_y[0])
    
    # Add the c_dir plot line
    fig.add_trace(go.Scatter(
        x=points_x,
        y=points_y,
        mode='lines',
        line=dict(color=TT_DarkBlue, width=2),
        showlegend=False
    ))
    
    # Add c_dir value annotations
    for angle, value in uk_dir_factors.items():
        # Convert to plotting coordinates (clockwise from top)
        angle_rad = math.radians(angle)
        x = scale * value * math.sin(angle_rad)
        y = scale * value * math.cos(angle_rad)
        
        # Add annotation with slight offset
        offset_factor = 1.05  # Small offset for readability
        fig.add_annotation(
            x=x * offset_factor,
            y=y * offset_factor,
            text=f"{value:.2f}",
            showarrow=False,
            font=dict(size=10, color=TT_DarkBlue)
        )
    
    # Add cardinal directions at the edges
    cardinals = [
        {"dir": "N", "angle": 0, "x": 0, "y": max_dim},
        {"dir": "E", "angle": 90, "x": max_dim, "y": 0},
        {"dir": "S", "angle": 180, "x": 0, "y": -max_dim},
        {"dir": "W", "angle": 270, "x": -max_dim, "y": 0}
    ]
    
    for cardinal in cardinals:
        fig.add_annotation(
            x=cardinal["x"],
            y=cardinal["y"],
            text=cardinal["dir"],
            showarrow=False,
            font=dict(size=12, color=TT_DarkBlue, weight="bold")
        )
    
    # Add radial lines at 30° intervals
    for angle in range(0, 360, 30):
        angle_rad = math.radians(angle)
        line_x = [0, scale * math.sin(angle_rad)]
        line_y = [0, scale * math.cos(angle_rad)]
        
        fig.add_trace(go.Scatter(
            x=line_x,
            y=line_y,
            mode='lines',
            line=dict(color="rgba(99,102,105,0.3)", width=1),
            showlegend=False
        ))
    
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

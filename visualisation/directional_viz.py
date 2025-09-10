import numpy as np
import plotly.graph_objects as go
import math

# Define color palette
TT_LightBlue = "rgba(136,219,223,0.5)"  # Light blue with transparency
TT_DarkBlue = "rgb(0,48,60)"  # Dark blue for labels
TT_Orange = "rgb(211,69,29)"  # Orange for the 1.0 line
TT_Building = "rgba(100,100,100,0.7)"  # Building color
TT_BuildingOutline = "rgb(60,60,60)"  # Building outline

def create_cdir_radial_plot(height=400, width=400, rotation_angle=0, NS_dimension=1.0, EW_dimension=1.0):
    """
    Create a radial plot of c_dir values with concentric circles and building footprint.
    
    Parameters:
    -----------
    height : int
        Height of the plot in pixels
    width : int
        Width of the plot in pixels
    rotation_angle : float
        Building rotation angle in degrees (clockwise from north)
    NS_dimension : float
        North-South dimension of the building (width in east-west direction)
    EW_dimension : float
        East-West dimension of the building (height in north-south direction)
    
    Returns:
    --------
    plotly.graph_objects.Figure
        A radial plot showing c_dir values with building footprint
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
    
    # Calculate nearest 30° increment for rotation
    rotation_increment = round(rotation_angle / 30) * 30
    
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
            showlegend=False,
            hoverinfo='skip'
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
        showlegend=False,
        hoverinfo='skip'
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
    plot_angles_rad = [math.radians(angle) for angle in directions]
    
    # Calculate x and y coordinates for the plot points
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
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add c_dir value annotations
    for angle, value in uk_dir_factors.items():
        # Convert to plotting coordinates (clockwise from top)
        angle_rad = math.radians(angle)
        x = scale * value * math.sin(angle_rad)
        y = scale * value * math.cos(angle_rad)
        
        # Add annotation with slight offset
        offset_factor = 1.05
        fig.add_annotation(
            x=x * offset_factor,
            y=y * offset_factor,
            text=f"{value:.2f}",
            showarrow=False,
            font=dict(size=10, color=TT_DarkBlue)
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
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Add building footprint in center
    if NS_dimension and EW_dimension:
        # Scale building to be smaller than the radial chart (max ~30% of radius)
        max_building_dim = scale * 0.6  # Maximum building dimension
        building_scale = min(max_building_dim / max(NS_dimension, EW_dimension), 1.0)
        
        scaled_NS = NS_dimension * building_scale
        scaled_EW = EW_dimension * building_scale
        
        # Create building rectangle corners (before rotation)
        # NS_dimension is width (east-west), EW_dimension is height (north-south)
        corners = [
            [-scaled_NS/2, -scaled_EW/2],  # Bottom-left
            [scaled_NS/2, -scaled_EW/2],   # Bottom-right
            [scaled_NS/2, scaled_EW/2],    # Top-right
            [-scaled_NS/2, scaled_EW/2],   # Top-left
            [-scaled_NS/2, -scaled_EW/2]   # Close the shape
        ]
        
        # Rotate building corners (clockwise rotation)
        rotation_rad = math.radians(-rotation_angle)  # Negative for clockwise
        cos_rot = math.cos(rotation_rad)
        sin_rot = math.sin(rotation_rad)
        
        rotated_corners = []
        for x, y in corners:
            rotated_x = x * cos_rot - y * sin_rot
            rotated_y = x * sin_rot + y * cos_rot
            rotated_corners.append([rotated_x, rotated_y])
        
        building_x = [corner[0] for corner in rotated_corners]
        building_y = [corner[1] for corner in rotated_corners]
        
        # Add building footprint
        fig.add_trace(go.Scatter(
            x=building_x,
            y=building_y,
            mode='lines',
            fill='toself',
            fillcolor=TT_Building,
            line=dict(color=TT_BuildingOutline, width=2),
            showlegend=False,
            hovertemplate=f"Building<br>Rotation: {rotation_angle}°<br>NS: {NS_dimension:.1f}<br>EW: {EW_dimension:.1f}<extra></extra>"
        ))
    
    # Add main cardinal directions (N, E, S, W) - these are the global wind directions
    # These stay fixed and are shown in light gray
    fixed_cardinals = [
        {"dir": "N", "angle": 0},
        {"dir": "E", "angle": 90}, 
        {"dir": "S", "angle": 180},
        {"dir": "W", "angle": 270}
    ]
    
    for cardinal in fixed_cardinals:
        angle_rad = math.radians(cardinal["angle"])
        x = max_dim * math.sin(angle_rad)
        y = max_dim * math.cos(angle_rad)
        
        fig.add_annotation(
            x=x,
            y=y,
            text=cardinal["dir"],
            showarrow=False,
            font=dict(size=12, color="rgba(0,48,60,0.4)", weight="normal")
        )
    
    # Add building-specific NE-SW axes labels on the building faces
    # These are positioned near the building edges and rotate with the building
    if NS_dimension and EW_dimension:
        # Calculate the building edge positions (10% offset from face centers)
        edge_offset = 1.1  # 10% beyond the building edge
        
        # Building NE-SW axis labels
        building_axes = [
            {"dir": "NE", "corner_offset": [1, 1]},   # Northeast corner direction
            {"dir": "SW", "corner_offset": [-1, -1]}  # Southwest corner direction
        ]
        
        for axis in building_axes:
            # Calculate position based on building dimensions and rotation
            base_x = (scaled_NS/2) * axis["corner_offset"][0] * edge_offset
            base_y = (scaled_EW/2) * axis["corner_offset"][1] * edge_offset
            
            # Apply building rotation
            rotation_rad = math.radians(-rotation_angle)
            cos_rot = math.cos(rotation_rad)
            sin_rot = math.sin(rotation_rad)
            
            x = base_x * cos_rot - base_y * sin_rot
            y = base_x * sin_rot + base_y * cos_rot
            
            fig.add_annotation(
                x=x,
                y=y,
                text=axis["dir"],
                showarrow=False,
                font=dict(size=10, color=TT_DarkBlue, weight="bold")
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

# Updated wrapper function
def create_direction_viz(rotation_angle=0, NS_dimension=1.0, EW_dimension=1.0, height=400, width=400):
    """
    Create a directional wind visualization with building footprint.
    
    Parameters:
    -----------
    rotation_angle : float
        Building rotation angle in degrees (clockwise from north)
    NS_dimension : float
        North-South dimension of the building (width in east-west direction)
    EW_dimension : float
        East-West dimension of the building (height in north-south direction)
    height : int
        Height of the plot in pixels
    width : int
        Width of the plot in pixels
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A radial plot showing c_dir values with building footprint
    """
    return create_cdir_radial_plot(
        height=height, 
        width=width, 
        rotation_angle=rotation_angle or 0,
        NS_dimension=NS_dimension or 1.0,
        EW_dimension=EW_dimension or 1.0
    )

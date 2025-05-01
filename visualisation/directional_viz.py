import numpy as np
import plotly.graph_objects as go
import math

# Define color palette
TT_Orange = "rgb(211,69,29)"
TT_Blue = "rgb(0,163,173)"
TT_DarkBlue = "rgb(0,48,60)"
TT_Grey = "rgb(99,102,105)"
TT_LightGrey = "rgb(223,224,225)"

def create_simplified_direction_viz(rotation_angle=0, NS_dimension=20.0, EW_dimension=40.0):
    """
    Create a simplified visualization showing the building orientation and directional factors.
    
    Parameters:
    -----------
    rotation_angle : int
        Building rotation angle in degrees clockwise from north
    NS_dimension : float
        North-South dimension of the building (m)
    EW_dimension : float
        East-West dimension of the building (m)
    
    Returns:
    --------
    plotly.graph_objects.Figure
        Figure showing the building orientation and directional factors
    """
    # Create the figure
    fig = go.Figure()
    
    # UK directional factors
    uk_dir_factors = {
        0: 0.78,
        30: 0.73,
        60: 0.73,
        90: 0.74,
        120: 0.73,
        150: 0.80,
        180: 0.85,
        210: 0.93,
        240: 1.00,
        270: 0.99,
        300: 0.91,
        330: 0.82
    }
    
    # Get max c_dir value for scaling
    max_c_dir = max(uk_dir_factors.values())
    plot_scale = 5  # Base scale for the plot
    
    # Calculate the maximum dimension for plot scaling
    # Make sure building fits inside the c_dir plot
    max_building_dim = max(NS_dimension, EW_dimension)
    max_dimension = plot_scale * max_c_dir
    
    # Scale building to fit inside c_dir plot
    building_scale = 0.65 * max_dimension / max_building_dim
    NS_dimension *= building_scale
    EW_dimension *= building_scale
    
    # Calculate building corners based on rotation
    half_ns = NS_dimension / 2
    half_ew = EW_dimension / 2
    
    # Building corners in local coordinates (clockwise from bottom-left)
    local_corners = [
        [-half_ew, -half_ns],  # Bottom-left
        [half_ew, -half_ns],   # Bottom-right
        [half_ew, half_ns],    # Top-right
        [-half_ew, half_ns]    # Top-left
    ]
    
    # Convert rotation angle to radians
    theta = math.radians(rotation_angle)
    
    # Rotation matrix
    rotation_matrix = [
        [math.cos(theta), -math.sin(theta)],
        [math.sin(theta), math.cos(theta)]
    ]
    
    # Rotate building corners to global coordinates
    rotated_corners = []
    for x, y in local_corners:
        # Apply rotation matrix
        x_rot = rotation_matrix[0][0] * x + rotation_matrix[0][1] * y
        y_rot = rotation_matrix[1][0] * x + rotation_matrix[1][1] * y
        rotated_corners.append([x_rot, y_rot])
    
    # Extract x and y coordinates of rotated corners
    x_corners = [corner[0] for corner in rotated_corners] + [rotated_corners[0][0]]  # Close the polygon
    y_corners = [corner[1] for corner in rotated_corners] + [rotated_corners[0][1]]  # Close the polygon
    
    # Create radial plot for c_dir values
    angles = np.linspace(0, 2*np.pi, 13)[:-1]  # Every 30 degrees, excluding duplicate at 360
    directions = list(uk_dir_factors.keys())
    r_values = list(uk_dir_factors.values())
    
    # Convert angles to match North at top (0 = North, clockwise)
    # and adjust for Plotly's polar coordinates (0 = East, counterclockwise)
    plot_angles = [(270 - a) % 360 for a in directions]
    plot_angles_rad = [math.radians(a) for a in plot_angles]
    
    # Calculate x and y coordinates for the radar chart
    radar_x = [plot_scale * r * math.cos(theta) for r, theta in zip(r_values, plot_angles_rad)]
    radar_y = [plot_scale * r * math.sin(theta) for r, theta in zip(r_values, plot_angles_rad)]
    
    # Close the loop by adding the first point again
    radar_x.append(radar_x[0])
    radar_y.append(radar_y[0])
    
    # Add radar chart for directional factors
    fig.add_trace(go.Scatter(
        x=radar_x,
        y=radar_y,
        mode='lines',
        line=dict(color=TT_Blue, width=3),
        fill='toself',
        fillcolor=TT_Blue,
        opacity=0.4,
        showlegend=False
    ))
    
    # Draw building outline
    fig.add_trace(go.Scatter(
        x=x_corners,
        y=y_corners,
        mode='lines',
        line=dict(color=TT_DarkBlue, width=2),
        fill='toself',
        fillcolor='rgba(0,0,0,0)',
        showlegend=False
    ))
    
    # Get the directional factors based on the rotation
    # Calculate c_dir for each elevation based on the building rotation
    directions = ["North", "East", "South", "West"]
    elevations_c_dir = {}
    
    for i, direction in enumerate(directions):
        # Calculate the global angle for this elevation
        base_angles = {"North": 0, "East": 90, "South": 180, "West": 270}
        global_angle = (base_angles[direction] + rotation_angle) % 360
        
        # Find the closest direction in the UK factors table
        closest_dir = min(uk_dir_factors.keys(), key=lambda x: min(abs(x - global_angle), abs((x + 360) - global_angle), abs(x - (global_angle + 360))))
        elevations_c_dir[direction] = uk_dir_factors[closest_dir]
    
    # Add simplified elevation labels to the building with c_dir values
    rotated_corners_with_first = rotated_corners + [rotated_corners[0]]
    face_labels = ["N", "E", "S", "W"]
    face_directions = ["North", "East", "South", "West"]
    
    for i in range(4):
        # Calculate midpoint of this face
        mid_x = (rotated_corners[i][0] + rotated_corners[(i+1)%4][0]) / 2
        mid_y = (rotated_corners[i][1] + rotated_corners[(i+1)%4][1]) / 2
        
        # Determine which cardinal direction this face corresponds to after rotation
        # At 0° rotation: Face 0 (bottom) = S, Face 1 (right) = E, Face 2 (top) = N, Face 3 (left) = W
        face_idx = (2 - i + rotation_angle // 90) % 4
        label = face_labels[face_idx]
        direction = face_directions[face_idx]
        
        # Get the c_dir value for this face
        c_dir = elevations_c_dir[direction]
        
        # Add the label with c_dir value
        fig.add_annotation(
            x=mid_x,
            y=mid_y,
            text=f"{label}\n{c_dir:.2f}",
            showarrow=False,
            font=dict(size=12, color=TT_DarkBlue)
        )
    
    # Add the maximum c_dir value annotation
    max_dir = max(uk_dir_factors, key=uk_dir_factors.get)
    max_value = uk_dir_factors[max_dir]
    max_angle_rad = math.radians((270 - max_dir) % 360)
    max_x = plot_scale * max_value * math.cos(max_angle_rad)
    max_y = plot_scale * max_value * math.sin(max_angle_rad)
    
    fig.add_annotation(
        x=max_x,
        y=max_y,
        text=f"{max_value:.1f}",
        showarrow=False,
        font=dict(size=14, color=TT_Orange)
    )
    
    # Set layout with equal aspect ratio and square dimensions
    fig.update_layout(
        showlegend=False,
        xaxis=dict(
            range=[-max_dimension*1.1, max_dimension*1.1],
            zeroline=False,
            showgrid=False,
            showticklabels=False
        ),
        yaxis=dict(
            range=[-max_dimension*1.1, max_dimension*1.1],
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        plot_bgcolor='white',
        height=500,
        width=500,
        margin=dict(l=20, r=20, t=20, b=20),
        autosize=False
    )
    
    # Add cardinal direction markers at the edges
    cardinal_markers = [
        {"dir": "N", "angle": 0, "x": 0, "y": max_dimension*1.15},
        {"dir": "E", "angle": 90, "x": max_dimension*1.15, "y": 0},
        {"dir": "S", "angle": 180, "x": 0, "y": -max_dimension*1.15},
        {"dir": "W", "angle": 270, "x": -max_dimension*1.15, "y": 0}
    ]
    
    for marker in cardinal_markers:
        fig.add_annotation(
            x=marker["x"],
            y=marker["y"],
            text=marker["dir"],
            showarrow=False,
            font=dict(size=14, color=TT_Grey)
        )
    
    return fig

def create_direction_viz(rotation_angle, NS_dimension, EW_dimension):
    """
    Wrapper function to match the expected interface in the main application
    """
    return create_simplified_direction_viz(rotation_angle, NS_dimension, EW_dimension)

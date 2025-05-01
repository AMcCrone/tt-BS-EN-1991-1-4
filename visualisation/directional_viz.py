import numpy as np
import pandas as pd
import plotly.graph_objects as go
import math

# Define color palette
TT_Orange = "rgb(211,69,29)"
TT_LightBlue = "rgb(136,219,223)"
TT_MidBlue = "rgb(0,163,173)"
TT_DarkBlue = "rgb(0,48,60)"
TT_Grey = "rgb(99,102,105)"
TT_LightLightBlue = "rgb(207,241,242)"
TT_LightGrey = "rgb(223,224,225)"

def create_direction_viz(rotation_angle, direction_factors, NS_dimension, EW_dimension):
    """
    Create a visualization showing the building orientation and directional factors.
    
    Parameters:
    -----------
    rotation_angle : int
        Building rotation angle in degrees clockwise from north
    direction_factors : dict
        Dictionary mapping cardinal directions to c_dir values
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
    
    # Calculate the maximum dimension for plot scaling
    max_dimension = max(NS_dimension, EW_dimension) * 1.5
    
    # Calculate building corners based on rotation
    # In the building's local coordinates, NS is along y-axis, EW is along x-axis
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
    
    # Draw building outline
    fig.add_trace(go.Scatter(
        x=x_corners,
        y=y_corners,
        mode='lines',
        line=dict(color=TT_MidBlue, width=3),
        fill='toself',
        fillcolor=TT_LightBlue,
        opacity=0.7,
        name='Building'
    ))
    
    # Add building center point
    fig.add_trace(go.Scatter(
        x=[0],
        y=[0],
        mode='markers',
        marker=dict(color=TT_DarkBlue, size=8),
        name='Building Center'
    ))
    
    # Add local coordinate indicators for each face
    face_centers = []
    face_labels = []
    face_directions = []
    
    # Calculate midpoints of each face
    for i in range(4):
        mid_x = (rotated_corners[i][0] + rotated_corners[(i+1)%4][0]) / 2
        mid_y = (rotated_corners[i][0] + rotated_corners[(i+1)%4][0]) / 2
        face_centers.append([mid_x, mid_y])
    
    # Assign directions based on rotation
    # At 0° rotation:
    # Face 0 (bottom) = South
    # Face 1 (right) = West
    # Face 2 (top) = North
    # Face 3 (left) = East
    
    # Map index to direction based on rotation
    face_mapping = ["South", "West", "North", "East"]
    
    # Adjust face midpoints slightly outward for label placement
    label_positions = []
    for i in range(4):
        # Calculate normal vector pointing outward (perpendicular to the face)
        next_idx = (i+1) % 4
        edge_x = rotated_corners[next_idx][0] - rotated_corners[i][0]
        edge_y = rotated_corners[next_idx][1] - rotated_corners[i][1]
        
        # Perpendicular vector
        normal_x = -edge_y
        normal_y = edge_x
        
        # Normalize
        length = (normal_x**2 + normal_y**2)**0.5
        if length > 0:
            normal_x /= length
            normal_y /= length
        
        # Calculate midpoint
        mid_x = (rotated_corners[i][0] + rotated_corners[next_idx][0]) / 2
        mid_y = (rotated_corners[i][1] + rotated_corners[next_idx][1]) / 2
        
        # Adjust outward by 10% of max dimension
        offset = max_dimension * 0.07
        label_x = mid_x + normal_x * offset
        label_y = mid_y + normal_y * offset
        
        # Map to appropriate elevation name based on orientation
        # The face_mapping needs to rotate with the building
        direction_idx = (i - rotation_angle // 90) % 4
        direction = face_mapping[direction_idx]
        
        label_positions.append([label_x, label_y, direction])
    
    # Add elevation labels
    for pos in label_positions:
        fig.add_annotation(
            x=pos[0],
            y=pos[1],
            text=f"{pos[2]} Elevation",
            showarrow=False,
            font=dict(size=12, color=TT_DarkBlue),
            bgcolor=TT_LightLightBlue,
            bordercolor=TT_MidBlue,
            borderwidth=1,
            borderpad=4
        )
    
    # Draw the cardinal directions (fixed to global coordinates)
    arrow_length = max_dimension * 0.35
    
    # Create cardinal direction arrows at some distance from origin
    cardinals = {
        "N": [0, arrow_length],
        "E": [arrow_length, 0],
        "S": [0, -arrow_length],
        "W": [-arrow_length, 0]
    }
    
    # Add cardinal direction arrows
    for direction, (x, y) in cardinals.items():
        # Arrow line
        fig.add_trace(go.Scatter(
            x=[0, x],
            y=[0, y],
            mode='lines',
            line=dict(color=TT_Grey, width=1),
            name=f'{direction} Direction',
            showlegend=False
        ))
        
        # Direction label
        fig.add_annotation(
            x=x*1.1,
            y=y*1.1,
            text=direction,
            showarrow=False,
            font=dict(size=14, color=TT_Grey)
        )
    
    # Plot the directional factors as a radar chart (star shape)
    angles = np.linspace(0, 2*np.pi, 13)[:-1]  # Every 30 degrees, excluding duplicate at 360
    directions = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
    
    # Get directional factors in the correct order
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
    
    # Get the values
    r_values = [uk_dir_factors[angle] for angle in directions]
    
    # Convert angles to match meteorological convention (0 = North, clockwise)
    # and adjust for Plotly's polar coordinates (0 = East, counterclockwise)
    plot_angles = [(270 - a) % 360 for a in directions]
    plot_angles_rad = [math.radians(a) for a in plot_angles]
    
    # Calculate x and y coordinates for the radar chart
    radar_scale = max_dimension * 0.25
    radar_x = [radar_scale * r * math.cos(theta) for r, theta in zip(r_values, plot_angles_rad)]
    radar_y = [radar_scale * r * math.sin(theta) for r, theta in zip(r_values, plot_angles_rad)]
    
    # Add first point again to close the loop
    radar_x.append(radar_x[0])
    radar_y.append(radar_y[0])
    
    # Add radar chart for directional factors
    fig.add_trace(go.Scatter(
        x=radar_x,
        y=radar_y,
        mode='lines',
        line=dict(color=TT_Orange, width=2),
        fill='toself',
        fillcolor=TT_Orange,
        opacity=0.5,
        name='Directional Factors (c_dir)'
    ))
    
    # Add reference circle for c_dir = 1.0
    theta = np.linspace(0, 2*np.pi, 100)
    circle_x = radar_scale * np.cos(theta)
    circle_y = radar_scale * np.sin(theta)
    
    fig.add_trace(go.Scatter(
        x=circle_x,
        y=circle_y,
        mode='lines',
        line=dict(color=TT_Grey, width=1, dash='dot'),
        name='c_dir = 1.0',
        showlegend=False
    ))
    
    # Highlight the current direction factors for each building face
    for direction, factor in direction_factors.items():
        # Convert direction name to angle
        dir_angle_map = {"North": 0, "East": 90, "South": 180, "West": 270}
        angle = dir_angle_map.get(direction, 0)
        
        # Apply building rotation to get the global angle
        global_angle = (angle + rotation_angle) % 360
        
        # Convert to radians with correct orientation for plotting
        plot_angle = math.radians((270 - global_angle) % 360)
        
        # Calculate point position
        point_x = radar_scale * factor * math.cos(plot_angle)
        point_y = radar_scale * factor * math.sin(plot_angle)
        
        # Add marker for this face's factor
        fig.add_trace(go.Scatter(
            x=[point_x],
            y=[point_y],
            mode='markers+text',
            marker=dict(color=TT_DarkBlue, size=10, symbol='circle'),
            text=[f"{factor:.2f}"],
            textposition="top center",
            textfont=dict(color=TT_DarkBlue),
            name=f'{direction} (c_dir={factor:.2f})'
        ))
    
    # Add rotation angle indicator
    fig.add_annotation(
        x=0,
        y=max_dimension * 0.45,
        text=f"Rotation: {rotation_angle}° clockwise from North",
        showarrow=False,
        font=dict(size=14, color=TT_DarkBlue, family="Arial"),
        bgcolor=TT_LightGrey,
        bordercolor=TT_MidBlue,
        borderwidth=1,
        borderpad=4
    )
    
    # Set layout with equal aspect ratio
    fig.update_layout(
        title="Building Orientation and Directional Factors",
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.01,
            bgcolor=TT_LightGrey,
            bordercolor=TT_Grey
        ),
        xaxis=dict(
            range=[-max_dimension, max_dimension],
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor=TT_Grey,
            showgrid=True,
            gridcolor=TT_LightGrey,
            tickmode='linear',
            tick0=0,
            dtick=max_dimension/2
        ),
        yaxis=dict(
            range=[-max_dimension, max_dimension],
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor=TT_Grey,
            showgrid=True,
            gridcolor=TT_LightGrey,
            scaleanchor="x",
            scaleratio=1,
            tickmode='linear',
            tick0=0,
            dtick=max_dimension/2
        ),
        plot_bgcolor='white',
        height=600,
        width=600,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Add N, E, S, W ticks on the axes
    fig.update_xaxes(
        tickvals=[-max_dimension, 0, max_dimension],
        ticktext=["W", "0", "E"]
    )
    
    fig.update_yaxes(
        tickvals=[-max_dimension, 0, max_dimension],
        ticktext=["S", "0", "N"]
    )
    
    return fig

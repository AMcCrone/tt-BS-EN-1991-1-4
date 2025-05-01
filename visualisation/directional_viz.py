import numpy as np
import plotly.graph_objects as go
import math

# Define color palette
TT_Orange = "rgb(211,69,29)"
TT_Blue = "rgb(0,163,173)"
TT_DarkBlue = "rgb(0,48,60)"
TT_Grey = "rgb(99,102,105)"
TT_LightGrey = "rgb(223,224,225)"

def create_direction_viz(rotation_angle=0, NS_dimension=4, EW_dimension=2):
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
    
    # Convert angles to match meteorological convention (0 = North, clockwise)
    # and adjust for Plotly's polar coordinates (0 = East, counterclockwise)
    plot_angles = [(270 - a) % 360 for a in directions]
    plot_angles_rad = [math.radians(a) for a in plot_angles]
    
    # Calculate x and y coordinates for the radar chart
    radar_x = [plot_scale * r * math.cos(theta) for r, theta in zip(r_values, plot_angles_rad)]
    radar_y = [plot_scale * r * math.sin(theta) for r, theta in zip(r_values, plot_angles_rad)]
    
    # Add first point again to close the loop
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
    
    # Add reference lines at 30-degree intervals
    for angle in range(0, 360, 30):
        rad_angle = math.radians((270 - angle) % 360)
        line_x = [0, max_dimension * math.cos(rad_angle)]
        line_y = [0, max_dimension * math.sin(rad_angle)]
        
        fig.add_trace(go.Scatter(
            x=line_x,
            y=line_y,
            mode='lines',
            line=dict(color='red', width=1),
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
    
    # Add axes
    fig.add_trace(go.Scatter(
        x=[-max_dimension, max_dimension],
        y=[0, 0],
        mode='lines',
        line=dict(color='red', width=2),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[0, 0],
        y=[-max_dimension, max_dimension],
        mode='lines',
        line=dict(color='red', width=2),
        showlegend=False
    ))
    
    # Add key c_dir values as annotations
    # Add annotations for main cardinal directions and max value
    key_directions = {
        0: "N", 
        90: "E", 
        180: "S", 
        270: "W",
        240: "1.0"  # Maximum value
    }
    
    for angle, label in key_directions.items():
        rad_angle = math.radians((270 - angle) % 360)
        
        # Get the c_dir value for this angle
        c_dir = uk_dir_factors.get(angle, 1.0)  # Default to 1.0 for 240 degrees
        
        # Position the label at the edge of the c_dir plot
        pos_x = plot_scale * c_dir * math.cos(rad_angle) * 1.1
        pos_y = plot_scale * c_dir * math.sin(rad_angle) * 1.1
        
        # For cardinal directions, add the label
        if label in ["N", "E", "S", "W"]:
            fig.add_annotation(
                x=pos_x,
                y=pos_y,
                text=label,
                showarrow=False,
                font=dict(size=14, color=TT_DarkBlue)
            )
        else:
            # For the max value point, add the value
            fig.add_annotation(
                x=pos_x,
                y=pos_y,
                text=label,
                showarrow=False,
                font=dict(size=14, color=TT_Orange)
            )
    
    # Add simplified elevation labels to the building
    # Calculate the midpoints of each face and add simplified labels
    rotated_corners_with_first = rotated_corners + [rotated_corners[0]]
    
    # Labels to use based on the building's orientation
    face_labels = ["N", "E", "S", "W"]
    
    for i in range(4):
        # Calculate midpoint of this face
        mid_x = (rotated_corners[i][0] + rotated_corners[(i+1)%4][0]) / 2
        mid_y = (rotated_corners[i][1] + rotated_corners[(i+1)%4][1]) / 2
        
        # Determine which cardinal direction this face corresponds to after rotation
        # At 0° rotation: Face 0 (bottom) = S, Face 1 (right) = E, Face 2 (top) = N, Face 3 (left) = W
        face_idx = (2 - i + rotation_angle // 90) % 4
        label = face_labels[face_idx]
        
        fig.add_annotation(
            x=mid_x,
            y=mid_y,
            text=label,
            showarrow=False,
            font=dict(size=12, color=TT_DarkBlue)
        )
    
    # Add key c_dir values
    key_values = [0.73, 0.74, 0.80, 1.0]
    for value in key_values:
        # Find direction with this value
        for angle, val in uk_dir_factors.items():
            if abs(val - value) < 0.01:
                rad_angle = math.radians((270 - angle) % 360)
                pos_x = plot_scale * val * math.cos(rad_angle)
                pos_y = plot_scale * val * math.sin(rad_angle)
                
                fig.add_annotation(
                    x=pos_x,
                    y=pos_y,
                    text=f"{val:.2f}",
                    showarrow=False,
                    font=dict(size=12, color=TT_DarkBlue)
                )
                break
    
    # Set layout with equal aspect ratio
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
        height=600,
        width=600,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    return fig

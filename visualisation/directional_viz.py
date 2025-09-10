import numpy as np
import plotly.graph_objects as go
import math

# Define color palette
TT_LightBlue = "rgba(136,219,223,0.5)"  # Light blue with transparency
TT_DarkBlue = "rgb(0,48,60)"  # Dark blue for labels
TT_Orange = "rgb(211,69,29)"  # Orange for the 1.0 line
TT_GrayFaint = "rgba(99,102,105,0.35)"

def create_direction_viz(rotation_angle=0, NS_dimension=0.6, EW_dimension=0.4, height=500, width=500):
    """
    Create the radial c_dir plot and overlay a rotated building footprint centered on the plot.

    Parameters
    ----------
    rotation_angle : float
        Building rotation angle, in degrees, clockwise from North (0 = North).
    NS_dimension : float
        North-South dimension (used as the rectangle's horizontal size in the plot coordinate system).
        Expected in same normalized units as the radial values (i.e. 0..1 typically).
    EW_dimension : float
        East-West dimension (used as the rectangle's vertical size in the plot coordinate system).
        Expected in same normalized units as the radial values (i.e. 0..1 typically).
    height, width : int
        Figure size in pixels.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    # UK directional factors (unchanged)
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

    fig = go.Figure()

    # Plot scale: maps r=1 to this plotting radius.
    scale = 5
    max_dim = scale * 1.1

    # Draw concentric circles at 0.1 intervals
    for radius in np.arange(0.1, 1.0, 0.1):
        theta = np.linspace(0, 2*np.pi, 200)
        x = scale * radius * np.cos(theta)
        y = scale * radius * np.sin(theta)
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
                                 line=dict(color=TT_LightBlue, width=1),
                                 showlegend=False))
        fig.add_annotation(x=0, y=scale * radius, text=f"{radius:.1f}",
                           showarrow=False, font=dict(size=8, color=TT_LightBlue), yshift=8)

    # Special circle for 1.0
    theta = np.linspace(0, 2*np.pi, 200)
    x = scale * np.cos(theta)
    y = scale * np.sin(theta)
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
                             line=dict(color=TT_Orange, width=1.5, dash='dash'),
                             showlegend=False))
    fig.add_annotation(x=0, y=scale, text="1.0", showarrow=False,
                       font=dict(size=10, color=TT_Orange), yshift=8)

    # Convert angles to plotting coords where top=0°, clockwise positive
    directions = list(uk_dir_factors.keys())
    r_values = list(uk_dir_factors.values())
    plot_angles_rad = [math.radians(a) for a in directions]

    # Compute c_dir points using x = scale * r * sin(theta), y = scale * r * cos(theta)
    points_x = [scale * r * math.sin(theta) for r, theta in zip(r_values, plot_angles_rad)]
    points_y = [scale * r * math.cos(theta) for r, theta in zip(r_values, plot_angles_rad)]
    # Close loop
    points_x.append(points_x[0])
    points_y.append(points_y[0])

    fig.add_trace(go.Scatter(x=points_x, y=points_y, mode='lines',
                             line=dict(color=TT_DarkBlue, width=2), showlegend=False))

    # Add c_dir value annotations around the curve
    for angle, value in uk_dir_factors.items():
        angle_rad = math.radians(angle)
        x = scale * value * math.sin(angle_rad)
        y = scale * value * math.cos(angle_rad)
        offset_factor = 1.05
        fig.add_annotation(x=x * offset_factor, y=y * offset_factor,
                           text=f"{value:.2f}", showarrow=False,
                           font=dict(size=10, color=TT_DarkBlue))

    # Add radial lines at 30° intervals (background)
    for angle in range(0, 360, 30):
        angle_rad = math.radians(angle)
        line_x = [0, scale * math.sin(angle_rad)]
        line_y = [0, scale * math.cos(angle_rad)]
        fig.add_trace(go.Scatter(x=line_x, y=line_y, mode='lines',
                                 line=dict(color="rgba(99,102,105,0.25)", width=1),
                                 showlegend=False))

    # --- Building footprint overlay (centered) ---
    # Interpret NS_dimension and EW_dimension as values on the same normalized scale as c_dir (0..1 typical).
    # According to your request: building "height" = EW_dimension (vertical extent), and "width" = NS_dimension (horizontal extent).
    # Convert to plotting units:
    # Half-width along x (east-west plotting axis) = (NS_dimension * scale) / 2
    # Half-height along y (north-south plotting axis) = (EW_dimension * scale) / 2
    hx = (NS_dimension * scale) / 2.0
    hy = (EW_dimension * scale) / 2.0

    # Create rectangle vertices (centered at origin) before rotation: (x,y)
    rect_local = [
        (-hx, -hy),
        ( hx, -hy),
        ( hx,  hy),
        (-hx,  hy),
        (-hx, -hy)  # close polygon
    ]

    # Rotation: rotation_angle is clockwise from North.
    # Standard math rotation is counter-clockwise positive, so convert by negating angle.
    theta = math.radians(-rotation_angle)  # negative for clockwise rotation
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    rect_rotated_x = []
    rect_rotated_y = []
    for x0, y0 in rect_local:
        # rotate point (x0, y0) by theta (ccw). We already negated so this effectively rotates clockwise.
        xr = x0 * cos_t - y0 * sin_t
        yr = x0 * sin_t + y0 * cos_t
        rect_rotated_x.append(xr)
        rect_rotated_y.append(yr)

    # Add building polygon on top of other traces (so add it late)
    fig.add_trace(go.Scatter(
        x=rect_rotated_x,
        y=rect_rotated_y,
        mode='lines',
        fill='toself',
        fillcolor="rgba(211,69,29,0.12)",
        line=dict(color="rgba(211,69,29,0.8)", width=2),
        hoverinfo='skip',
        showlegend=False
    ))

    # Annotate rotation + dimensions near the building center
    fig.add_annotation(x=0, y=-max_dim + 0.08*scale,
                       text=f"Rotation: {rotation_angle:.0f}° (clockwise from N) · NS={NS_dimension} · EW={EW_dimension}",
                       showarrow=False, font=dict(size=10, color=TT_DarkBlue))

    # --- Directional outer labels, rotated together with the building ---
    # We'll place labels at 45° increments and rotate their positions by the same rotation_angle (clockwise).
    base_angles = [0, 45, 90, 135, 180, 225, 270, 315]
    labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    label_radius = scale * 1.12

    for base_angle, lab in zip(base_angles, labels):
        # Move label clockwise by rotation_angle (so label positions line up with building rotation)
        label_angle = (base_angle + rotation_angle) % 360
        a_rad = math.radians(label_angle)
        lx = label_radius * math.sin(a_rad)
        ly = label_radius * math.cos(a_rad)

        # Emphasize NE and SW as "principal" (larger and darker), grey-out the rest
        if lab in ('NE', 'SW'):
            font_size = 14
            font_color = TT_DarkBlue
            font_weight = "bold"
        else:
            font_size = 10
            font_color = TT_GrayFaint
            font_weight = "normal"

        fig.add_annotation(x=lx, y=ly, text=lab, showarrow=False,
                           font=dict(size=font_size, color=font_color),
                           xanchor='center', yanchor='middle')

    # Also optionally draw faint marks for each 15° to give a sense of continuous rotation (grayed)
    for angle in range(0, 360, 15):
        a_rad = math.radians((angle + rotation_angle) % 360)
        tick_out = scale * 1.05
        tick_in = scale * 0.98
        x1, y1 = tick_in * math.sin(a_rad), tick_in * math.cos(a_rad)
        x2, y2 = tick_out * math.sin(a_rad), tick_out * math.cos(a_rad)
        fig.add_trace(go.Scatter(x=[x1, x2], y=[y1, y2], mode='lines',
                                 line=dict(color="rgba(99,102,105,0.12)", width=1),
                                 showlegend=False, hoverinfo='skip'))

    # Add cardinal directions (N,E,S,W) at the edges for clarity (also rotate with the frame)
    cardinals = [
        {"dir": "N", "angle": 0},
        {"dir": "E", "angle": 90},
        {"dir": "S", "angle": 180},
        {"dir": "W", "angle": 270}
    ]
    for c in cardinals:
        ang = (c["angle"] + rotation_angle) % 360
        a_rad = math.radians(ang)
        cx = (scale * 1.03) * math.sin(a_rad)
        cy = (scale * 1.03) * math.cos(a_rad)
        fig.add_annotation(x=cx, y=cy, text=c["dir"], showarrow=False,
                           font=dict(size=12, color=TT_DarkBlue, family="Arial"))

    # Final layout
    fig.update_layout(
        showlegend=False,
        xaxis=dict(range=[-max_dim, max_dim], zeroline=False, showgrid=False, showticklabels=False),
        yaxis=dict(range=[-max_dim, max_dim], zeroline=False, showgrid=False, showticklabels=False,
                   scaleanchor="x", scaleratio=1),
        plot_bgcolor='white',
        height=height, width=width,
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
        North-South dimension of the building
    EW_dimension : float
        East-West dimension of the building
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

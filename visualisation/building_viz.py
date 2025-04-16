import plotly.graph_objects as go
def create_building_visualisation(NS_dimension, EW_dimension, z):
    # Create a simple 3D building model
    x = [0, NS_dimension, NS_dimension, 0, 0]
    y = [0, 0, EW_dimension, EW_dimension, 0]
    z_base = [0, 0, 0, 0, 0]
    z_top = [z, z, z, z, z]
    
    # Create a blank figure with minimal styling
    fig = go.Figure()
    
    # Add the base
    fig.add_trace(go.Scatter3d(x=x, y=y, z=z_base, mode='lines', line=dict(color='blue', width=3),
                              name='Base'))
    
    # Add the top
    fig.add_trace(go.Scatter3d(x=x, y=y, z=z_top, mode='lines', line=dict(color='blue', width=3),
                              name='Top'))
    
    # Add the vertical edges
    for i in range(4):
        fig.add_trace(go.Scatter3d(x=[x[i], x[i]], y=[y[i], y[i]], z=[0, z], mode='lines',
                                  line=dict(color='blue', width=3), showlegend=False))
    
    # Set the layout to be minimal but clear
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='North-South (m)', showbackground=False, showgrid=True, zeroline=True),
            yaxis=dict(title='East-West (m)', showbackground=False, showgrid=True, zeroline=True),
            zaxis=dict(title='Height (m)', showbackground=False, showgrid=True, zeroline=True),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        legend=dict(x=0, y=0),
        scene_camera=dict(
            eye=dict(x=1.5, y=-1.5, z=1.2)
        ),
        height=400
    )
    
    return fig

import plotly.graph_objects as go
def create_building_visualisation(NS_dimension, EW_dimension, z):
    # Define colors
    TT_LightBlue = "rgb(136,219,223)"
    TT_MidBlue = "rgb(0,163,173)"
    
    # Create a blank figure
    fig = go.Figure()
    
    # Define vertices for each face of the building
    # North-South faces (mid blue)
    # Front face (y=0)
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, 0, 0],
        z=[0, 0, z, z],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color=TT_MidBlue,
        opacity=1,
        showlegend=False
    ))
    
    # Back face (y=EW_dimension)
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[EW_dimension, EW_dimension, EW_dimension, EW_dimension],
        z=[0, 0, z, z],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color=TT_MidBlue,
        opacity=1,
        showlegend=False
    ))
    
    # East-West faces (light blue)
    # Left face (x=0)
    fig.add_trace(go.Mesh3d(
        x=[0, 0, 0, 0],
        y=[0, EW_dimension, EW_dimension, 0],
        z=[0, 0, z, z],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color=TT_LightBlue,
        opacity=1,
        showlegend=False
    ))
    
    # Right face (x=NS_dimension)
    fig.add_trace(go.Mesh3d(
        x=[NS_dimension, NS_dimension, NS_dimension, NS_dimension],
        y=[0, EW_dimension, EW_dimension, 0],
        z=[0, 0, z, z],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color=TT_LightBlue,
        opacity=1,
        showlegend=False
    ))
    
    # Top face (z=z)
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, EW_dimension, EW_dimension],
        z=[z, z, z, z],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color=TT_LightBlue,
        opacity=1,
        showlegend=False
    ))
    
    # Bottom face (z=0)
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, EW_dimension, EW_dimension],
        z=[0, 0, 0, 0],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color=TT_LightBlue,
        opacity=1,
        showlegend=False
    ))
    
    # Set the layout to be minimal with no axes or grid
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, showticklabels=False, showbackground=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, showticklabels=False, showbackground=False, zeroline=False),
            zaxis=dict(visible=False, showgrid=False, showticklabels=False, showbackground=False, zeroline=False),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        showlegend=False,
        scene_camera=dict(
            eye=dict(x=1.5, y=-1.5, z=1.2)
        ),
        height=400
    )
    
    return fig

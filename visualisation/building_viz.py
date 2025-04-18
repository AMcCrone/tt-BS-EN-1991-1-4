import plotly.graph_objects as go
def create_building_visualisation(NS_dimension, EW_dimension, z, include_inset=False, inset_offset=0, inset_height=0):
    # Define colors
    TT_LightBlue = "rgb(136,219,223)"
    TT_MidBlue = "rgb(0,163,173)"
    TT_DarkBlue = "rgb(0,48,60)"
    
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
        showlegend=False,
        hoverinfo='none'
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
        showlegend=False,
        hoverinfo='none'
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
        showlegend=False,
        hoverinfo='none'
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
        showlegend=False,
        hoverinfo='none'
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
        showlegend=False,
        hoverinfo='none'
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
        showlegend=False,
        hoverinfo='none'
    ))
    
    # Add inset zone if requested
    if include_inset and inset_offset > 0 and inset_height > 0:
        # Calculate inset dimensions
        inset_NS = NS_dimension - (2 * inset_offset)
        inset_EW = EW_dimension - (2 * inset_offset)
        inset_base_z = z
        inset_top_z = z + inset_height
        
        if inset_NS > 0 and inset_EW > 0:  # Only draw if dimensions are positive
            # Front face of inset (y=inset_offset)
            fig.add_trace(go.Mesh3d(
                x=[inset_offset, inset_offset + inset_NS, inset_offset + inset_NS, inset_offset],
                y=[inset_offset, inset_offset, inset_offset, inset_offset],
                z=[inset_base_z, inset_base_z, inset_top_z, inset_top_z],
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                color=TT_DarkBlue,
                opacity=1,
                showlegend=False,
                hoverinfo='none'
            ))
            
            # Back face of inset (y=EW_dimension-inset_offset)
            fig.add_trace(go.Mesh3d(
                x=[inset_offset, inset_offset + inset_NS, inset_offset + inset_NS, inset_offset],
                y=[EW_dimension - inset_offset, EW_dimension - inset_offset, 
                   EW_dimension - inset_offset, EW_dimension - inset_offset],
                z=[inset_base_z, inset_base_z, inset_top_z, inset_top_z],
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                color=TT_DarkBlue,
                opacity=1,
                showlegend=False,
                hoverinfo='none'
            ))
            
            # Left face of inset (x=inset_offset)
            fig.add_trace(go.Mesh3d(
                x=[inset_offset, inset_offset, inset_offset, inset_offset],
                y=[inset_offset, EW_dimension - inset_offset, 
                   EW_dimension - inset_offset, inset_offset],
                z=[inset_base_z, inset_base_z, inset_top_z, inset_top_z],
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                color=TT_DarkBlue,
                opacity=1,
                showlegend=False,
                hoverinfo='none'
            ))
            
            # Right face of inset (x=NS_dimension-inset_offset)
            fig.add_trace(go.Mesh3d(
                x=[NS_dimension - inset_offset, NS_dimension - inset_offset, 
                   NS_dimension - inset_offset, NS_dimension - inset_offset],
                y=[inset_offset, EW_dimension - inset_offset, 
                   EW_dimension - inset_offset, inset_offset],
                z=[inset_base_z, inset_base_z, inset_top_z, inset_top_z],
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                color=TT_DarkBlue,
                opacity=1,
                showlegend=False,
                hoverinfo='none'
            ))
            
            # Top face of inset (z=inset_top_z)
            fig.add_trace(go.Mesh3d(
                x=[inset_offset, inset_offset + inset_NS, inset_offset + inset_NS, inset_offset],
                y=[inset_offset, inset_offset, EW_dimension - inset_offset, EW_dimension - inset_offset],
                z=[inset_top_z, inset_top_z, inset_top_z, inset_top_z],
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                color=TT_DarkBlue,
                opacity=1,
                showlegend=False,
                hoverinfo='none'
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
        height=400,
        hovermode=False
    )
    
    return fig

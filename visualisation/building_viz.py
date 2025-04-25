import plotly.graph_objects as go
def create_building_visualisation(NS_dimension, EW_dimension, z, include_inset=False, inset_offset=0, inset_height=0):
    # Define colors
    TT_LightBlue = "rgb(136,219,223)"
    TT_MidBlue = "rgb(0,163,173)"
    TT_DarkBlue = "rgb(0,48,60)"
    Ground_Grey = "rgb(200,200,200)"  # Grey color for the ground base
    
    # Create a blank figure
    fig = go.Figure()
    
    # Add ground base (extending beyond the building footprint)
    ground_extension = max(NS_dimension, EW_dimension) * 0.5  # Extend ground beyond building
    fig.add_trace(go.Mesh3d(
        x=[-ground_extension, NS_dimension + ground_extension, NS_dimension + ground_extension, -ground_extension],
        y=[-ground_extension, -ground_extension, EW_dimension + ground_extension, EW_dimension + ground_extension],
        z=[0, 0, 0, 0],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color=Ground_Grey,
        opacity=0.7,
        showlegend=False,
        hoverinfo='none'
    ))
    
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
    
    # Add dimensions to the plot
    # NS dimension arrow and text
    fig.add_trace(go.Scatter3d(
        x=[0, NS_dimension],
        y=[-ground_extension/2, -ground_extension/2],
        z=[0, 0],
        mode='lines+text',
        line=dict(color='black', width=3),
        text=['', f'{NS_dimension}m'],
        textposition='middle right',
        showlegend=False
    ))
    
    # EW dimension arrow and text
    fig.add_trace(go.Scatter3d(
        x=[-ground_extension/2, -ground_extension/2],
        y=[0, EW_dimension],
        z=[0, 0],
        mode='lines+text',
        line=dict(color='black', width=3),
        text=['', f'{EW_dimension}m'],
        textposition='middle right',
        showlegend=False
    ))
    
    # Height dimension arrow and text
    fig.add_trace(go.Scatter3d(
        x=[-ground_extension/2, -ground_extension/2],
        y=[0, 0],
        z=[0, z],
        mode='lines+text',
        line=dict(color='black', width=3),
        text=['', f'{z}m'],
        textposition='middle right',
        showlegend=False
    ))
    
    # If inset is included, add its height dimension
    if include_inset and inset_offset > 0 and inset_height > 0:
        fig.add_trace(go.Scatter3d(
            x=[NS_dimension + ground_extension/3, NS_dimension + ground_extension/3],
            y=[EW_dimension/2, EW_dimension/2],
            z=[z, z + inset_height],
            mode='lines+text',
            line=dict(color='black', width=3),
            text=['', f'{inset_height}m'],
            textposition='middle right',
            showlegend=False
        ))
    
    # Set the layout to be minimal but retain enough context
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=True, showgrid=False, showticklabels=False, title=''),
            yaxis=dict(visible=True, showgrid=False, showticklabels=False, title=''),
            zaxis=dict(visible=True, showgrid=False, showticklabels=False, title=''),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        showlegend=False,
        scene_camera=dict(
            eye=dict(x=1.8, y=-1.8, z=1.5)  # Adjusted camera position for better view
        ),
        height=500,  # Increased height for better visibility
        width=700,   # Set width for better proportions
        hovermode=False
    )
    
    return fig

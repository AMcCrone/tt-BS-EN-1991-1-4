import plotly.graph_objects as go
def create_building_visualisation(NS_dimension, EW_dimension, z, include_inset=False, inset_offset=0, inset_height=0):
    # Define colors
    TT_LightBlue = "rgb(136,219,223)"
    TT_MidBlue = "rgb(0,163,173)"
    TT_DarkBlue = "rgb(0,48,60)"
    TT_LightGrey = "rgb(223,224,225)"  # Updated grey color for the ground base
    
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
        color=TT_LightGrey,
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
    
    # Add dimension arrows using cone traces for arrowheads
    arrow_size = min(NS_dimension, EW_dimension, z) * 0.04
    text_offset = arrow_size * 1.5
    
    # NS dimension
    # Main line
    fig.add_trace(go.Scatter3d(
        x=[arrow_size, NS_dimension - arrow_size],
        y=[-ground_extension/2, -ground_extension/2],
        z=[0, 0],
        mode='lines',
        line=dict(color='black', width=3),
        showlegend=False,
        hoverinfo='none'
    ))
    # Left arrowhead (cone)
    fig.add_trace(go.Cone(
        x=[0],
        y=[-ground_extension/2],
        z=[0],
        u=[-arrow_size],
        v=[0],
        w=[0],
        colorscale=[[0, 'black'], [1, 'black']],
        showscale=False,
        sizemode='absolute',
        sizeref=arrow_size,
        hoverinfo='none'
    ))
    # Right arrowhead (cone)
    fig.add_trace(go.Cone(
        x=[NS_dimension],
        y=[-ground_extension/2],
        z=[0],
        u=[arrow_size],
        v=[0],
        w=[0],
        colorscale=[[0, 'black'], [1, 'black']],
        showscale=False,
        sizemode='absolute',
        sizeref=arrow_size,
        hoverinfo='none'
    ))
    # Text for NS dimension
    fig.add_trace(go.Scatter3d(
        x=[NS_dimension/2],
        y=[-ground_extension/2 - text_offset],
        z=[0],
        mode='text',
        text=[f'{NS_dimension}m'],
        textposition='middle center',
        showlegend=False,
        hoverinfo='none'
    ))
    
    # EW dimension
    # Main line
    fig.add_trace(go.Scatter3d(
        x=[-ground_extension/2, -ground_extension/2],
        y=[arrow_size, EW_dimension - arrow_size],
        z=[0, 0],
        mode='lines',
        line=dict(color='black', width=3),
        showlegend=False,
        hoverinfo='none'
    ))
    # Bottom arrowhead (cone)
    fig.add_trace(go.Cone(
        x=[-ground_extension/2],
        y=[0],
        z=[0],
        u=[0],
        v=[-arrow_size],
        w=[0],
        colorscale=[[0, 'black'], [1, 'black']],
        showscale=False,
        sizemode='absolute',
        sizeref=arrow_size,
        hoverinfo='none'
    ))
    # Top arrowhead (cone)
    fig.add_trace(go.Cone(
        x=[-ground_extension/2],
        y=[EW_dimension],
        z=[0],
        u=[0],
        v=[arrow_size],
        w=[0],
        colorscale=[[0, 'black'], [1, 'black']],
        showscale=False,
        sizemode='absolute',
        sizeref=arrow_size,
        hoverinfo='none'
    ))
    # Text for EW dimension
    fig.add_trace(go.Scatter3d(
        x=[-ground_extension/2 - text_offset],
        y=[EW_dimension/2],
        z=[0],
        mode='text',
        text=[f'{EW_dimension}m'],
        textposition='middle center',
        showlegend=False,
        hoverinfo='none'
    ))
    
    # Height dimension
    # Main line
    fig.add_trace(go.Scatter3d(
        x=[-ground_extension/2, -ground_extension/2],
        y=[0, 0],
        z=[arrow_size, z - arrow_size],
        mode='lines',
        line=dict(color='black', width=3),
        showlegend=False,
        hoverinfo='none'
    ))
    # Bottom arrowhead (cone)
    fig.add_trace(go.Cone(
        x=[-ground_extension/2],
        y=[0],
        z=[0],
        u=[0],
        v=[0],
        w=[-arrow_size],
        colorscale=[[0, 'black'], [1, 'black']],
        showscale=False,
        sizemode='absolute',
        sizeref=arrow_size,
        hoverinfo='none'
    ))
    # Top arrowhead (cone)
    fig.add_trace(go.Cone(
        x=[-ground_extension/2],
        y=[0],
        z=[z],
        u=[0],
        v=[0],
        w=[arrow_size],
        colorscale=[[0, 'black'], [1, 'black']],
        showscale=False,
        sizemode='absolute',
        sizeref=arrow_size,
        hoverinfo='none'
    ))
    # Text for Height dimension
    fig.add_trace(go.Scatter3d(
        x=[-ground_extension/2 - text_offset],
        y=[0],
        z=[z/2],
        mode='text',
        text=[f'{z}m'],
        textposition='middle center',
        showlegend=False,
        hoverinfo='none'
    ))
    
    # If inset is included, add its height dimension
    if include_inset and inset_offset > 0 and inset_height > 0:
        # Main line
        fig.add_trace(go.Scatter3d(
            x=[NS_dimension + ground_extension/3, NS_dimension + ground_extension/3],
            y=[EW_dimension/2, EW_dimension/2],
            z=[z + arrow_size, z + inset_height - arrow_size],
            mode='lines',
            line=dict(color='black', width=3),
            showlegend=False,
            hoverinfo='none'
        ))
        # Bottom arrowhead (cone)
        fig.add_trace(go.Cone(
            x=[NS_dimension + ground_extension/3],
            y=[EW_dimension/2],
            z=[z],
            u=[0],
            v=[0],
            w=[-arrow_size],
            colorscale=[[0, 'black'], [1, 'black']],
            showscale=False,
            sizemode='absolute',
            sizeref=arrow_size,
            hoverinfo='none'
        ))
        # Top arrowhead (cone)
        fig.add_trace(go.Cone(
            x=[NS_dimension + ground_extension/3],
            y=[EW_dimension/2],
            z=[z + inset_height],
            u=[0],
            v=[0],
            w=[arrow_size],
            colorscale=[[0, 'black'], [1, 'black']],
            showscale=False,
            sizemode='absolute',
            sizeref=arrow_size,
            hoverinfo='none'
        ))
        # Text for inset height
        fig.add_trace(go.Scatter3d(
            x=[NS_dimension + ground_extension/3 + text_offset],
            y=[EW_dimension/2],
            z=[z + inset_height/2],
            mode='text',
            text=[f'{inset_height}m'],
            textposition='middle center',
            showlegend=False,
            hoverinfo='none'
        ))
    
    # Set the layout to be completely clean with no axes or grid
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
            eye=dict(x=1.8, y=-1.8, z=1.5)
        ),
        height=500,
        width=700,
        hovermode=False
    )
    
    return fig

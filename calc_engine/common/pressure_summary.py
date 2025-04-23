import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

def create_pressure_summary(session_state, results_by_direction):
    """
    Create a summary DataFrame with pressure/suction values for each elevation.
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions and qp value
    results_by_direction : dict
        Dictionary of DataFrames with cp,e values for each direction
    
    Returns:
    --------
    pd.DataFrame
        Summary of pressure/suction values for all elevations
    """
    # Extract dimensions and peak velocity pressure
    h = session_state.inputs.get("z", 10.0)  # Building height
    qp_value = session_state.inputs.get("qp_value", 1000.0)  # Peak velocity pressure in N/m²
    
    # Define cp,i values
    cp_i_positive = 0.2
    cp_i_negative = -0.3
    
    # Initialize summary data
    summary_data = []
    
    # Process each direction (elevation)
    for direction, cp_df in results_by_direction.items():
        # For each zone in this direction
        for _, row in cp_df.iterrows():
            zone = row['Zone']
            
            # Skip Zone E
            if zone == 'E':
                continue
                
            cp_e = row['cp,e']
            
            # Round cp,e to 2 decimal places
            cp_e = round(cp_e, 2)
            
            # Calculate external pressure
            we = qp_value * cp_e
            
            # Calculate internal pressures
            wi_positive = qp_value * cp_i_positive
            wi_negative = qp_value * cp_i_negative
            
            # Calculate net pressures - most onerous combination
            net_positive = max(we + wi_positive, we - wi_negative)  # Maximum positive pressure
            net_negative = min(we + wi_negative, we - wi_positive)  # Maximum negative pressure
            
            # Determine the governing case (maximum absolute value)
            if abs(net_positive) > abs(net_negative):
                net_pressure = net_positive
                # Determine which internal pressure was used
                if net_positive == (we + wi_positive):
                    cp_i_used = cp_i_positive
                    wi_used = wi_positive
                else:
                    cp_i_used = cp_i_negative
                    wi_used = wi_negative
            else:
                net_pressure = net_negative
                # Determine which internal pressure was used
                if net_negative == (we + wi_negative):
                    cp_i_used = cp_i_negative
                    wi_used = wi_negative
                else:
                    cp_i_used = cp_i_positive
                    wi_used = wi_positive
            
            # Round cp,i to 2 decimal places
            cp_i_used = round(cp_i_used, 2)
            
            # Convert N/m² to kPa and round to 2 decimal places
            we_kpa = round(we / 1000, 2)
            wi_kpa = round(wi_used / 1000, 2)
            net_kpa = round(net_pressure / 1000, 2)
            
            # Determine action type based on net pressure
            action_type = "Pressure" if net_pressure > 0 else "Suction"
            
            # Add to summary data
            summary_data.append({
                "Direction": direction,
                "Zone": zone,
                "cp,e": cp_e,
                "cp,i (used)": cp_i_used,
                "We (kPa)": we_kpa,
                "Wi (kPa)": wi_kpa,
                "Net (kPa)": net_kpa,
                "Action": action_type
            })
    
    # Create DataFrame
    summary_df = pd.DataFrame(summary_data)
    
    return summary_df

def create_wind_pressure_plot(building_height, building_width, qp_value, direction):
    """Create wind pressure profile plot using Plotly."""
    # Determine the case based on height-to-width ratio
    profile_case = get_profile_case(building_height, building_width)
    
    # Create height points for plotting
    z_points = np.linspace(0, building_height, 100)
    qp_points = [get_qp_at_height(z, building_height, building_width, qp_value) for z in z_points]
    
    # Create the figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Define max arrow length and reference point
    max_arrow_length = building_width * 1.5
    ref_x = building_width * 1.5
    arrow_scale = max_arrow_length / qp_value if qp_value > 0 else 1
    
    # Create building outline
    fig.add_trace(
        go.Scatter(
            x=[0, building_width, building_width, 0, 0],
            y=[0, 0, building_height, building_height, 0],
            fill='toself',
            fillcolor=TT_LightGrey,
            line=dict(color=TT_DarkBlue, width=2),
            name='Building'
        )
    )
    
    # Draw pressure profile curve
    fig.add_trace(
        go.Scatter(
            x=[ref_x + qp * arrow_scale for qp in qp_points],
            y=z_points,
            line=dict(color=TT_MidBlue, width=3),
            name='Pressure Profile'
        )
    )
    
    # Draw arrows at different heights
    num_arrows = 15
    arrow_heights = np.linspace(0.1*building_height, 0.9*building_height, num_arrows)
    
    for i, z_height in enumerate(arrow_heights):
        qp_at_z = get_qp_at_height(z_height, building_height, building_width, qp_value)
        arrow_length = qp_at_z * arrow_scale
        
        # Draw arrow line
        fig.add_trace(
            go.Scatter(
                x=[ref_x, ref_x + arrow_length],
                y=[z_height, z_height],
                line=dict(color=TT_Orange, width=1),
                showlegend=False
            )
        )
        
        # Draw arrow head (triangle)
        head_size = 0.02 * building_height
        if i % 3 == 0:  # Add pressure text for every 3rd arrow
            fig.add_annotation(
                x=ref_x + arrow_length + 0.1*building_width,
                y=z_height,
                text=f"{qp_at_z:.2f} N/m²",
                showarrow=False,
                font=dict(size=10),
                xanchor="left"
            )
        
        # Add arrowhead annotation
        fig.add_annotation(
            x=ref_x + arrow_length,
            y=z_height,
            text="",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=2,
            arrowcolor=TT_Orange,
            axref="x",
            ayref="y",
            ax=ref_x + arrow_length - 0.05*building_width,
            ay=z_height
        )
    
    # Add reference height lines
    if building_height <= building_width:
        # Case 1: Only mark h
        fig.add_shape(
            type="line",
            x0=0, y0=building_height, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_height,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_annotation(
            x=0, y=building_height,
            text=f"zₑ = h = {building_height} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        
    elif building_width < building_height <= 2*building_width:
        # Case 2: Mark b and h
        fig.add_shape(
            type="line",
            x0=0, y0=building_width, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_width,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_shape(
            type="line",
            x0=0, y0=building_height, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_height,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_annotation(
            x=0, y=building_width,
            text=f"zₑ = b = {building_width} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        fig.add_annotation(
            x=0, y=building_height,
            text=f"zₑ = h = {building_height} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        
        # Add rectangle for upper zone
        fig.add_shape(
            type="rect",
            x0=0, y0=building_width,
            x1=building_width, y1=building_height,
            fillcolor=TT_LightLightBlue,
            opacity=0.3,
            line=dict(width=0)
        )
        
    else:  # h > 2*b
        # Case 3: Mark b, h-b, and h
        z_strip = building_height - building_width
        fig.add_shape(
            type="line",
            x0=0, y0=building_width, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_width,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_shape(
            type="line",
            x0=0, y0=z_strip, 
            x1=ref_x + max_arrow_length * 1.2, y1=z_strip,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_shape(
            type="line",
            x0=0, y0=building_height, 
            x1=ref_x + max_arrow_length * 1.2, y1=building_height,
            line=dict(color=TT_Orange, width=1, dash="dash")
        )
        fig.add_annotation(
            x=0, y=building_width,
            text=f"zₑ = b = {building_width} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        fig.add_annotation(
            x=0, y=z_strip,
            text=f"zₑ = z_strip = {z_strip:.1f} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        fig.add_annotation(
            x=0, y=building_height,
            text=f"zₑ = h = {building_height} m",
            showarrow=False,
            font=dict(color=TT_Orange, size=10),
            xanchor="left",
            yanchor="bottom"
        )
        
        # Add rectangle for middle zone
        fig.add_shape(
            type="rect",
            x0=0, y0=building_width,
            x1=building_width, y1=z_strip,
            fillcolor=TT_LightLightBlue,
            opacity=0.3,
            line=dict(width=0)
        )
        
        # Add rectangle for upper zone
        fig.add_shape(
            type="rect",
            x0=0, y0=z_strip,
            x1=building_width, y1=building_height,
            fillcolor=TT_LightBlue,
            opacity=0.3,
            line=dict(width=0)
        )
    
    # Update layout
    fig.update_layout(
        title=f'Wind Pressure Profile - {direction} Direction - {profile_case}',
        xaxis_title='Distance [m]',
        yaxis_title='Height [m]',
        template='plotly_white',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    # Set axes limits
    fig.update_xaxes(range=[-0.5*building_width, ref_x + max_arrow_length * 1.2])
    fig.update_yaxes(range=[-0.1*building_height, 1.1*building_height])
    
    return fig, profile_case

def visualize_wind_pressures(session_state):
    """
    Create and display wind pressure visualizations including summary table and elevation plots.
    
    Parameters:
    -----------
    session_state : StreamlitSessionState
        Streamlit session state containing building dimensions and other inputs
    
    Returns:
    --------
    tuple
        (summary_df, elevation_figures) - Summary DataFrame and dictionary of plotly figures
    """
    import streamlit as st
    
    # First calculate the cp,e values considering funnelling effects
    results_by_direction = calculate_cpe()
    
    # Create the summary DataFrame
    summary_df = create_pressure_summary(session_state, results_by_direction)
    
    # Create elevation plots
    elevation_figures = plot_elevation_with_pressures(session_state, results_by_direction)
    
    # Display the summary table
    st.subheader("Wind Pressure Summary")
    st.dataframe(summary_df)
    
    # Add download button for the summary table
    csv = summary_df.to_csv(index=False)
    st.download_button(
        label="Download Summary CSV",
        data=csv,
        file_name="wind_pressure_summary.csv",
        mime="text/csv"
    )
    
    # Display elevation plots
    st.subheader("Elevation Wind Pressure Zones")
    
    # Create two columns for North-South elevations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(elevation_figures["North"], use_container_width=True)
    
    with col2:
        st.plotly_chart(elevation_figures["South"], use_container_width=True)
    
    # Create two columns for East-West elevations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(elevation_figures["East"], use_container_width=True)
    
    with col2:
        st.plotly_chart(elevation_figures["West"], use_container_width=True)
    
    return summary_df, elevation_figures

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Define colors
TT_Orange = "rgb(211,69,29)"
TT_LightBlue = "rgb(136,219,223)"
TT_MidBlue = "rgb(0,163,173)"
TT_DarkBlue = "rgb(0,48,60)"
TT_Grey = "rgb(99,102,105)"
TT_LightGrey = "rgb(229,229,229)"  # Lighter grey for the donut building

def display_funnelling_inputs():
    """Display inputs for funnelling effect calculations"""
    st.subheader("Building Proximity (Funnelling)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        north_gap = st.number_input("North Gap [m]", min_value=0.0, value=st.session_state.inputs.get("north_gap", 10.0), help="Distance to nearest building from North face")
    with col2:
        south_gap = st.number_input("South Gap [m]", min_value=0.0, value=st.session_state.inputs.get("south_gap", 10.0), help="Distance to nearest building from South face")
    with col3:
        east_gap = st.number_input("East Gap [m]", min_value=0.0, value=st.session_state.inputs.get("east_gap", 10.0), help="Distance to nearest building from East face")
    with col4:
        west_gap = st.number_input("West Gap [m]", min_value=0.0, value=st.session_state.inputs.get("west_gap", 10.0), help="Distance to nearest building from West face")
    
    # Save values to session state
    st.session_state.inputs["north_gap"] = north_gap
    st.session_state.inputs["south_gap"] = south_gap
    st.session_state.inputs["east_gap"] = east_gap
    st.session_state.inputs["west_gap"] = west_gap
    
    # Create building layout visualization
    display_building_layout(north_gap, south_gap, east_gap, west_gap)
    
    return north_gap, south_gap, east_gap, west_gap

def display_building_layout(north_gap, south_gap, east_gap, west_gap):
    """Display a plan view of the building with adjacent structures"""
    NS_dimension = st.session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = st.session_state.inputs.get("EW_dimension", 40.0)
    
    # Calculate coordinates for main building
    building_x = [-EW_dimension/2, EW_dimension/2, EW_dimension/2, -EW_dimension/2, -EW_dimension/2]
    building_y = [-NS_dimension/2, -NS_dimension/2, NS_dimension/2, NS_dimension/2, -NS_dimension/2]
    
    # Create the figure
    fig = go.Figure()
    
    # Create a donut shape for surrounding buildings
    # Outer boundary (very large to extend beyond view)
    plot_size = max(NS_dimension, EW_dimension) * 2
    outer_x = [-plot_size, plot_size, plot_size, -plot_size, -plot_size]
    outer_y = [-plot_size, -plot_size, plot_size, plot_size, -plot_size]
    
    # Inner boundary (just around the main building with gaps)
    inner_x = [
        -EW_dimension/2 - west_gap, # Bottom left
        EW_dimension/2 + east_gap,  # Bottom right
        EW_dimension/2 + east_gap,  # Top right
        -EW_dimension/2 - west_gap, # Top left
        -EW_dimension/2 - west_gap  # Back to start
    ]
    inner_y = [
        -NS_dimension/2 - south_gap, # Bottom left
        -NS_dimension/2 - south_gap, # Bottom right
        NS_dimension/2 + north_gap,  # Top right
        NS_dimension/2 + north_gap,  # Top left
        -NS_dimension/2 - south_gap  # Back to start
    ]
    
    # Add donut shape (surrounding buildings)
    fig.add_trace(go.Scatter(
        x=outer_x + [None] + inner_x[::-1],  # Outer shape and reversed inner shape with None to create a break
        y=outer_y + [None] + inner_y[::-1],
        fill='toself',
        fillcolor=TT_LightGrey,
        line=dict(color=TT_Grey, width=1),
        name="Surrounding Buildings",
        hoverinfo="text",
        hovertext="Surrounding Buildings",
        mode="lines"  # Just lines, no markers
    ))
    
    # Main building
    fig.add_trace(go.Scatter(
        x=building_x,
        y=building_y,
        fill="toself",
        fillcolor=TT_MidBlue,
        line=dict(color=TT_DarkBlue, width=2),
        name="Main Building",
        hoverinfo="text",
        hovertext="Main Building",
        mode="lines"  # Just lines, no markers
    ))
    
    # Add building labels
    # North building label
    fig.add_annotation(
        x=0,
        y=NS_dimension/2 + north_gap + 10,
        text="North Building",
        showarrow=False,
        font=dict(color=TT_Grey, size=12)
    )
    
    # South building label
    fig.add_annotation(
        x=0,
        y=-NS_dimension/2 - south_gap - 10,
        text="South Building",
        showarrow=False,
        font=dict(color=TT_Grey, size=12)
    )
    
    # East building label
    fig.add_annotation(
        x=EW_dimension/2 + east_gap + 10,
        y=0,
        text="East Building",
        showarrow=False,
        font=dict(color=TT_Grey, size=12)
    )
    
    # West building label
    fig.add_annotation(
        x=-EW_dimension/2 - west_gap - 10,
        y=0,
        text="West Building",
        showarrow=False,
        font=dict(color=TT_Grey, size=12)
    )
    
    # Highlight the gaps with orange if funnelling applies
    for direction, gap, dimension, is_ns in [
        ("North", north_gap, EW_dimension, True),
        ("South", south_gap, EW_dimension, True),
        ("East", east_gap, NS_dimension, False),
        ("West", west_gap, NS_dimension, False)
    ]:
        # Calculate e (the smaller of b or 2h)
        h = st.session_state.inputs.get("z", 10.0)  # Building height
        b = dimension  # Width of face perpendicular to wind
        e = min(b, 2*h)
        
        # Check if funnelling applies (gap between e/4 and e)
        if e/4 < gap < e:
            if is_ns:  # North-South direction
                if direction == "North":
                    x = [-dimension/2, dimension/2, dimension/2, -dimension/2, -dimension/2]
                    y = [NS_dimension/2, NS_dimension/2, NS_dimension/2+gap, NS_dimension/2+gap, NS_dimension/2]
                else:  # South
                    x = [-dimension/2, dimension/2, dimension/2, -dimension/2, -dimension/2]
                    y = [-NS_dimension/2, -NS_dimension/2, -NS_dimension/2-gap, -NS_dimension/2-gap, -NS_dimension/2]
            else:  # East-West direction
                if direction == "East":
                    x = [EW_dimension/2, EW_dimension/2+gap, EW_dimension/2+gap, EW_dimension/2, EW_dimension/2]
                    y = [-dimension/2, -dimension/2, dimension/2, dimension/2, -dimension/2]
                else:  # West
                    x = [-EW_dimension/2, -EW_dimension/2-gap, -EW_dimension/2-gap, -EW_dimension/2, -EW_dimension/2]
                    y = [-dimension/2, -dimension/2, dimension/2, dimension/2, -dimension/2]
            
            # Calculate funnelling intensity based on gap's position between e/4 and e
            if gap <= e/2:
                # Interpolate between e/4 and e/2 (increasing effect)
                factor = (gap - e/4) / (e/4)  # 0 at e/4, 1 at e/2
                intensity_text = f"Increasing (factor: {factor:.2f})"
            else:
                # Interpolate between e/2 and e (decreasing effect)
                factor = (e - gap) / (e/2)  # 1 at e/2, 0 at e
                intensity_text = f"Decreasing (factor: {factor:.2f})"
            
            fig.add_trace(go.Scatter(
                x=x,
                y=y,
                fill="toself",
                fillcolor=TT_Orange,
                opacity=0.3,
                line=dict(color=TT_Orange, width=1),
                name=f"{direction} Funnelling Zone",
                hoverinfo="text",
                hovertext=f"{direction} Funnelling Zone - {intensity_text}",
                mode="lines"  # Just lines, no markers
            ))
            
            # Add a funnelling effect label if applicable
            if is_ns:
                label_x = 0
                label_y = NS_dimension/2 + gap/2 if direction == "North" else -NS_dimension/2 - gap/2
            else:
                label_x = EW_dimension/2 + gap/2 if direction == "East" else -EW_dimension/2 - gap/2
                label_y = 0
                
            fig.add_annotation(
                x=label_x,
                y=label_y,
                text=f"Funnelling\nGap: {gap:.1f}m",
                showarrow=False,
                font=dict(color=TT_Orange, size=10),
                bgcolor="rgba(255,255,255,0.7)"
            )
    
    # Layout settings
    fig.update_layout(
        title="Building Layout (Plan View)",
        showlegend=False,
        autosize=False,
        width=800,
        height=500,
        margin=dict(l=50, r=50, b=50, t=50),
    )
    
    # Make sure axes are equal scale and hide axes
    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        showline=False
    )
    
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        showline=False
    )
    
    st.plotly_chart(fig)

def calculate_cpe():
    """
    Calculate external pressure coefficients (cp,e) for projects considering funnelling effects for all wind directions
    
    Returns:
    - Dictionary of DataFrames of cp,e values for different wind directions
    """
    h = st.session_state.inputs.get("z", 10.0)  # Building height
    NS_dimension = st.session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = st.session_state.inputs.get("EW_dimension", 40.0)
    
    # Calculate for all wind directions
    wind_directions = ["N", "S", "E", "W"]
    results_by_direction = {}
    
    for wind_direction in wind_directions:    
        # Determine h/d ratio based on wind direction
        if wind_direction in ["N", "S"]:
            d = NS_dimension
        else:  # E or W
            d = EW_dimension
        
        h_d_ratio = h / d
        
        # Interpolate cp,e values based on h/d ratio
        # Values from BS EN 1991-1-4 Table 7.1
        h_d_points = [0.25, 1.0, 5.0]
        
        # Base values for each zone at different h/d ratios
        zone_A_values = [-1.2, -1.2, -1.2]
        zone_B_values = [-0.8, -0.8, -0.8]
        zone_C_values = [-0.5, -0.5, -0.5]
        zone_D_values = [0.8, 0.8, 0.8]  # Windward
        zone_E_values = [-0.5, -0.5, -0.7]  # Leeward
        
        # Linear interpolation for h/d ratio
        if h_d_ratio <= 0.25:
            cp_A = zone_A_values[0]
            cp_B = zone_B_values[0]
            cp_C = zone_C_values[0]
            cp_D = zone_D_values[0]
            cp_E = zone_E_values[0]
        elif h_d_ratio >= 5.0:
            cp_A = zone_A_values[2]
            cp_B = zone_B_values[2]
            cp_C = zone_C_values[2]
            cp_D = zone_D_values[2]
            cp_E = zone_E_values[2]
        else:
            # Interpolate between known points
            for i in range(len(h_d_points)-1):
                if h_d_points[i] <= h_d_ratio <= h_d_points[i+1]:
                    factor = (h_d_ratio - h_d_points[i]) / (h_d_points[i+1] - h_d_points[i])
                    cp_A = zone_A_values[i] + factor * (zone_A_values[i+1] - zone_A_values[i])
                    cp_B = zone_B_values[i] + factor * (zone_B_values[i+1] - zone_B_values[i])
                    cp_C = zone_C_values[i] + factor * (zone_C_values[i+1] - zone_C_values[i])
                    cp_D = zone_D_values[i] + factor * (zone_D_values[i+1] - zone_D_values[i])
                    cp_E = zone_E_values[i] + factor * (zone_E_values[i+1] - zone_E_values[i])
                    break
        
        # Store original values before funnelling adjustment
        base_cp_A = cp_A
        base_cp_B = cp_B
        base_cp_C = cp_C
        
        # Check for funnelling effect based on wind direction
        if wind_direction == "N":
            gap = st.session_state.inputs.get("south_gap", 10.0)
            dimension = EW_dimension
        elif wind_direction == "S":
            gap = st.session_state.inputs.get("north_gap", 10.0)
            dimension = EW_dimension
        elif wind_direction == "E":
            gap = st.session_state.inputs.get("west_gap", 10.0)
            dimension = NS_dimension
        else:  # "W"
            gap = st.session_state.inputs.get("east_gap", 10.0)
            dimension = NS_dimension
        
        # Calculate e (the smaller of b or 2h)
        b = dimension  # Width of face perpendicular to wind
        e = min(b, 2*h)
        
        # Apply funnelling according to the guidance and graph
        has_funnelling = False
        funnelling_factor = 0
        
        # Define the funnelling peak values
        max_funnel_cp_A = -1.6
        max_funnel_cp_B = -0.9
        max_funnel_cp_C = -0.9
        
        if e/4 < gap < e:  # Funnelling applies when e/4 < gap < e
            has_funnelling = True
            
            if gap <= e/2:
                # Interpolate between e/4 and e/2 (increasing effect)
                # At e/4: original values
                # At e/2: maximum funnelling values
                factor = (gap - e/4) / (e/4)  # 0 at e/4, 1 at e/2
                
                cp_A = base_cp_A + factor * (max_funnel_cp_A - base_cp_A)
                cp_B = base_cp_B + factor * (max_funnel_cp_B - base_cp_B)
                cp_C = base_cp_C + factor * (max_funnel_cp_C - base_cp_C)
                funnelling_factor = factor
                
            else:
                # Interpolate between e/2 and e (decreasing effect)
                # At e/2: maximum funnelling values
                # At e: original values
                factor = (e - gap) / (e/2)  # 1 at e/2, 0 at e
                
                cp_A = base_cp_A + factor * (max_funnel_cp_A - base_cp_A)
                cp_B = base_cp_B + factor * (max_funnel_cp_B - base_cp_B)
                cp_C = base_cp_C + factor * (max_funnel_cp_C - base_cp_C)
                funnelling_factor = factor
        
        # Map the direction code to full name for display
        dir_map = {"N": "North", "S": "South", "E": "East", "W": "West"}
        direction_name = dir_map[wind_direction]
        
        # Add funnelling indicator to description if applicable
        funnelling_note = f" (Funnelling factor: {funnelling_factor:.2f})" if has_funnelling else ""
        
        # Create results for this direction
        direction_results = [
            {"Zone": "A", "cp,e": cp_A, "Description": f"Side Suction (Edge){funnelling_note}"},
            {"Zone": "B", "cp,e": cp_B, "Description": f"Side Suction{funnelling_note}"},
            {"Zone": "C", "cp,e": cp_C, "Description": f"Side Suction (Center){funnelling_note}"},
            {"Zone": "D", "cp,e": cp_D, "Description": "Windward Face"},
            {"Zone": "E", "cp,e": cp_E, "Description": "Leeward Face"}
        ]
        
        # Store results for this direction in the dictionary
        results_by_direction[direction_name] = pd.DataFrame(direction_results)
    
    return results_by_direction

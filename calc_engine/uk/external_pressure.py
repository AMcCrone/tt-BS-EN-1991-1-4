# calc_engine/uk/external_pressure.py

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

def display_funnelling_inputs():
    """Display inputs for funnelling effect calculations"""
    st.subheader("Building Proximity (Funnelling)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        north_gap = st.number_input("North Gap [m]", 
                                  min_value=0.0, 
                                  value=st.session_state.inputs.get("north_gap", 10.0),
                                  help="Distance to nearest building from North face")
        
        south_gap = st.number_input("South Gap [m]", 
                                  min_value=0.0, 
                                  value=st.session_state.inputs.get("south_gap", 10.0),
                                  help="Distance to nearest building from South face")
    
    with col2:
        east_gap = st.number_input("East Gap [m]", 
                                 min_value=0.0, 
                                 value=st.session_state.inputs.get("east_gap", 10.0),
                                 help="Distance to nearest building from East face")
        
        west_gap = st.number_input("West Gap [m]", 
                                 min_value=0.0, 
                                 value=st.session_state.inputs.get("west_gap", 10.0),
                                 help="Distance to nearest building from West face")
    
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
    
    # Calculate coordinates
    building_x = [-EW_dimension/2, EW_dimension/2, EW_dimension/2, -EW_dimension/2, -EW_dimension/2]
    building_y = [-NS_dimension/2, -NS_dimension/2, NS_dimension/2, NS_dimension/2, -NS_dimension/2]
    
    # Create the figure
    fig = go.Figure()
    
    # Main building
    fig.add_trace(go.Scatter(
        x=building_x,
        y=building_y,
        fill="toself",
        fillcolor=TT_MidBlue,
        line=dict(color=TT_DarkBlue, width=2),
        name="Main Building"
    ))
    
    # Add surrounding buildings if they exist
    adjacent_size = 10  # Size of adjacent buildings for visualization
    
    # North building if applicable
    if north_gap < 50:  # Only show if relatively close
        north_building_x = [-EW_dimension/2-adjacent_size, EW_dimension/2+adjacent_size, 
                         EW_dimension/2+adjacent_size, -EW_dimension/2-adjacent_size, -EW_dimension/2-adjacent_size]
        north_building_y = [NS_dimension/2+north_gap, NS_dimension/2+north_gap,
                         NS_dimension/2+north_gap+adjacent_size, NS_dimension/2+north_gap+adjacent_size, 
                         NS_dimension/2+north_gap]
        fig.add_trace(go.Scatter(
            x=north_building_x,
            y=north_building_y,
            fill="toself",
            fillcolor=TT_Grey,
            opacity=0.7,
            line=dict(color=TT_Grey, width=1),
            name="North Building"
        ))

    # South building if applicable
    if south_gap < 50:
        south_building_x = [-EW_dimension/2-adjacent_size, EW_dimension/2+adjacent_size, 
                          EW_dimension/2+adjacent_size, -EW_dimension/2-adjacent_size, -EW_dimension/2-adjacent_size]
        south_building_y = [-NS_dimension/2-south_gap, -NS_dimension/2-south_gap,
                          -NS_dimension/2-south_gap-adjacent_size, -NS_dimension/2-south_gap-adjacent_size, 
                          -NS_dimension/2-south_gap]
        fig.add_trace(go.Scatter(
            x=south_building_x,
            y=south_building_y,
            fill="toself",
            fillcolor=TT_Grey,
            opacity=0.7,
            line=dict(color=TT_Grey, width=1),
            name="South Building"
        ))

    # East building if applicable
    if east_gap < 50:
        east_building_x = [EW_dimension/2+east_gap, EW_dimension/2+east_gap+adjacent_size, 
                         EW_dimension/2+east_gap+adjacent_size, EW_dimension/2+east_gap, EW_dimension/2+east_gap]
        east_building_y = [-NS_dimension/2-adjacent_size, -NS_dimension/2-adjacent_size,
                         NS_dimension/2+adjacent_size, NS_dimension/2+adjacent_size, -NS_dimension/2-adjacent_size]
        fig.add_trace(go.Scatter(
            x=east_building_x,
            y=east_building_y,
            fill="toself",
            fillcolor=TT_Grey,
            opacity=0.7,
            line=dict(color=TT_Grey, width=1),
            name="East Building"
        ))

    # West building if applicable
    if west_gap < 50:
        west_building_x = [-EW_dimension/2-west_gap, -EW_dimension/2-west_gap-adjacent_size, 
                          -EW_dimension/2-west_gap-adjacent_size, -EW_dimension/2-west_gap, -EW_dimension/2-west_gap]
        west_building_y = [-NS_dimension/2-adjacent_size, -NS_dimension/2-adjacent_size,
                          NS_dimension/2+adjacent_size, NS_dimension/2+adjacent_size, -NS_dimension/2-adjacent_size]
        fig.add_trace(go.Scatter(
            x=west_building_x,
            y=west_building_y,
            fill="toself",
            fillcolor=TT_Grey,
            opacity=0.7,
            line=dict(color=TT_Grey, width=1),
            name="West Building"
        ))
    
    # Highlight the gap with orange if funnelling occurs
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
        if e/4 <= gap <= e:
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
            
            fig.add_trace(go.Scatter(
                x=x,
                y=y,
                fill="toself",
                fillcolor=TT_Orange,
                opacity=0.3,
                line=dict(color=TT_Orange, width=1),
                name=f"{direction} Funnelling Zone"
            ))
    
    # Layout settings
    fig.update_layout(
        title="Building Layout (Plan View)",
        xaxis_title="East-West Direction [m]",
        yaxis_title="North-South Direction [m]",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        autosize=False,
        width=600,
        height=500,
        margin=dict(l=50, r=50, b=50, t=50),
    )
    
    # Make sure axes are equal scale
    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )
    
    st.plotly_chart(fig)

def calculate_cpe_uk(wind_direction, elevation_face=None):
    """
    Calculate external pressure coefficients (cp,e) for UK projects
    
    Parameters:
    - wind_direction: Direction of wind (N, S, E, W)
    - elevation_face: Face being analyzed (N, S, E, W)
    
    Returns:
    - DataFrame of cp,e values for different zones
    """
    h = st.session_state.inputs.get("z", 10.0)  # Building height
    NS_dimension = st.session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = st.session_state.inputs.get("EW_dimension", 40.0)
    
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
    
    # Check if funnelling applies
    funnelling_factor = 0.0  # No funnelling by default
    if e/4 <= gap <= e:
        # Linear interpolation for funnelling effect
        # When gap = e/4, max funnelling (factor = 1.0)
        # When gap = e, no funnelling (factor = 0.0)
        funnelling_factor = (e - gap) / (e - e/4)
        
        # Apply funnelling effect (increase absolute value of pressure coefficients by up to 1.2)
        if funnelling_factor > 0:
            # Increase magnitude of negative coefficients for suction zones
            cp_A = cp_A - 1.2 * funnelling_factor
            cp_B = cp_B - 1.2 * funnelling_factor
            cp_C = cp_C - 1.2 * funnelling_factor
            # For positive pressure on windward face
            cp_D = cp_D + 1.2 * funnelling_factor
            # For negative pressure on leeward face
            cp_E = cp_E - 1.2 * funnelling_factor
    
    # Create DataFrame of results
    results = pd.DataFrame({
        'Zone': ['A', 'B', 'C', 'D', 'E'],
        'cp,e': [cp_A, cp_B, cp_C, cp_D, cp_E],
        'Description': ['Side Suction (Edge)', 'Side Suction', 'Side Suction (Center)', 
                      'Windward Face', 'Leeward Face']
    })
    
    return results

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
    
    # Determine plot size based on building dimensions and gaps
    # Add a margin factor to ensure everything fits nicely
    margin_factor = 1.2
    max_north = NS_dimension/2 + north_gap * margin_factor
    max_south = NS_dimension/2 + south_gap * margin_factor
    max_east = EW_dimension/2 + east_gap * margin_factor
    max_west = EW_dimension/2 + west_gap * margin_factor
    
    # Set plot boundaries based on the maximum extents in each direction
    plot_size_x = max(max_east, max_west) * 1.5
    plot_size_y = max(max_north, max_south) * 1.5
    
    # Create the figure
    fig = go.Figure()
    
    # Define adjacent building sizes
    # Width of adjacent buildings is proportional to the main building dimension
    north_building_height = max(north_gap * 0.8, 5)  # Height of north building
    south_building_height = max(south_gap * 0.8, 5)  # Height of south building
    east_building_width = max(east_gap * 0.8, 5)     # Width of east building
    west_building_width = max(west_gap * 0.8, 5)     # Width of west building
    
    # Add the four surrounding buildings as individual rectangular shapes
    # North building
    north_x = [-EW_dimension/2 - west_gap/2, EW_dimension/2 + east_gap/2, 
              EW_dimension/2 + east_gap/2, -EW_dimension/2 - west_gap/2, -EW_dimension/2 - west_gap/2]
    north_y = [NS_dimension/2 + north_gap, NS_dimension/2 + north_gap,
              NS_dimension/2 + north_gap + north_building_height, 
              NS_dimension/2 + north_gap + north_building_height, NS_dimension/2 + north_gap]
    
    # South building
    south_x = [-EW_dimension/2 - west_gap/2, EW_dimension/2 + east_gap/2, 
              EW_dimension/2 + east_gap/2, -EW_dimension/2 - west_gap/2, -EW_dimension/2 - west_gap/2]
    south_y = [-NS_dimension/2 - south_gap - south_building_height, -NS_dimension/2 - south_gap - south_building_height,
              -NS_dimension/2 - south_gap, -NS_dimension/2 - south_gap, -NS_dimension/2 - south_gap - south_building_height]
    
    # East building
    east_x = [EW_dimension/2 + east_gap, EW_dimension/2 + east_gap + east_building_width, 
             EW_dimension/2 + east_gap + east_building_width, EW_dimension/2 + east_gap, EW_dimension/2 + east_gap]
    east_y = [-NS_dimension/2 - south_gap/2, -NS_dimension/2 - south_gap/2,
             NS_dimension/2 + north_gap/2, NS_dimension/2 + north_gap/2, -NS_dimension/2 - south_gap/2]
    
    # West building
    west_x = [-EW_dimension/2 - west_gap - west_building_width, -EW_dimension/2 - west_gap, 
             -EW_dimension/2 - west_gap, -EW_dimension/2 - west_gap - west_building_width, -EW_dimension/2 - west_gap - west_building_width]
    west_y = [-NS_dimension/2 - south_gap/2, -NS_dimension/2 - south_gap/2,
             NS_dimension/2 + north_gap/2, NS_dimension/2 + north_gap/2, -NS_dimension/2 - south_gap/2]
    
    # Add the surrounding buildings to the plot
    buildings_data = [
        (north_x, north_y, "North Building"),
        (south_x, south_y, "South Building"),
        (east_x, east_y, "East Building"),
        (west_x, west_y, "West Building")
    ]
    
    for x_coords, y_coords, name in buildings_data:
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords,
            fill="toself",
            fillcolor=TT_LightGrey,
            line=dict(color=TT_Grey, width=1),
            name=name,
            hoverinfo="text",
            hovertext=name,
            mode="lines"
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
        mode="lines"
    ))
    
    # Add building labels - position them better to avoid overlap
    # Adaptive positioning based on building size and gaps
    labels_data = [
        (0, NS_dimension/2 + north_gap + north_building_height/2, "North Building"),
        (0, -NS_dimension/2 - south_gap - south_building_height/2, "South Building"),
        (EW_dimension/2 + east_gap + east_building_width/2, 0, "East Building"),
        (-EW_dimension/2 - west_gap - west_building_width/2, 0, "West Building")
    ]
    
    for x, y, text in labels_data:
        fig.add_annotation(
            x=x, y=y,
            text=text,
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
                mode="lines"
            ))
            
            # Add a funnelling effect label - improved positioning to prevent overlap
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
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=TT_Orange,
                borderwidth=1,
                borderpad=4
            )
    
    # Calculate optimal range for axes to ensure everything is visible
    x_range = [-plot_size_x, plot_size_x]
    y_range = [-plot_size_y, plot_size_y]
    
    # Layout settings with dynamic sizing
    fig.update_layout(
        title="Building Layout (Plan View)",
        showlegend=False,
        autosize=False,
        width=600,
        height=500,
        margin=dict(l=50, r=50, b=50, t=50),
        xaxis=dict(range=x_range),
        yaxis=dict(range=y_range)
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
    Calculate external pressure coefficients (cp,e) for building elevations (N, E, S, W)
    considering funnelling effects for all wind directions
    
    Returns:
    - Dictionary of DataFrames of cp,e values for different elevations
    """
    h = st.session_state.inputs.get("z", 10.0)  # Building height
    NS_dimension = st.session_state.inputs.get("NS_dimension", 20.0)
    EW_dimension = st.session_state.inputs.get("EW_dimension", 40.0)
    
    # Create results dictionary for each elevation
    elevations = ["North", "South", "East", "West"]
    results_by_elevation = {elevation: [] for elevation in elevations}
    
    # For each elevation, calculate cp,e values based on wind hitting that elevation
    for elevation in elevations:
        # Define dimensions based on elevation orientation
        if elevation in ["North", "South"]:
            b = EW_dimension  # Width of the elevation perpendicular to wind
            d = NS_dimension  # Depth of building parallel to wind
        else:  # East or West
            b = NS_dimension  # Width of the elevation perpendicular to wind
            d = EW_dimension  # Depth of building parallel to wind
        
        # Calculate h/d ratio
        h_d_ratio = h / d
        
        # Interpolate cp,e values based on h/d ratio
        # Values from BS EN 1991-1-4 Table 7.1
        h_d_points = [0.25, 1.0, 5.0]
        
        # Base values for each zone at different h/d ratios
        zone_A_values = [-1.2, -1.2, -1.2]
        zone_B_values = [-0.8, -0.8, -0.8]
        zone_C_values = [-0.5, -0.5, -0.5]
        zone_D_values = [0.7, 0.8, 0.8]  # Updated for h/d <= 0.25, D = 0.7
        
        # Linear interpolation for h/d ratio
        if h_d_ratio <= 0.25:
            cp_A = zone_A_values[0]
            cp_B = zone_B_values[0]
            cp_C = zone_C_values[0]
            cp_D = zone_D_values[0]  # 0.7 when h/d <= 0.25
        elif h_d_ratio >= 5.0:
            cp_A = zone_A_values[2]
            cp_B = zone_B_values[2]
            cp_C = zone_C_values[2]
            cp_D = zone_D_values[2]
        else:
            # Interpolate between known points
            for i in range(len(h_d_points)-1):
                if h_d_points[i] <= h_d_ratio <= h_d_points[i+1]:
                    factor = (h_d_ratio - h_d_points[i]) / (h_d_points[i+1] - h_d_points[i])
                    cp_A = zone_A_values[i] + factor * (zone_A_values[i+1] - zone_A_values[i])
                    cp_B = zone_B_values[i] + factor * (zone_B_values[i+1] - zone_B_values[i])
                    cp_C = zone_C_values[i] + factor * (zone_C_values[i+1] - zone_C_values[i])
                    cp_D = zone_D_values[i] + factor * (zone_D_values[i+1] - zone_D_values[i])
                    break
        
        # Store original values before funnelling adjustment
        base_cp_A = cp_A
        base_cp_B = cp_B
        base_cp_C = cp_C
        
        # Check for funnelling effect based on elevation
        if elevation == "North":
            gap = st.session_state.inputs.get("north_gap", 10.0)
        elif elevation == "South":
            gap = st.session_state.inputs.get("south_gap", 10.0)
        elif elevation == "East":
            gap = st.session_state.inputs.get("east_gap", 10.0)
        else:  # "West"
            gap = st.session_state.inputs.get("west_gap", 10.0)
        
        # Calculate e (the smaller of b or 2h)
        e = min(b, 2*h)
        
        # Apply funnelling according to the guidance and graph
        has_funnelling = False
        funnelling_increase_pct_A = 0
        funnelling_increase_pct_B = 0
        funnelling_increase_pct_C = 0
        
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
                
                # Calculate with funnelling
                cp_A_with_funnel = base_cp_A + factor * (max_funnel_cp_A - base_cp_A)
                cp_B_with_funnel = base_cp_B + factor * (max_funnel_cp_B - base_cp_B)
                cp_C_with_funnel = base_cp_C + factor * (max_funnel_cp_C - base_cp_C)
                
                # Calculate percentage increase (negative values, so using absolute difference)
                funnelling_increase_pct_A = (abs(cp_A_with_funnel) - abs(base_cp_A)) / abs(base_cp_A) * 100
                funnelling_increase_pct_B = (abs(cp_B_with_funnel) - abs(base_cp_B)) / abs(base_cp_B) * 100
                funnelling_increase_pct_C = (abs(cp_C_with_funnel) - abs(base_cp_C)) / abs(base_cp_C) * 100
                
                # Update values with funnelling
                cp_A = cp_A_with_funnel
                cp_B = cp_B_with_funnel
                cp_C = cp_C_with_funnel
                
            else:
                # Interpolate between e/2 and e (decreasing effect)
                # At e/2: maximum funnelling values
                # At e: original values
                factor = (e - gap) / (e/2)  # 1 at e/2, 0 at e
                
                # Calculate with funnelling
                cp_A_with_funnel = base_cp_A + factor * (max_funnel_cp_A - base_cp_A)
                cp_B_with_funnel = base_cp_B + factor * (max_funnel_cp_B - base_cp_B)
                cp_C_with_funnel = base_cp_C + factor * (max_funnel_cp_C - base_cp_C)
                
                # Calculate percentage increase (negative values, so using absolute difference)
                funnelling_increase_pct_A = (abs(cp_A_with_funnel) - abs(base_cp_A)) / abs(base_cp_A) * 100
                funnelling_increase_pct_B = (abs(cp_B_with_funnel) - abs(base_cp_B)) / abs(base_cp_B) * 100
                funnelling_increase_pct_C = (abs(cp_C_with_funnel) - abs(base_cp_C)) / abs(base_cp_C) * 100
                
                # Update values with funnelling
                cp_A = cp_A_with_funnel
                cp_B = cp_B_with_funnel
                cp_C = cp_C_with_funnel
        
        # Create result entries for this elevation
        funnelling_note_A = f" (+{funnelling_increase_pct_A:.1f}% funnelling)" if has_funnelling and funnelling_increase_pct_A > 0 else ""
        funnelling_note_B = f" (+{funnelling_increase_pct_B:.1f}% funnelling)" if has_funnelling and funnelling_increase_pct_B > 0 else ""
        funnelling_note_C = f" (+{funnelling_increase_pct_C:.1f}% funnelling)" if has_funnelling and funnelling_increase_pct_C > 0 else ""
        
        elevation_results = [
            {"Zone": "A", "cp,e": cp_A, "Description": f"Side Suction (Edge){funnelling_note_A}"},
            {"Zone": "B", "cp,e": cp_B, "Description": f"Side Suction{funnelling_note_B}"},
            {"Zone": "C", "cp,e": cp_C, "Description": f"Side Suction (Center){funnelling_note_C}"},
            {"Zone": "D", "cp,e": cp_D, "Description": "Windward Face"}
        ]
        
        # Store results for this elevation in the dictionary
        results_by_elevation[elevation] = pd.DataFrame(elevation_results)
    
    return results_by_elevation

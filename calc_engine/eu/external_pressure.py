# calc_engine/eu/external_pressure.py

import numpy as np
import pandas as pd
import streamlit as st

def calculate_cpe_eu(wind_direction, elevation_face=None):
    """
    Calculate external pressure coefficients (cp,e) for EU projects
    
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
    # Values from BS EN 1991-1-4 for cp,e10 (first column of each zone)
    h_d_points = [0.25, 1.0, 5.0]
    
    # Base values for each zone at different h/d ratios
    zone_A_values = [-1.2, -1.2, -1.2]
    zone_B_values = [-0.8, -0.8, -0.8]
    zone_C_values = [-0.5, -0.5, -0.5]
    zone_D_values = [0.7, 0.8, 0.9]  # Windward - increases with h/d
    zone_E_values = [-0.3, -0.5, -0.7]  # Leeward - increases (in magnitude) with h/d
    
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
    
    # Create DataFrame of results
    results = pd.DataFrame({
        'Zone': ['A', 'B', 'C', 'D', 'E'],
        'cp,e': [cp_A, cp_B, cp_C, cp_D, cp_E],
        'Description': ['Side Suction (Edge)', 'Side Suction', 'Side Suction (Center)', 
                      'Windward Face', 'Leeward Face']
    })
    
    return results

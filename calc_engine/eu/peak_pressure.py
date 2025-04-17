import math

def calculate_qp(z, terrain_category, v_b, rho_air=1.25, c_o=1.0):
    """
    Calculate the peak velocity pressure q_p(z) for a given height z and terrain category,
    based on the EU standard (BS EN 1991-1-4).
    
    The peak velocity pressure q_p(z) is calculated as:
    q_p(z) = [1 + 7 * I_v(z)] * 0.5 * rho * v_m^2(z)
    
    where:
    - I_v(z) is the turbulence intensity
    - rho is the air density (typically 1.25 kg/m³)
    - v_m(z) is the mean wind velocity
    
    Parameters:
    -----------
    z : float
        Height above ground (in m)
    terrain_category : str
        The terrain category identifier. Valid options are '0', 'I', 'II', 'III', or 'IV'.
    v_b : float
        Basic wind velocity (in m/s)
    rho_air : float, optional
        Air density (in kg/m³), default is 1.25
    c_o : float, optional
        Orography factor, default is 1.0
    
    Returns:
    --------
    q_p : float
        The peak velocity pressure at height z (in N/m²)
    """
    # Define terrain parameters for each category
    terrain_params = {
        '0': {'z0': 0.003, 'z_min': 1},
        'I': {'z0': 0.01, 'z_min': 1},
        'II': {'z0': 0.05, 'z_min': 2},
        'III': {'z0': 0.3, 'z_min': 5},
        'IV': {'z0': 1.0, 'z_min': 10},
    }
    
    # Ensure terrain_category is a string and in correct form for lookup
    terrain_category = str(terrain_category).strip()
    if terrain_category not in terrain_params:
        raise ValueError("Invalid terrain category. Must be one of: 0, I, II, III, IV.")
    
    # Retrieve the roughness length and the minimum height for the selected category
    z0 = terrain_params[terrain_category]['z0']
    z_min = terrain_params[terrain_category]['z_min']
    
    # Calculate the terrain factor k_r using Equation (4.5)
    z0_II = 0.05  # roughness length for terrain category II as reference
    k_r = 0.19 * (z0 / z0_II) ** 0.07
    
    # Calculate roughness factor c_r(z)
    if z < z_min:
        # For z below the minimum height, use the value at z_min
        c_r = k_r * math.log(z_min / z0)
    else:
        # For z between z_min and z_max (and above), use the logarithmic formula
        c_r = k_r * math.log(z / z0)
    
    # Calculate the mean wind velocity v_m(z)
    v_m = v_b * c_r * c_o
    
    # Calculate the turbulence intensity I_v(z)
    k_I = 1.0  # turbulence factor (default value is 1.0)
    
    if z < z_min:
        I_v = k_I / (c_o * math.log(z_min / z0))
    else:
        I_v = k_I / (c_o * math.log(z / z0))
    
    # Calculate the peak velocity pressure q_p(z)
    q_p = (1 + 7 * I_v) * 0.5 * rho_air * (v_m ** 2)
    
    return q_p

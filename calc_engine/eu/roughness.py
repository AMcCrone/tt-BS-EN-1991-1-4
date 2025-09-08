import math
import streamlit as st

def calculate_crz(z, terrain_category):
    """
    Calculate the roughness factor c_r(z) for a given height z and terrain category,
    based on the EU standard (BS EN 1991-1-4).

    Table 4.1 - Terrain categories and parameters:
        Terrain Category 0: Sea or coastal areas exposed to open sea
             z0   = 0.003 m,  z_min = 1 m
        Terrain Category I: Lakes or flat areas with negligible vegetation
             z0   = 0.01 m,   z_min = 1 m
        Terrain Category II: Areas with low vegetation (e.g., grass, isolated obstacles)
             z0   = 0.05 m,   z_min = 2 m
        Terrain Category III: Areas with regular cover of vegetation or buildings
             z0   = 0.3 m,    z_min = 5 m
        Terrain Category IV: Areas with at least 15% of surface covered by buildings
             z0   = 1.0 m,    z_min = 10 m

    Equations and definitions:
      For z_min ≤ z ≤ z_max (with z_max = 200 m):
          c_r(z) = k_t · ln(z / z0)
      For z < z_min:
          c_r(z) = c_r(z_min)

      The terrain factor k_t is calculated as:
          k_t = 0.19 · (z0 / z0_II)^0.07
      where the reference roughness length for Terrain Category II is:
          z0_II = 0.05 m

    Parameters:
    -----------
    z : float
        Height above ground (in m). This value comes from the session state in main.py.
    terrain_category : str or int
        The terrain category identifier. Valid options are '0', 'I', 'II', 'III', or 'IV'.

    Returns:
    --------
    c_rz : float
        The roughness factor at height z.
    """

    # Define terrain parameters for each category
    terrain_params = {
        '0': {'z0': 0.003, 'z_min': 1},
        'I': {'z0': 0.01, 'z_min': 1},
        'II': {'z0': 0.05, 'z_min': 2},
        'III': {'z0': 0.3, 'z_min': 5},
        'IV': {'z0': 1.0, 'z_min': 10},
    }

    # Ensure terrain_category is a string and in uppercase form for lookup.
    terrain_category = str(terrain_category).strip()
    if terrain_category not in terrain_params:
        raise ValueError("Invalid terrain category. Must be one of: 0, I, II, III, IV.")

    # Retrieve the roughness length and the minimum height for the selected category.
    z0 = terrain_params[terrain_category]['z0']
    z_min = terrain_params[terrain_category]['z_min']
    z_max = 200.0  # maximum height to which the formula applies

    # Calculate the terrain factor k_t using Equation (4.5)
    z0_II = 0.05  # roughness length for terrain category II as reference
    k_t = 0.19 * (z0 / z0_II) ** 0.07

    # Calculate c_r(z)
    if z < z_min:
        # For z below the minimum height, use the value at z_min
        c_rz = k_t * math.log(z_min / z0)
    else:
        # For z between z_min and z_max (and above), use the logarithmic formula.
        c_rz = k_t * math.log(z / z0)

    return c_rz

def display_eu_roughness_calculation(st, z_minus_h_dis, terrain_category):
    """Display EU roughness calculation with explanation.
    
    Args:
        st: Streamlit object
        z_minus_h_dis: Effective height
        terrain_category: The terrain category
        
    Returns:
        float: The calculated roughness factor
    """
    # Calculate roughness factor using your existing function
    c_rz = calculate_crz(z_minus_h_dis, terrain_category)
    
    # Store in session state
    st.session_state.inputs["c_rz"] = c_rz
    
    # Get terrain parameters for explanation
    terrain_params = {
        '0': {'z0': 0.003, 'z_min': 1},
        'I': {'z0': 0.01, 'z_min': 1},
        'II': {'z0': 0.05, 'z_min': 2},
        'III': {'z0': 0.3, 'z_min': 5},
        'IV': {'z0': 1.0, 'z_min': 10},
    }
    z0 = terrain_params[terrain_category]['z0']
    z_min = terrain_params[terrain_category]['z_min']
    z0_II = 0.05
    kr = 0.19 * (z0 / z0_II) ** 0.07
    
    # Display explanation and results
    st.markdown("#### Roughness Factor $C_r(z)$")
    
    st.write(f"Roughness length $z_0 = {z0:.3f}$ m")
    st.write(f"Minimum height $z_{{min}} = {z_min}$ m")
    st.write(f"Terrain factor $k_r = 0.19 \\cdot (\\frac{{z_0}}{{z_{{0,II}}}})^{{0.07}} = 0.19 \\cdot (\\frac{{{z0:.3f}}}{{{z0_II}}})^{{0.07}} = {kr:.3f}$")
    st.write(f"For terrain category **{terrain_category}** and height **{z_minus_h_dis:.2f} m**")
    # Show appropriate formula based on height comparison
    if z_minus_h_dis < z_min:
        st.latex(f"c_r(z) = k_r \\cdot \\ln(\\frac{{z_{{min}}}}{{z_0}}) = {kr:.3f} \\cdot \\ln(\\frac{{{z_min}}}{{{z0:.3f}}}) = {c_rz:.3f}")
    else:
        st.latex(f"c_r(z) = k_r \\cdot \\ln(\\frac{{z}}{{z_0}}) = {kr:.3f} \\cdot \\ln(\\frac{{{z_minus_h_dis:.2f}}}{{{z0:.3f}}}) = {c_rz:.3f}")
    
    return c_rz

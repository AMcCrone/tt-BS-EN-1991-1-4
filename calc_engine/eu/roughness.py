import math

def calculate_cr(z, terrain_category):
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
    c_r : float
        The roughness factor at height z.
    """

    # Define terrain parameters for each category
    terrain_params = {
        '0 - Sea or coastal area exposed to the open sea': {'z0': 0.003, 'z_min': 1},
        'I - Lakes or flat and horizontal area with negligible vegetation': {'z0': 0.01, 'z_min': 1},
        'II - Area with low vegetation and isolated obstacles': {'z0': 0.05, 'z_min': 2},
        'III - Area with regular cover of vegetation or buildings': {'z0': 0.3, 'z_min': 5},
        'IV - Area where at least 15% of surface is covered with buildings': {'z0': 1.0, 'z_min': 10},
    }

    # Ensure terrain_category is a string and in uppercase form for lookup.
    terrain_category = str(terrain_category).strip().upper()
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
        c_r = k_t * math.log(z_min / z0)
    else:
        # For z between z_min and z_max (and above), use the logarithmic formula.
        c_r = k_t * math.log(z / z0)

    return c_r

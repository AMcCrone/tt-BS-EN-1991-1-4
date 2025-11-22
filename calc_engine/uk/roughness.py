import streamlit as st
from calc_engine.uk.plot_display import display_contour_plot_with_override

def calculate_uk_roughness(st, datasets):
    """Calculate the roughness factor for UK region.
    
    Args:
        st: Streamlit object
        datasets: Loaded contour data
        
    Returns:
        float: The calculated roughness factor
    """
    # Get necessary parameters from session state
    z_minus_h_dis = st.session_state.inputs.get("z_minus_h_dis", 10.0)
    d_sea = st.session_state.inputs.get("d_sea", 60.0)
    terrain = st.session_state.inputs.get("terrain_category", "").lower()
    
    # Calculate roughness factor from NA.3 plot
    c_rz = display_contour_plot_with_override(
        st, 
        datasets, 
        "NA.3", 
        d_sea, 
        z_minus_h_dis, 
        "Town Roughness Factor $c_r(z)$", 
        "c_r(z)", 
        "c_rz"
    )
    
    # If terrain is town, apply additional correction factor
    if terrain == "town":
        d_town_terrain = st.session_state.inputs.get("d_town_terrain", 5.0)
        
        c_rT = display_contour_plot_with_override(
            st, 
            datasets, 
            "NA.4", 
            d_town_terrain, 
            z_minus_h_dis, 
            "Town Roughness Factor $c_{r,T}$", 
            "c_{r,T}", 
            "c_rT"
        )
        # Calculate the combined roughness factor
        c_rz = c_rT * c_rz
        # Show combined result with LaTeX
        st.latex(f"c_r(z) = c_{{r,T}} \\cdot c_r(z) = {c_rT:.3f} \\cdot {c_rz/c_rT:.3f} = {c_rz:.3f}")
    
    return c_rz

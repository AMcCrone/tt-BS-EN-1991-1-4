import math
import streamlit as st
from calc_engine.uk.plot_display import display_contour_plot_with_override
from calc_engine.common.util import get_session_value, store_session_value

def calculate_uk_peak_pressure(st, datasets, q_b):
    """Calculate peak velocity pressure according to UK standard.
    
    Args:
        st: Streamlit object
        datasets: Loaded contour data
        q_b: Basic wind pressure
        
    Returns:
        float: The calculated peak pressure
    """
    # User options
    is_orography_significant = st.checkbox("Orography is significant", value=False)
    # Retrieve inputs from session state
    z_minus_h_dis = get_session_value(st, "z_minus_h_dis", 10.0)
    d_sea = get_session_value(st, "d_sea", 60.0)
    terrain = get_session_value(st, "terrain_category", "").lower()
    
    if is_orography_significant:
        # NA.5 approach for significant orography       
        # Display plot and get interpolated value
        factor = display_contour_plot_with_override(
            st, 
            datasets, 
            "NA.5", 
            d_sea, 
            z_minus_h_dis, 
            "Turbulence Intensity $I_{v}(z)$", 
            "I_v(z)", 
            "i_v"
        )
        
        # Apply additional correction for UK town terrain with significant orography
        if terrain == "town":            
            # Display plot and get interpolated NA.6 value
            d_town_terrain = get_session_value(st, "d_town_terrain", 5.0)
            k_IT = display_contour_plot_with_override(
                st, 
                datasets, 
                "NA.6", 
                d_town_terrain, 
                z_minus_h_dis, 
                "Terrain Orography Correction Factor", 
                "Turbulence Correction Factor $k_{I,T}$", 
                "k_IT"
            )
            
            # Calculate peak pressure with NA.6 correction
            qp_value = factor * k_IT * q_b
            store_session_value(st, "qp_value", qp_value)
            
            # Display result with equation
            st.write(f"Peak velocity pressure: $q_p(z) = q_b \\cdot I_v(z) \\cdot \\text{{NA.6}} = {q_b:.2f} \\cdot {factor:.3f} \\cdot {k_IT:.3f} = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
        else:
            # Calculate peak pressure without NA.6 correction
            qp_value = factor * q_b
            store_session_value(st, "qp_value", qp_value)
            
            # Display result with equation
            st.write(f"Peak velocity pressure: $q_p(z) = q_b \\cdot I_v(z) = {q_b:.2f} \\cdot {factor:.3f} = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
    
    else:
        # Standard approach using exposure factors
        # Get height factor from NA.7
        c_ez = display_contour_plot_with_override(
            st, 
            datasets, 
            "NA.7", 
            d_sea, 
            z_minus_h_dis, 
            "Exposure Factor $C_{e}(z)$", 
            "C_e(z)", 
            "c_ez"
        )
        
        formula = f"q_p(z) = q_b \\cdot C_e(z) = {q_b:.2f} \\cdot {c_ez:.3f}"
        
        # Apply town correction if needed
        if terrain == "town":
            d_town_terrain = get_session_value(st, "d_town_terrain", 5.0)
            
            # Get town factor from NA.8
            c_eT = display_contour_plot_with_override(
                st, 
                datasets, 
                "NA.8", 
                d_town_terrain, 
                z_minus_h_dis, 
                "Exposure Factor Correction $C_{e,T}$", 
                "C_{e,T}", 
                "c_eT"
            )
            
            # Calculate with town correction
            qp_value = q_b * c_ez * c_eT
            formula += f" \\cdot {c_eT:.3f}"
        else:
            # Calculate without town correction
            qp_value = q_b * c_ez
        
        # Store result and display
        store_session_value(st, "qp_value", qp_value)
        st.write(f"Peak velocity pressure: ${formula} = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
    
    return qp_value

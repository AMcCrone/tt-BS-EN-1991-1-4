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
    
    # Get height value from session state
    z = st.session_state.inputs.get("z", 30.0)
    
    if is_orography_significant:
        # Get NA.7 - Exposure Factor - Used in calculations for z ≤ 50m
        c_ez = display_contour_plot_with_override(
            st, 
            datasets, 
            "NA.7", 
            d_sea, 
            z_minus_h_dis, 
            "Exposure Factor $c_{e}(z)$", 
            "c_e(z)", 
            "c_ez"
        )
        
        # Get orography factor from session state
        c_oz = get_session_value(st, "c_oz", 1.0)
        
        if z > 50:
            # For z > 50m, we need turbulence intensity
            i_vz = display_contour_plot_with_override(
                st, 
                datasets, 
                "NA.5", 
                d_sea, 
                z_minus_h_dis, 
                "Turbulence Intensity $I_{v}(z)$", 
                "I_v(z)", 
                "i_v"
            )
        
        if terrain == "town":
            # Get town parameters for town terrain
            d_town_terrain = get_session_value(st, "d_town_terrain", 5.0)
            
            # Get NA.8 - Town correction - Used in all town calculations
            c_eT = display_contour_plot_with_override(
                st, 
                datasets, 
                "NA.8", 
                d_town_terrain, 
                z_minus_h_dis, 
                "Exposure Factor Correction $c_{e,T}$", 
                "c_{e,T}", 
                "c_eT"
            )
            
            if z > 50:
                # Only need turbulence correction for z > 50
                k_IT = display_contour_plot_with_override(
                    st, 
                    datasets, 
                    "NA.6", 
                    d_town_terrain, 
                    z_minus_h_dis, 
                    "Turbulence Correction Factor $k_{I,T}$", 
                    "k_{I,T}", 
                    "k_IT"
                )
                
                # Apply town correction to turbulence intensity
                i_vz = i_vz * k_IT
                st.write(f"Corrected turbulence intensity: $I_v(z) = I_v(z) \\cdot k_{{I,T}} = {i_vz:.3f}$")
            
            # Calculate peak pressure with different formulas based on height
            if z <= 50:
                # Calculate with formula for z <= 50 with town correction
                qp_value = c_ez * c_eT * q_b * ((c_oz + 0.6) / 1.6) ** 2
                
                # Display result with equation
                st.write(f"z ≤ 50m: $q_p(z) = c_e(z) \\cdot c_{{e,T}} \\cdot q_b \\cdot ((c_o(z) + 0.6) / 1.6)^2 = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
            else:
                # Get air density and mean velocity from session state
                rho = get_session_value(st, "rho_air", 1.25)
                v_m = get_session_value(st, "v_mean", 0.0)
                
                # Calculate with formula for z > 50
                qp_value = (1 + 3 * i_vz) ** 2 * 0.5 * rho * (v_m ** 2)
                
                # Display result with equation
                st.write(f"z > 50m: $q_p(z) = (1 + 3 \\cdot I_v(z))^2 \\cdot 0.5 \\cdot \\rho \\cdot v_m^2 = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
                
                # Apply town correction
                qp_value = qp_value * c_eT
                st.write(f"With town correction: $q_p(z) = {qp_value:.2f} \\cdot {c_eT:.3f} = {qp_value * c_eT:.2f}\\;\\mathrm{{N/m^2}}$")
        else:
            # For non-town terrain with significant orography
            if z <= 50:
                # Calculate with formula for z <= 50
                qp_value = c_ez * q_b * ((c_oz + 0.6) / 1.6) ** 2
                
                # Display result with equation
                st.write(f"z ≤ 50m: $q_p(z) = c_e(z) \\cdot q_b \\cdot ((c_o(z) + 0.6) / 1.6)^2 = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
            else:
                # Get air density and mean velocity from session state
                rho = get_session_value(st, "rho_air", 1.25)
                v_m = get_session_value(st, "v_mean", 0.0)
                
                # Calculate with formula for z > 50
                qp_value = (1 + 3 * i_vz) ** 2 * 0.5 * rho * (v_m ** 2)
                
                # Display result with equation
                st.write(f"z > 50m: $q_p(z) = (1 + 3 \\cdot I_v(z))^2 \\cdot 0.5 \\cdot \\rho \\cdot v_m^2 = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
    else:
        # Standard approach when orography is not significant
        # Get NA.7 - Exposure Factor
        c_ez = display_contour_plot_with_override(
            st, 
            datasets, 
            "NA.7", 
            d_sea, 
            z_minus_h_dis, 
            "Exposure Factor $c_{e}(z)$", 
            "c_e(z)", 
            "c_ez"
        )
        
        if terrain == "town":
            d_town_terrain = get_session_value(st, "d_town_terrain", 5.0)
            
            # Get town factor from NA.8
            c_eT = display_contour_plot_with_override(
                st, 
                datasets, 
                "NA.8", 
                d_town_terrain, 
                z_minus_h_dis, 
                "Exposure Factor Correction $c_{e,T}$", 
                "c_{e,T}", 
                "c_eT"
            )
            
            # Calculate with town correction
            qp_value = q_b * c_ez * c_eT
            
            # Display result with formula
            st.write(f"$q_p(z) = q_b \\cdot c_e(z) \\cdot c_{{e,T}} = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
        else:
            # Calculate without town correction
            qp_value = q_b * c_ez
            
            # Display result with formula
            st.write(f"$q_p(z) = q_b \\cdot c_e(z) = {qp_value:.2f}\\;\\mathrm{{N/m^2}}$")
    
    # Store the result in session state
    store_session_value(st, "qp_value", qp_value)
    
    return qp_value

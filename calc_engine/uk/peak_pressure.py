import math
import streamlit as st
from calc_engine.uk.plot_display import display_contour_plot_with_override


def calculate_uk_peak_pressure_no_orography(st, datasets, q_b, d_sea, z_minus_h_dis, terrain):
    """Calculate peak pressure when orography is NOT significant.
    
    This follows the 'N' path in the flowchart - simple calculation.
    
    Args:
        st: Streamlit object
        datasets: Loaded contour data
        q_b: Basic wind pressure
        d_sea: Distance from sea
        z_minus_h_dis: Height above displacement height
        terrain: Terrain category ("town", "country", or "sea")
        
    Returns:
        float: The calculated peak pressure
    """
    # Get NA.7 - Exposure Factor (always needed)
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
    st.session_state.results["c_ez"] = c_ez
    
    if terrain == "town":
        # Town terrain - need NA.8 as well
        d_town_terrain = st.session_state.inputs.get("d_town_terrain", 5.0)
        
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
        st.session_state.results["c_eT"] = c_eT
        
        # Calculate with town correction
        q_p = q_b * c_ez * c_eT
        st.session_state.results["q_p"] = q_p
        # Display result with formula
        st.write(f"$q_p(z) = q_b \\cdot c_e(z) \\cdot c_{{e,T}} = {q_b:.2f} \\cdot {c_ez:.3f} \\cdot {c_eT:.3f} = {q_p:.2f}\\;\\mathrm{{N/m^2}}$")
    else:
        # Country/Sea terrain - simple calculation
        q_p = q_b * c_ez
        st.session_state.results["q_p"] = q_p
        # Display result with formula
        st.write(f"$q_p(z) = q_b \\cdot c_e(z) = {q_b:.2f} \\cdot {c_ez:.3f} = {q_p:.2f}\\;\\mathrm{{N/m^2}}$")
    
    return q_p


def calculate_uk_peak_pressure_with_orography(st, datasets, q_b, d_sea, z_minus_h_dis, terrain, z, c_o):
    """Calculate peak pressure when orography IS significant.
    
    This follows the 'Y' path in the flowchart - more complex calculation.
    
    Args:
        st: Streamlit object
        datasets: Loaded contour data
        q_b: Basic wind pressure
        d_sea: Distance from sea
        z_minus_h_dis: Height above displacement height
        terrain: Terrain category ("town", "country", or "sea")
        z: Height above ground
        c_o: Orography factor (already obtained from user in main.py)
        
    Returns:
        float: The calculated peak pressure
    """
    # Check height to determine which formula to use
    if z <= 50:
        # z ≤ 50m: Use simplified formula with c_e(z)
        
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
        st.session_state.results["c_ez"] = c_ez
        
        if terrain == "town":
            # Town: need both NA.7 and NA.8
            d_town_terrain = st.session_state.inputs.get("d_town_terrain", 5.0)
            
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
            st.session_state.results["c_eT"] = c_eT
            
            # Calculate with town correction
            q_p = c_ez * c_eT * q_b * ((c_o + 0.6) / 1.6) ** 2
            st.session_state.results["q_p"] = q_p
            
            st.write(f"z ≤ 50m (Town): $q_p(z) = c_e(z) \\cdot c_{{e,T}} \\cdot q_b \\cdot \\left(\\frac{{c_o(z) + 0.6}}{{1.6}}\\right)^2$")
            st.write(f"$q_p(z) = {c_ez:.3f} \\cdot {c_eT:.3f} \\cdot {q_b:.2f} \\cdot {((c_o + 0.6) / 1.6):.3f}^2 = {q_p:.2f}\\;\\mathrm{{N/m^2}}$")
        else:
            # Country/Sea: only need NA.7
            q_p = c_ez * q_b * ((c_o + 0.6) / 1.6) ** 2
            st.session_state.results["q_p"] = q_p
            
            st.write(f"z ≤ 50m: $q_p(z) = c_e(z) \\cdot q_b \\cdot \\left(\\frac{{c_o(z) + 0.6}}{{1.6}}\\right)^2$")
            st.write(f"$q_p(z) = {c_ez:.3f} \\cdot {q_b:.2f} \\cdot {((c_o + 0.6) / 1.6):.3f}^2 = {q_p:.2f}\\;\\mathrm{{N/m^2}}$")
    
    else:
        # z > 50m: Use turbulence intensity formula
        
        # Get NA.5 - Turbulence Intensity (needed for z > 50)
        i_vz = display_contour_plot_with_override(
            st, 
            datasets, 
            "NA.5", 
            d_sea, 
            z_minus_h_dis, 
            "Turbulence Intensity $I_{v}(z)_{flat}$", 
            "I_v(z)_flat", 
            "i_vz"
        )
        st.session_state.results["i_vz"] = i_vz
        
        if terrain == "town":
            # Town: need correction factors NA.6 and NA.8
            d_town_terrain = st.session_state.inputs.get("d_town_terrain", 5.0)
            
            # Get NA.6 - Turbulence Correction Factor
            k_iT = display_contour_plot_with_override(
                st, 
                datasets, 
                "NA.6", 
                d_town_terrain, 
                z_minus_h_dis, 
                "Turbulence Correction Factor $k_{I,T}$", 
                "k_{I,T}", 
                "k_iT"
            )
            st.session_state.results["k_iT"] = k_iT
            
            # Get NA.8 - Exposure Factor Correction
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
            st.session_state.results["c_eT"] = c_eT
            
            # Apply town correction to turbulence intensity
            z_corrected = z * k_iT
            st.write(f"Corrected turbulence intensity: $I_v(z) = I_v(z)_{{flat}} \\cdot k_{{I,T}} = {z:.3f} \\cdot {k_iT:.3f} = {z_corrected:.3f}$")
            
            # Get air density and mean velocity from session state
            rho = st.session_state.inputs.get("rho_air", 1.226)
            v_m = st.session_state.results.get("v_mean", 0.0)
            
            # Calculate peak pressure
            qp_base = (1 + 3 * z_corrected) ** 2 * 0.5 * rho * (v_m ** 2)
            
            st.write(f"z > 50m: $q_p(z) = (1 + 3 \\cdot I_v(z))^2 \\cdot 0.5 \\cdot \\rho \\cdot v_m^2$")
            st.write(f"$q_p(z) = (1 + 3 \\cdot {z_corrected:.3f})^2 \\cdot 0.5 \\cdot {rho:.3f} \\cdot {v_m:.2f}^2 = {qp_base:.2f}\\;\\mathrm{{N/m^2}}$")
            
            # Apply town correction
            q_p = qp_base * c_eT
            st.session_state.results["q_p"] = q_p
            st.write(f"With town correction: $q_p(z) = q_p(z) \\cdot c_{{e,T}} = {qp_base:.2f} \\cdot {c_eT:.3f} = {q_p:.2f}\\;\\mathrm{{N/m^2}}$")
        else:
            # Country/Sea: use turbulence intensity directly
            
            # Get air density and mean velocity from session state
            rho = st.session_state.inputs.get("rho_air", 1.226)
            v_m = st.session_state.results.get("v_mean", 0.0)
            
            # Calculate peak pressure
            q_p = (1 + 3 * z) ** 2 * 0.5 * rho * (v_m ** 2)
            st.session_state.results["q_p"] = q_p
            st.write(f"z > 50m: $q_p(z) = (1 + 3 \\cdot I_v(z)_{{flat}})^2 \\cdot 0.5 \\cdot \\rho \\cdot v_m^2$")
            st.write(f"$q_p(z) = (1 + 3 \\cdot {z:.3f})^2 \\cdot 0.5 \\cdot {rho:.3f} \\cdot {v_m:.2f}^2 = {q_p:.2f}\\;\\mathrm{{N/m^2}}$")
    
    return q_p

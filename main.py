import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def main():
    st.title("BS EN 1991-1-4 Wind Load Calculator")
    st.sidebar.header("Project Information")
    
    # Project and Location Information
    project_name = st.sidebar.text_input("Project Name")
    location = st.sidebar.text_input("Location")
    height_above_ground = st.sidebar.number_input("Height above ground (m)", min_value=0.0, value=10.0)
    altitude = st.sidebar.number_input("Altitude above sea level (m)", min_value=0.0, value=0.0)
    
    # Building Geometry
    st.sidebar.header("Building Geometry")
    width = st.sidebar.number_input("Elevation width (m)", min_value=0.0, value=20.0)
    height = st.sidebar.number_input("Building height (m)", min_value=0.0, value=10.0)
    depth = st.sidebar.number_input("Building depth (m)", min_value=0.0, value=15.0)
    
    # Terrain Information
    st.sidebar.header("Terrain Information")
    country = st.sidebar.selectbox("Country", ["UK", "Other European Country"])
    
    if country == "UK":
        location_type = st.sidebar.selectbox("Location Type", ["Town", "Country", "Sea"])
        uk_vb_map = st.sidebar.number_input("Vb,map from UK Map (m/s)", min_value=0.0, value=23.0)
    else:
        terrain_category = st.sidebar.selectbox("Terrain Category", ["0", "I", "II", "III", "IV"])
        vb_0 = st.sidebar.number_input("Fundamental Wind Velocity Vb,0 (m/s)", min_value=0.0, value=27.0)
    
    # Terrain & Geometry Factors
    with st.expander("Terrain & Geometry Factors"):
        if country == "UK":
            # UK specific calculations
            altitude_factor = calculate_altitude_factor(altitude)
            vb_0 = uk_vb_map * altitude_factor
            st.write(f"Altitude Factor: {altitude_factor:.3f}")
            st.write(f"Fundamental Wind Velocity after altitude correction (Vb,0): {vb_0:.2f} m/s")
        else:
            # Other European country calculations
            st.write(f"Using provided Fundamental Wind Velocity (Vb,0): {vb_0:.2f} m/s")
        
        c_dir = st.number_input("Directional factor (Cdir)", min_value=0.0, max_value=1.0, value=1.0, 
                               help="Conservative value is 1.0")
        c_season = st.number_input("Seasonal factor (Cseason)", min_value=0.0, max_value=1.0, value=1.0,
                                  help="1.0 for year-round calculation")
        
        # Return period
        st.subheader("Return Period")
        return_period = st.number_input("Return Period (years)", min_value=1, value=50)
        
        # Custom K, n, p values or standard
        custom_probability_factors = st.checkbox("Use custom probability factors?")
        if custom_probability_factors:
            k = st.number_input("Shape factor (K)", min_value=0.0, value=0.2)
            n = st.number_input("Exponent (n)", min_value=0.0, value=0.5)
            p = st.number_input("Annual probability of exceedance (p)", min_value=0.0, max_value=1.0, value=0.02)
            c_prob = calculate_cprob(return_period, k, n, p)
        else:
            k, n, p = 0.2, 0.5, 0.02
            c_prob = 1.0
        
        st.write(f"Probability factor (Cprob): {c_prob:.3f}")
        
        # Basic Wind Velocity calculation
        vb = vb_0 * c_dir * c_season * c_prob
        st.write(f"Basic Wind Velocity (Vb): {vb:.2f} m/s")
    
    # Roughness Factor and Orography
    with st.expander("Roughness Factor and Orography"):
        # Roughness factor
        if country == "UK":
            if location_type == "Town":
                terrain_cat = "IV"
            elif location_type == "Country":
                terrain_cat = "II"
            else:  # Sea
                terrain_cat = "0"
            st.write(f"UK Location Type: {location_type} (Terrain Category: {terrain_cat})")
        else:
            terrain_cat = terrain_category
            st.write(f"Terrain Category: {terrain_cat}")
        
        cr_z = calculate_roughness_factor(height_above_ground, terrain_cat)
        st.write(f"Roughness Factor Cr(z): {cr_z:.3f}")
        
        # Orography factor
        orography_significant = st.checkbox("Is orography significant?")
        if orography_significant:
            co_z = st.number_input("Orography factor Co(z)", min_value=0.0, value=1.0, 
                                 help="Use A.3 for hills or A.4 for shaded areas")
        else:
            co_z = 1.0
        
        st.write(f"Orography Factor Co(z): {co_z:.3f}")
        
        # Mean wind velocity
        vm_z = vb * cr_z * co_z
        st.write(f"Mean Wind Velocity Vm(z): {vm_z:.2f} m/s")
    
    # Peak Velocity Pressure
    with st.expander("Peak Velocity Pressure"):
        air_density = st.number_input("Air Density (kg/m³)", min_value=0.0, value=1.25)
        
        # Basic wind pressure
        qb = 0.5 * air_density * vb**2
        st.write(f"Basic Wind Pressure qb: {qb:.2f} Pa")
        
        # Calculate peak velocity pressure
        # In a real implementation, this would use more complex formulas from BS EN 1991-1-4
        iv = calculate_turbulence_intensity(height_above_ground, terrain_cat, co_z)
        qp_z = qb * (1 + 7 * iv) * (cr_z * co_z)**2
        
        st.write(f"Turbulence Intensity Iv(z): {iv:.3f}")
        st.write(f"Peak Velocity Pressure qp(z): {qp_z:.2f} Pa")
    
    # Wind Zones and Pressure Coefficients
    with st.expander("Wind Zones and Pressure Coefficients"):
        # Calculate e
        e = min(width, 2 * height)
        st.write(f"e = min(b, 2h) = {e:.2f} m")
        
        # Determine zones
        if e < depth:
            zones = ["A", "B", "C"]
        elif e >= 5 * depth:
            zones = ["A"]
        else:
            zones = ["A", "B"]
        
        st.write(f"Applicable Wind Zones: {', '.join(zones)}")
        
        # External pressure coefficients
        h_d_ratio = height / depth
        st.write(f"h/d ratio: {h_d_ratio:.3f}")
        
        # This is simplified - would need more complex lookup tables in reality
        cpe_values = calculate_external_pressure_coefficients(h_d_ratio, zones, width, height)
        
        # Display cpe values
        st.write("External Pressure Coefficients:")
        for zone, cpe in cpe_values.items():
            st.write(f"Zone {zone}: cpe,10 = {cpe:.3f}")
        
        # Internal pressure coefficients
        st.subheader("Internal Pressure Coefficient")
        st.write("Most onerous of +0.2, -0.3 is typically used")
        cpi_values = [0.2, -0.3]
        
        # Funnelling check
        check_funnelling = st.checkbox("Check for funnelling effects")
        if check_funnelling:
            gap_width = st.number_input("Gap width (m)", min_value=0.0, value=2.0)
            
            if gap_width < e/4 or gap_width > e:
                st.write("No funnelling applies")
            else:
                st.write(f"Funnelling applies (gap between e/4 = {e/4:.2f}m and e = {e:.2f}m)")
                # Here you would adjust cpe values for funnelling
    
    # Net Pressures
    with st.expander("Net Pressures"):
        st.subheader("Wind Pressure Calculation")
        
        for zone, cpe in cpe_values.items():
            st.write(f"Zone {zone}:")
            for cpi in cpi_values:
                we = qp_z * cpe
                wi = qp_z * cpi
                net_pressure_1 = we + wi  # For suction on internal surfaces
                net_pressure_2 = we - wi  # For pressure on internal surfaces
                
                st.write(f"  With cpi = {cpi}:")
                st.write(f"  - External pressure (We): {we:.2f} Pa")
                st.write(f"  - Internal pressure (Wi): {wi:.2f} Pa")
                st.write(f"  - Net pressure (We + Wi): {net_pressure_1:.2f} Pa")
                st.write(f"  - Net pressure (We - Wi): {net_pressure_2:.2f} Pa")
                st.write("---")
    
    # Visual representation
    with st.expander("Visual Representation"):
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Simple building representation
        building_x = [0, width, width, 0, 0]
        building_y = [0, 0, height, height, 0]
        ax.plot(building_x, building_y, 'k-', linewidth=2)
        
        # Wind zones (simplified)
        if "A" in zones:
            # Zone A coloring - this is simplified
            zone_a_width = min(e/5, width)
            ax.fill_between([0, zone_a_width], [0], [height], alpha=0.3, color='blue', label='Zone A')
        
        if "B" in zones:
            zone_b_width = min(e*4/5, width)
            ax.fill_between([zone_a_width, zone_b_width], [0], [height], alpha=0.3, color='green', label='Zone B')
        
        if "C" in zones:
            ax.fill_between([zone_b_width, width], [0], [height], alpha=0.3, color='red', label='Zone C')
        
        # Add labels and legend
        ax.set_xlabel('Width (m)')
        ax.set_ylabel('Height (m)')
        ax.set_title('Wind Zones on Building Facade')
        ax.legend()
        ax.grid(True)
        ax.set_aspect('equal')
        
        st.pyplot(fig)

# Helper functions
def calculate_altitude_factor(altitude):
    """Calculate altitude factor for UK"""
    if altitude <= 10:
        return 1.0
    else:
        return 1.0 + 0.001 * (altitude - 10)

def calculate_cprob(return_period, k=0.2, n=0.5, p=0.02):
    """Calculate probability factor based on return period"""
    p_annual = 1 / return_period
    return ((1 - k * np.log(-np.log(1 - p_annual))) / (1 - k * np.log(-np.log(1 - p))))**n

def calculate_roughness_factor(z, terrain_category):
    """Calculate roughness factor based on terrain category and height"""
    # Simplified - would need more detailed implementation based on BS EN 1991-1-4
    z0_values = {
        "0": 0.003,
        "I": 0.01,
        "II": 0.05,
        "III": 0.3,
        "IV": 1.0
    }
    z_min_values = {
        "0": 1,
        "I": 1,
        "II": 2,
        "III": 5,
        "IV": 10
    }
    
    z0 = z0_values[terrain_category]
    z_min = z_min_values[terrain_category]
    z_max = 200  # Standard value
    
    # Apply the height limit
    z_calc = max(z_min, min(z, z_max))
    
    kr = 0.19 * (z0 / 0.05)**0.07  # Terrain factor
    cr = kr * np.log(z_calc / z0)  # Roughness factor
    
    return cr

def calculate_turbulence_intensity(z, terrain_category, co_z):
    """Calculate turbulence intensity"""
    # Simplified - would need more detailed implementation
    z0_values = {
        "0": 0.003,
        "I": 0.01,
        "II": 0.05,
        "III": 0.3,
        "IV": 1.0
    }
    z_min_values = {
        "0": 1,
        "I": 1,
        "II": 2,
        "III": 5,
        "IV": 10
    }
    
    z0 = z0_values[terrain_category]
    z_min = z_min_values[terrain_category]
    
    # Apply the height limit
    z_calc = max(z_min, min(z, 200))
    
    if co_z > 1.0:
        # Orography affects turbulence
        kl = 1.0  # Turbulence factor, default value
        iv = kl / (co_z * np.log(z_calc / z0))
    else:
        kl = 1.0
        iv = kl / (np.log(z_calc / z0))
    
    return iv

def calculate_external_pressure_coefficients(h_d_ratio, zones, width, height):
    """Calculate external pressure coefficients for zones"""
    # Simplified implementation - would need more detailed tables from BS EN 1991-1-4
    cpe_values = {}
    
    # Very simplified coefficients - in reality would depend on h/d ratio and other factors
    if "A" in zones:
        cpe_values["A"] = -1.2
    if "B" in zones:
        cpe_values["B"] = -0.8
    if "C" in zones:
        cpe_values["C"] = -0.5
    
    # Adjust based on h/d ratio (simplified)
    factor = min(1.0, max(0.5, h_d_ratio / 5))
    for zone in cpe_values:
        cpe_values[zone] *= factor
    
    return cpe_values

if __name__ == "__main__":
    main()

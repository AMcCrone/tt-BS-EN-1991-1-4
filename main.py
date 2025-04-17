import streamlit as st
import datetime
import math
import pandas as pd
import openpyxl
from auth import authenticate_user
from calc_engine.uk.terrain import get_terrain_categories as get_uk_terrain
from calc_engine.eu.terrain import get_terrain_categories as get_eu_terrain
from visualisation.building_viz import create_building_visualisation

authenticate_user()

# App version and metadata
APP_VERSION = "1.0.0"
LAST_UPDATED = "April 15, 2025"

# Setup page configuration with a favicon
st.set_page_config(
    page_title="Wind Load Calculator",
    page_icon="🌪️"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.inputs = {}
    st.session_state.results = {}
    st.session_state.show_educational = True

# Display company logo
st.image("educational/images/TT_Logo_Colour.png", width=450, output_format="PNG")

# Simple title and subtitle using Streamlit's built-in functions
st.title("Wind Load Calculator")
st.caption("Wind Load Calculation to BS EN 1991-1-4 and UK National Annex")

# Add print-specific CSS - minimal version
st.markdown("""
<style>
@media print {
    /* Hide UI elements in print mode */
    .stApp header, .stApp footer, .stSidebar, .stButton, 
    .educational-content, .navigation-section {
        display: none !important;
    }
    
    /* Format printable content */
    .print-friendly {
        page-break-inside: avoid;
        margin: 20px 0;
    }
}
</style>
""", unsafe_allow_html=True)

# Section 1: Project Information
st.header("1. Project Information")
col1, col2 = st.columns(2)

with col1:
    # Project details
    project_name = st.text_input("Project Name", 
                          value=st.session_state.inputs.get("project_name", ""))
    location = st.text_input("Location (City/Country)", 
                      value=st.session_state.inputs.get("location", ""))

with col2:
    # Project number and region
    project_number = st.text_input("Project Number", 
                           value=st.session_state.inputs.get("project_number", ""))
    region_options = ["United Kingdom", "Other European Country"]
    region = st.selectbox("Region", 
                  options=region_options,
                  index=region_options.index(st.session_state.inputs.get("region", "United Kingdom")) 
                  if st.session_state.inputs.get("region") in region_options else 0)

# Save project info inputs to session state
if project_name:
    st.session_state.inputs["project_name"] = project_name
if project_number:
    st.session_state.inputs["project_number"] = project_number
if location:
    st.session_state.inputs["location"] = location
if region:
    st.session_state.inputs["region"] = region

# Divider between sections
st.markdown("---")

# Section 2: GEOMETRY AND TERRAIN
st.header("Geometry & Terrain")

st.subheader("Geometry")
# Building dimensions input
col1, col2 = st.columns([0.3,0.7])
with col1:
    # Building dimensions
    NS_dimension = st.number_input(
        "North-South Dimension (m)",
        min_value=1.0,
        max_value=500.0,
        value=float(st.session_state.inputs.get("NS_dimension", 20.0)),
        step=1.0
    )
    
    EW_dimension = st.number_input(
        "East-West Dimension (m)",
        min_value=1.0,
        max_value=500.0,
        value=float(st.session_state.inputs.get("EW_dimension", 15.0)),
        step=1.0
    )
    
    z = st.number_input(
        "Building Height (m)",
        min_value=1.0,
        max_value=500.0,
        value=float(st.session_state.inputs.get("z", 10.0)),
        step=1.0
    )
    
    # Option to include an inset zone
    include_inset = st.checkbox("Include Inset Zone", 
                               value=st.session_state.inputs.get("include_inset", False))
    
    # Show inset parameters only if inset is enabled
    inset_offset = 0
    inset_height = 0
    
    if include_inset:
        inset_offset = st.number_input(
            "Inset Offset from Edges (m)",
            min_value=0.1,
            max_value=min(NS_dimension/2, EW_dimension/2) - 0.1,  # Prevent negative dimensions
            value=float(st.session_state.inputs.get("inset_offset", 2.0)),
            step=0.1
        )
        
        inset_height = st.number_input(
            "Inset Zone Height (m)",
            min_value=0.1,
            max_value=100.0,
            value=float(st.session_state.inputs.get("inset_height", 3.0)),
            step=0.1
        )

# Save geometry inputs to session state
st.session_state.inputs["NS_dimension"] = NS_dimension
st.session_state.inputs["EW_dimension"] = EW_dimension
st.session_state.inputs["z"] = z
st.session_state.inputs["include_inset"] = include_inset
if include_inset:
    st.session_state.inputs["inset_offset"] = inset_offset
    st.session_state.inputs["inset_height"] = inset_height

# 3D visualization of the building
with col2:
    building_fig = create_building_visualisation(
        NS_dimension, 
        EW_dimension, 
        z,
        include_inset=include_inset,
        inset_offset=inset_offset if include_inset else 0,
        inset_height=inset_height if include_inset else 0
    )
    st.plotly_chart(building_fig, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
        altitude_factor = st.number_input(
        "Altitude Above Sea Level (m)",
        min_value=1.0,
        max_value=500.0,
        value=float(st.session_state.inputs.get("altitude_factor", 20.0)),
        step=1.0
    )
with col2:
    d_sea = st.number_input(
        "Distance to Sea (km)",
        min_value=1.0,
        max_value=1000.0,
        value=float(st.session_state.inputs.get("d_sea", 60.0)),
        step=1.0
    )

def render_terrain_category():
    st.subheader("Terrain Category")

    # Import correct terrain module based on region from session state
    region = st.session_state.inputs.get("region")
    if region == "United Kingdom":
        from calc_engine.uk import terrain as terrain_module
    else:
        from calc_engine.eu import terrain as terrain_module

    # Get the terrain categories dictionary
    terrain_dict = terrain_module.get_terrain_categories()

    # Create a display list that combines the key and description
    display_options = [f"{code} - {desc}" for code, desc in terrain_dict.items()]

    # Create a dropdown (selectbox) for terrain category selection using full descriptions
    selected_option = st.selectbox("Select Terrain Category", display_options)

    # Extract the simplified category code by splitting at " - "
    selected_code = selected_option.split(" - ")[0].strip()
    st.session_state.inputs["terrain_category"] = selected_code

    # Display educational content if the toggle is enabled in the sidebar
    if st.session_state.get("show_educational", False):
        st.markdown("""<div class="educational-content print-friendly">""", unsafe_allow_html=True)
        # Display an image from the educational folder; adjust the path as needed.
        st.image("educational/images/Terrain_Cat.png", caption="Terrain Types")
        # Import educational text from educational/text_content.py (assuming it contains a variable named terrain_help)
        from educational import text_content
        st.write(text_content.terrain_help)
        st.markdown("</div>", unsafe_allow_html=True)
render_terrain_category()

# Section 3: WIND VELOCITY
st.markdown("---")
st.header("Wind Velocity")
st.subheader("Basic Wind Velocity")

col_input, col_result = st.columns(2)

with col_input:
    # Vb,map input
    V_bmap = st.number_input(
        "$$v_{b,map}$$ (m/s)",
        min_value=0.1,
        max_value=100.0,
        value=float(st.session_state.inputs.get("V_bmap", 24.0)),
        step=0.1,
        help="Fundamental wind velocity from Figure 3.2"
    )
    st.session_state.inputs["V_bmap"] = V_bmap

    # Let the user choose whether they want to override standard K, n, return period
    use_custom_values = st.checkbox("Use custom K, n, and return period?")
    
    if use_custom_values:
        K = st.number_input(
            "Shape parameter (K)",
            min_value=0.0,
            max_value=5.0,
            value=0.2,
            step=0.1,
            help="Typically 0.2 if unspecified."
        )
        n = st.number_input(
            "Exponent (n)",
            min_value=0.0,
            max_value=5.0,
            value=0.5,
            step=0.1,
            help="Typically 0.5 if unspecified."
        )
        return_period = st.number_input(
            "Return Period (years)",
            min_value=1,
            max_value=10000,
            value=50,
            step=1,
            help="Typical is 50 years."
        )
        # Probability of exceedance
        p = 1.0 / return_period
        
        # Equation (4.2):
        # c_prob = [ (1 - K * ln(-ln(1 - p))) / (1 - K * ln(-ln(0.98))) ]^n
        numerator = 1.0 - K * math.log(-math.log(1.0 - p))
        denominator = 1.0 - K * math.log(-math.log(0.98))
        # Guard against division by zero
        if abs(denominator) < 1e-9:
            st.warning("Denominator is close to zero; check K and standard reference. Setting c_prob = 1.")
            c_prob = 1.0
        else:
            c_prob = (numerator / denominator) ** n
    else:
        # If user doesn't override, c_prob = 1.0
        c_prob = 1.0

with col_result:
    # Altitude correction
    if z <= 10:
        c_alt = 1 + 0.001 * altitude_factor
    else:
        c_alt = 1 + 0.001 * altitude_factor * (10 / z) ** 0.2

    V_b0 = V_bmap * c_alt
    
    # Directional & seasonal factors (assume standard = 1.0 unless user changes them)
    c_dir = 1.0
    c_season = 1.0
    
    # Basic Wind Speed with c_prob included
    V_b = V_b0 * c_dir * c_season * c_prob

    st.session_state.inputs["V_b"] = V_b
    
    # Display the result
    st.markdown("**Calculated Basic Wind Speed**")
    st.latex(f"V_b = {V_b:.2f}\\; m/s")
    st.write(f"(Probability factor used: {c_prob:.3f})")

st.subheader("Mean Wind Velocity")

def calculate_displacement_height():
    use_standard = st.checkbox("Use standard $h_{{dis}}$ = 15m")
    
    if use_standard:
        h_dis = 15.0
    else:
        col1, col2 = st.columns(2)
        with col1:
            x = st.number_input("Distance x (m)", value=10.0, min_value=0.0)
        with col2:
            h_ave = st.number_input("Average height h_ave (m)", value=5.0, min_value=0.1)
        
        h = st.number_input("Obstruction height h (m)", value=6.0, min_value=0.1)
        
        if x <= 2 * h_ave:
            h_dis = min(0.8 * h_ave, 0.6 * h)
        elif x < 6 * h_ave:
            h_dis = min(1.2 * h_ave - 0.2 * x, 0.6 * h)
        else:
            h_dis = 0
    
    return h_dis

# Execute the displacement height calculation
h_dis = calculate_displacement_height()

# Get or set the height z from session state
z = st.session_state.inputs.get("z", 10.0)
z_minus_h_dis = z - h_dis

st.write(f"Displacement height $h_{{dis}}$: {h_dis:.2f} m")
st.write(f"Effective height $z - h_{{dis}}$): {z_minus_h_dis:.2f} m")

# Check the region selection
region = st.session_state.inputs.get("region")

if region == "United Kingdom":
    st.markdown("#### Roughness Factor $C_r(z)$")
    
    # Import the contour plot functions for UK
    from calc_engine.uk.contour_plots import load_contour_data, get_interpolated_value, display_single_plot
    
    # Get required parameters from session state - use the freshly calculated values
    x_upwind = st.session_state.inputs.get("distance_upwind", 10.0)
    
    # Create columns for layout
    col1, col2 = st.columns([0.3, 0.7])
    
    with col1:
        # Allow user to override the calculated value (optional)
        use_calculated = st.checkbox("Use calculated value from contour plot", value=True)
        
        # Display the effective height but allow adjustment
        z_input = st.number_input(
            "z - h_dis (m)",
            min_value=1.0,
            max_value=200.0,
            value=z_minus_h_dis,  # Use the freshly calculated value
            format="%.1f"
        )
        # Update session state with any user-adjusted value
        st.session_state.inputs["z_minus_h_dis"] = z_input
        
        d_sea = st.session_state.inputs.get("d_sea", 60.0)
    
    # Load the contour data
    contour_data_path = "calc_engine/uk/contour_data.xlsx"
    datasets = load_contour_data(contour_data_path)
    
    # Get interpolated c_r(z) value from NA.3
    interpolated_c_r = get_interpolated_value(datasets, "NA.3", d_sea, z_input)
    
    with col2:
        # Display NA.3 plot in column 2
        display_single_plot(col2, datasets, "NA.3", d_sea, z_input)
    
    # Set c_r based on user's choice
    if use_calculated and interpolated_c_r is not None:
        c_r = interpolated_c_r
    else:
        # If user chooses to enter manually or if interpolation failed
        c_r = st.number_input(
            "Enter roughness factor value manually",
            min_value=0.70,
            max_value=1.75,
            value=float(st.session_state.inputs.get("c_r", 1.0)),  # Use the common c_r key
            step=0.01,
            format="%.3f"
        )
    
    # Store calculated value with consistent naming
    st.session_state.inputs["c_r"] = c_r
    st.session_state.inputs["c_rz"] = c_r  # Add for consistency with mean velocity calculation
    
    st.latex(f"c_r(z) = {c_r:.3f}")
else:
    # Import the roughness function from the EU module
    from calc_engine.eu import roughness as roughness_module
    
    # Assume that a terrain category was selected via a dropdown earlier, stored in session_state
    terrain_category = st.session_state.inputs.get("terrain_category", "II")
    
    # Now call the roughness function
    try:
        # Use z_minus_h_dis instead of z for consistent handling across regions
        c_r = roughness_module.calculate_cr(z_minus_h_dis, terrain_category)
        
        # Store calculated value with consistent naming
        st.session_state.inputs["c_r"] = c_r
        st.session_state.inputs["c_rz"] = c_r  # Add for consistency with mean velocity calculation
        
        st.markdown("#### Roughness Factor $C_r(z)$")
        st.write(f"The roughness factor, \\(c_r(z)\\), for terrain category **{terrain_category}** and height **{z_minus_h_dis} m** is:")
        st.latex(f"c_r(z) = {c_r:.3f}")
    except Exception as e:
        st.error(f"Error calculating roughness factor: {e}")

# --- Section 3: Mean Wind Velocity ---
st.markdown("#### Mean Wind Velocity")

# Retrieve stored values with consistent naming
v_b = st.session_state.inputs.get("V_b", 0.0)
c_rz = st.session_state.inputs.get("c_rz", 1.0)
c_oz = st.session_state.inputs.get("c_oz", 1.0)

# Calculate mean wind velocity
v_mean = v_b * c_rz * c_oz

# Store in session state for later use
st.session_state.inputs["v_mean"] = v_mean

# Display the result
st.write(f"$$v_m(z) = v_b \\cdot c_r(z) \\cdot c_o(z) = {v_b:.2f} \\cdot {c_rz:.2f} \\cdot {c_oz:.2f} = {v_mean:.2f}\\;\\mathrm{{m/s}}$$")
        
# Section 4: WIND PRESSURE
st.markdown("---")
st.header("Peak Wind Pressure")

# Air density input
rho_air = st.number_input(
    "Air Density (kg/m³)",
    min_value=1.0,
    max_value=1.5,
    value=1.25,
    step=0.01,
    format="%.2f"
)
st.session_state.inputs["rho_air"] = rho_air

# Basic wind pressure calculation
v_b = st.session_state.inputs.get("V_b", 0.0)
q_b = 0.5 * rho_air * (v_b ** 2)
st.session_state.inputs["q_b"] = q_b

st.write(f"Basic wind pressure: $q_b = 0.5 \\cdot \\rho \\cdot v_b^2 = 0.5 \\cdot {rho_air:.2f} \\cdot {v_b:.2f}^2 = {q_b:.2f}\\;\\mathrm{{N/m²}}$")

# Check the region selection
region = st.session_state.inputs.get("region")

if region == "United Kingdom":
    # UK-specific peak pressure calculation
    st.markdown("### UK Peak Wind Pressure")
    
    # Import the contour plot functions for UK
    from calc_engine.uk.contour_plots import load_contour_data, get_interpolated_value, display_single_plot
    
    # Check if orography is significant
    is_orography_significant = st.checkbox("Orography is significant", value=False)
    
    # Get effective height from previous calculation
    z_minus_h_dis = st.session_state.inputs.get("z_minus_h_dis", 10.0)
    
    # Load the contour data
    contour_data_path = "calc_engine/uk/contour_data.xlsx"
    datasets = load_contour_data(contour_data_path)
    
    if is_orography_significant:
        # Case 1: UK with significant orography (use NA.5)
        st.markdown("#### Using NA.5 for significant orography")
        
        # Get required parameters
        d_sea = st.session_state.inputs.get("d_sea", 60.0)
        
        # Create columns for layout
        col1, col2 = st.columns([0.3, 0.7])
        
        with col1:
            # Allow user to adjust parameters
            z_input = st.number_input(
                "Height z (m)",
                min_value=1.0,
                max_value=200.0,
                value=z_minus_h_dis,
                format="%.1f"
            )
            
            # Get interpolated value from NA.5
            interpolated_qp = get_interpolated_value(datasets, "NA.5", d_sea, z_input)
            
            if interpolated_qp is not None:
                qp_value = interpolated_qp * q_b
                st.session_state.inputs["qp_value"] = qp_value
                st.write(f"Peak velocity pressure: $q_p(z) = {qp_value:.2f}\\;\\mathrm{{N/m²}}$")
            else:
                st.error("Could not interpolate value from NA.5")
        
        with col2:
            # Display NA.5 plot
            display_single_plot(col2, datasets, "NA.5", d_sea, z_input)
    
    else:
        # Case 2: UK with non-significant orography
        st.markdown("#### Using NA.7 and NA.8 for non-significant orography")
        
        # Check if in town or country based on terrain category
        terrain_category = st.session_state.inputs.get("terrain_category", "II")
        in_town = terrain_category in ["III", "IV"]
        
        if in_town:
            st.markdown("##### Town terrain (Categories III or IV)")
            
            # Create columns for layout - just using one column for inputs now
            col1 = st.columns(1)[0]
            
            with col1:
                # Allow user to adjust parameters
                z_input = st.number_input(
                    "Height z (m)",
                    min_value=1.0,
                    max_value=200.0,
                    value=z_minus_h_dis,
                    format="%.1f"
                )
                
                # Distance inside town terrain
                distance_in_town = st.number_input(
                    "Distance inside town (km)",
                    min_value=0.0,
                    max_value=10.0,
                    value=1.0,
                    step=0.1,
                    format="%.1f"
                )
                st.session_state.inputs["distance_in_town"] = distance_in_town
            
            # Get interpolated values from NA.7 and NA.8
            # Display NA.7 plot (height factor) first
            st.markdown("##### NA.7 Plot (Height Factor)")
            display_single_plot(st, datasets, "NA.7", 0, z_input)
            interpolated_height_factor = get_interpolated_value(datasets, "NA.7", 0, z_input)
            
            # Then display NA.8 plot (town factor) beneath it
            st.markdown("##### NA.8 Plot (Town Factor)")
            display_single_plot(st, datasets, "NA.8", distance_in_town, 0)
            interpolated_town_factor = get_interpolated_value(datasets, "NA.8", distance_in_town, 0)
            
            if interpolated_height_factor is not None and interpolated_town_factor is not None:
                qp_value = interpolated_height_factor * interpolated_town_factor * q_b
                st.session_state.inputs["qp_value"] = qp_value
                
                st.write(f"Height factor from NA.7: {interpolated_height_factor:.3f}")
                st.write(f"Town factor from NA.8: {interpolated_town_factor:.3f}")
                st.write(f"Peak velocity pressure: $q_p(z) = {qp_value:.2f}\\;\\mathrm{{N/m²}}$")
            else:
                st.error("Could not interpolate values from NA.7 or NA.8")
        
        else:
            st.markdown("##### Country terrain (Categories 0, I, or II)")
            
            # Create columns for layout
            col1, col2 = st.columns([0.3, 0.7])
            
            with col1:
                # Allow user to adjust parameters
                z_input = st.number_input(
                    "Height z (m)",
                    min_value=1.0,
                    max_value=200.0,
                    value=z_minus_h_dis,
                    format="%.1f"
                )
            
            # Get interpolated value from NA.7 only
            with col2:
                # Display NA.7 plot
                display_single_plot(col2, datasets, "NA.7", 0, z_input)
                interpolated_height_factor = get_interpolated_value(datasets, "NA.7", 0, z_input)
            
            if interpolated_height_factor is not None:
                qp_value = interpolated_height_factor * q_b
                st.session_state.inputs["qp_value"] = qp_value
                
                st.write(f"Height factor from NA.7: {interpolated_height_factor:.3f}")
                st.write(f"Peak velocity pressure: $q_p(z) = {qp_value:.2f}\\;\\mathrm{{N/m²}}$")
            else:
                st.error("Could not interpolate value from NA.7")

else:
    # Non-UK peak pressure calculation (EU standard)
    st.markdown("### EU Peak Wind Pressure")
    
    # Import necessary functions
    from calc_engine.eu.peak_pressure import calculate_qp
    
    # Get needed parameters
    z = st.session_state.inputs.get("z_minus_h_dis", 10.0)
    terrain_category = st.session_state.inputs.get("terrain_category", "II")
    v_b = st.session_state.inputs.get("V_b", 0.0)
    c_o = st.session_state.inputs.get("c_oz", 1.0)  # Orography factor
    
    # Calculate peak pressure
    try:
        qp_value = calculate_qp(z, terrain_category, v_b, rho_air, c_o)
        st.session_state.inputs["qp_value"] = qp_value
        
        # Get the c_r value for display
        c_r = st.session_state.inputs.get("c_r", 1.0)
        
        # Display calculation parameters and result
        st.write(f"Basic wind pressure: $q_b = {q_b:.2f}\\;\\mathrm{{N/m²}}$")
        st.write(f"Roughness factor: $c_r(z) = {c_r:.3f}$")
        st.write(f"Orography factor: $c_o(z) = {c_o:.3f}$")
        
        # Calculate turbulence intensity (used in EU approach)
        k_I = 1.0  # turbulence factor (default value is 1.0)
        terrain_params = {
            '0': {'z0': 0.003, 'z_min': 1},
            'I': {'z0': 0.01, 'z_min': 1},
            'II': {'z0': 0.05, 'z_min': 2},
            'III': {'z0': 0.3, 'z_min': 5},
            'IV': {'z0': 1.0, 'z_min': 10},
        }
        z0 = terrain_params[terrain_category]['z0']
        z_min = terrain_params[terrain_category]['z_min']
        
        # Calculate turbulence intensity
        if z < z_min:
            I_v = k_I / (c_o * math.log(z_min / z0))
        else:
            I_v = k_I / (c_o * math.log(z / z0))
        
        st.write(f"Turbulence intensity: $I_v(z) = {I_v:.3f}$")
        
        # Display the full formula and result
        st.write(f"Peak velocity pressure: $q_p(z) = [1 + 7 \\cdot I_v(z)] \\cdot 0.5 \\cdot \\rho \\cdot v_m^2(z) = {qp_value:.2f}\\;\\mathrm{{N/m²}}$")
        
    except Exception as e:
        st.error(f"Error calculating peak velocity pressure: {e}")

# Get the peak velocity pressure from previous calculations
qp_value = st.session_state.inputs.get("qp_value", 0.0)

# Building dimensions input
col1, col2 = st.columns(2)
with col1:
    h = st.number_input("Building Height (h) [m]", 
                        min_value=1.0, 
                        value=15.0, 
                        step=0.5)
    st.session_state.inputs["building_height"] = h

with col2:
    b = st.number_input("Building Width (b) [m]", 
                        min_value=1.0, 
                        value=10.0, 
                        step=0.5)
    st.session_state.inputs["building_width"] = b

# Determine the case based on height-to-width ratio
if h <= b:
    profile_case = "Case 1: h ≤ b"
elif b < h <= 2*b:
    profile_case = "Case 2: b < h ≤ 2b"
else:  # h > 2*b
    profile_case = "Case 3: h > 2b"

st.write(f"Building profile: **{profile_case}**")

# Create the wind pressure profile visualization
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

def get_qp_at_height(z_height, building_height, building_width, qp_max):
    """Calculate q_p at a given height based on building dimensions."""
    h = building_height
    b = building_width
    
    if h <= b:
        # Case 1: Constant pressure across entire height
        return qp_max
    
    elif b < h <= 2*b:
        # Case 2: Two pressure zones
        if z_height <= b:
            return qp_max * (b / h)  # q_p(b)
        else:
            return qp_max  # q_p(h)
    
    else:  # h > 2*b
        # Case 3: Three pressure zones
        if z_height <= b:
            return qp_max * (b / h)  # q_p(b)
        elif b < z_height <= h - b:
            # Calculate z_strip relative position
            z_strip = b + (z_height - b) / (h - 2*b) * b
            # Linear interpolation between q_p(b) and q_p(h)
            return qp_max * (z_strip / h)
        else:  # z_height > h - b
            return qp_max  # q_p(h)

# Generate the plot
fig, ax = plt.subplots(figsize=(10, 8))

# Create height points for plotting
z_points = np.linspace(0, h, 100)
qp_points = [get_qp_at_height(z, h, b, qp_value) for z in z_points]

# Create the building outline
building_x = [0, b, b, 0, 0]
building_y = [0, 0, h, h, 0]

# Plot the building
ax.plot(building_x, building_y, 'k-', linewidth=2)

# Fill the building
ax.fill(building_x, building_y, color='lightgray', alpha=0.3)

# Plot pressure profile
max_arrow_length = 3 * b  # Maximum length for pressure arrows
arrow_scale = max_arrow_length / qp_value  # Scale factor for arrows

# Reference point for arrows
ref_x = b * 1.5

# Draw arrows at different heights
num_arrows = 20
arrow_heights = np.linspace(0.05*h, 0.95*h, num_arrows)

for z_height in arrow_heights:
    qp_at_z = get_qp_at_height(z_height, h, b, qp_value)
    arrow_length = qp_at_z * arrow_scale
    ax.arrow(ref_x, z_height, arrow_length, 0, 
             head_width=0.02*h, head_length=0.02*b, 
             fc='blue', ec='blue', linewidth=1)
    
    # Add pressure value text for selected arrows (every 5th arrow)
    if z_height in arrow_heights[::5]:
        ax.text(ref_x + arrow_length + 0.1*b, z_height, 
                f"{qp_at_z:.2f} N/m²", 
                verticalalignment='center', fontsize=8)

# Mark reference heights
if h <= b:
    # Case 1: Only mark h
    ax.axhline(y=h, color='r', linestyle='--', alpha=0.7)
    ax.text(0, h, f"$z_e = h = {h}$ m", verticalalignment='bottom', horizontalalignment='left', color='r', fontsize=9)
    
elif b < h <= 2*b:
    # Case 2: Mark b and h
    ax.axhline(y=b, color='r', linestyle='--', alpha=0.7)
    ax.axhline(y=h, color='r', linestyle='--', alpha=0.7)
    ax.text(0, b, f"$z_e = b = {b}$ m", verticalalignment='bottom', horizontalalignment='left', color='r', fontsize=9)
    ax.text(0, h, f"$z_e = h = {h}$ m", verticalalignment='bottom', horizontalalignment='left', color='r', fontsize=9)
    
    # Add hatching for the upper part
    hatch_x = np.linspace(0, b, 10)
    for i in range(5):
        y1 = b + i * (h - b) / 5
        y2 = b + (i + 1) * (h - b) / 5
        for j in range(len(hatch_x)-1):
            if i % 2 == j % 2:
                ax.plot([hatch_x[j], hatch_x[j+1]], [y1, y2], 'k-', linewidth=0.5, alpha=0.5)
    
else:  # h > 2*b
    # Case 3: Mark b, h-b, and h
    z_strip = h - b
    ax.axhline(y=b, color='r', linestyle='--', alpha=0.7)
    ax.axhline(y=z_strip, color='r', linestyle='--', alpha=0.7)
    ax.axhline(y=h, color='r', linestyle='--', alpha=0.7)
    ax.text(0, b, f"$z_e = b = {b}$ m", verticalalignment='bottom', horizontalalignment='left', color='r', fontsize=9)
    ax.text(0, z_strip, f"$z_e = z_{{strip}} = {z_strip:.1f}$ m", verticalalignment='bottom', horizontalalignment='left', color='r', fontsize=9)
    ax.text(0, h, f"$z_e = h = {h}$ m", verticalalignment='bottom', horizontalalignment='left', color='r', fontsize=9)
    
    # Add hatching for the middle part
    hatch_x = np.linspace(0, b, 10)
    for i in range(10):
        y1 = b + i * (z_strip - b) / 10
        y2 = b + (i + 1) * (z_strip - b) / 10
        for j in range(len(hatch_x)-1):
            if i % 2 == j % 2:
                ax.plot([hatch_x[j], hatch_x[j+1]], [y1, y2], 'k-', linewidth=0.5, alpha=0.5)

# Set axis labels and title
ax.set_xlabel('Distance [m]')
ax.set_ylabel('Height [m]')
ax.set_title(f'Wind Pressure Profile - {profile_case}')

# Set axis limits
ax.set_xlim(-0.5*b, ref_x + max_arrow_length + b)
ax.set_ylim(-0.1*h, 1.1*h)

# Add a grid
ax.grid(True, linestyle='--', alpha=0.3)

# Display the plot
st.pyplot(fig)

# Create a table showing pressure values at key heights
st.subheader("Wind Pressure Values at Key Heights")

key_heights = []
if h <= b:
    key_heights = [("Ground level", 0), (f"Top (h = {h} m)", h)]
elif b < h <= 2*b:
    key_heights = [("Ground level", 0), (f"Width level (b = {b} m)", b), (f"Top (h = {h} m)", h)]
else:  # h > 2*b
    key_heights = [
        ("Ground level", 0), 
        (f"Lower zone (b = {b} m)", b),
        (f"Middle zone (z_strip = {h-b:.1f} m)", h-b),
        (f"Top (h = {h} m)", h)
    ]

# Create and display the table
data = []
for label, z_height in key_heights:
    if z_height > 0:  # Skip ground level for calculation
        qp_at_z = get_qp_at_height(z_height, h, b, qp_value)
        data.append([label, f"{z_height:.2f}", f"{qp_at_z:.2f}"])
    else:
        data.append([label, "0.00", "0.00"])  # Ground level has zero pressure

import pandas as pd
df = pd.DataFrame(data, columns=["Position", "Height (m)", "q_p(z) (N/m²)"])
st.table(df)

# Calculate the resulting pressure for design
if h <= b:
    design_pressure = qp_value
elif b < h <= 2*b:
    # Weighted average of the two zones
    qp_b = qp_value * (b / h)
    weighted_avg = (qp_b * b + qp_value * (h - b)) / h
    design_pressure = weighted_avg
else:  # h > 2*b
    # More complex calculation with three zones
    qp_b = qp_value * (b / h)
    qp_strip = qp_value * ((h - b) / h)
    design_pressure = (qp_b * b + qp_strip * (h - 2*b) + qp_value * b) / h

st.info(f"Design peak velocity pressure for the entire building: {design_pressure:.2f} N/m²")

# Store in session state for later use
st.session_state.inputs["design_pressure"] = design_pressure

# Section 5: PRESSURE COEFFICIENTS
st.markdown("---")
st.header("Pressure Coefficients")
st.info("Pressure Coefficients will be displayed here")

# Section 6: RESULTS SUMMARY
st.markdown("---")
st.header("Results Summary")
st.info("Calculation results will be displayed here")

# Toggle educational content in sidebar
st.sidebar.title("Options")
show_educational = st.sidebar.checkbox("Show Educational Content", 
                              value=st.session_state.show_educational)
st.session_state.show_educational = show_educational

# Footer Design
st.markdown(f"""
<div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #f0f2f6; padding: 0.5rem; text-align: center; font-size: 0.8rem; color: #666; border-top: 1px solid #ddd;">
    Wind Load Calculator v{APP_VERSION} | © {datetime.datetime.now().year}
</div>
""", unsafe_allow_html=True)

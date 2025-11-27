# Import packages for main.py
import streamlit as st 
import datetime
import math
import pandas as pd
import openpyxl
import requests
from streamlit_folium import st_folium
from geopy.distance import geodesic

# Import functions from modules
from auth import authenticate_user
from calc_engine.uk.terrain import get_terrain_categories as get_uk_terrain
from calc_engine.eu.terrain import get_terrain_categories as get_eu_terrain
from calc_engine.common.inset_zone import detect_zone_E_and_visualise, create_styled_inset_dataframe
from calc_engine.common.pressure_summary import create_pressure_summary, plot_elevation_with_pressures, generate_pressure_summary_paragraphs
from visualisation.building_viz import create_building_visualisation
from visualisation.map import render_map_with_markers, get_elevation, compute_distance, interactive_map_ui
from educational import text_content
from outputs.state_manager import add_session_save_ui, add_session_load_ui, add_pdf_export_ui
from outputs.pdf_download import add_pdf_download_button

# Set authentication from auth.py
authenticate_user()

# Setup page configuration
st.set_page_config(page_title="Wind Load Calculator",page_icon="🌪️")

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.inputs = {}                # session state for inputs
    st.session_state.results = {}               # session state for results
    st.session_state.show_educational = True    # session state for educational content

# Sidebar with usage instructions and educational content toggle
st.sidebar.image("educational/images/TT_Logo_Colour.svg", width=180, output_format="PNG")
st.sidebar.title("Options")

show_educational = st.sidebar.checkbox(
    "Show Educational Content", 
    value=st.session_state.get("show_educational", False)
)

col1, col2, col3 = st.columns([1, 4.8, 1])
with col2:
    st.image("educational/images/TT_Logo_Colour.svg", width=450)
    st.title("Wind Load Calculator")
    st.caption("Wind Load Calculation to BS EN 1991-1-4 and UK National Annex")

TT_Grey = "rgb(99,102,105)"
st.markdown("""
<style>
/* ============================
   GLOBAL & PRINT-ONLY STYLES
   ============================ */
@media print {
    /* Hide UI chrome */
    .stApp header, .stApp footer, .stSidebar, .stButton,
    .navigation-section, .educational-content {
        display: none !important;
    }
    /* Hide number-input buttons & help icons */
    .stNumberInput button, .stNumberInput svg,
    [data-testid="stToolbar"], .stTooltipIcon,
    .stTabs button[data-baseweb="tab-list"] {
        display: none !important;
    }
    /* Keep charts/images together */
    .print-friendly, img, svg, figure,
    [data-testid="stImage"], [data-testid="stPlotlyChart"] {
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        margin: 20px 0;
    }
    /* Page margins */
    @page { margin: 1cm; }
    /* On-demand page breaks */
    .pagebreak { page-break-before: always !important; }
}

/* ============================
   ON-SCREEN STYLES
   ============================ */

/* Educational text in light grey */
.educational-content {
    font-size: 0.8rem;
    color: TT_Grey;
}
</style>
""", unsafe_allow_html=True)

if st.session_state.get("show_educational", False):
    st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
    with st.expander("How to Use This App?", expanded=False):
        st.markdown(f'<div class="educational-content">{text_content.how_to}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Section 1: Project Information
st.subheader("Project Information")
col1, col2 = st.columns(2)

with col1:
    # Project details
    project_name = st.text_input("Project Name", value=st.session_state.inputs.get("project_name", ""))
    location = st.text_input("Location (City/Country)", value=st.session_state.inputs.get("location", ""))

with col2:
    # Project number and region
    project_number = st.text_input("Project Number", value=st.session_state.inputs.get("project_number", ""))
    region_options = ["United Kingdom", "Europe"]
    region = st.selectbox("Region", options=region_options,  index=region_options.index(st.session_state.inputs.get("region", "United Kingdom")) if st.session_state.inputs.get("region") in region_options else 0)

# Save project info inputs to session state
if project_name:
    st.session_state.inputs["project_name"] = project_name
if project_number:
    st.session_state.inputs["project_number"] = project_number
if location:
    st.session_state.inputs["location"] = location
if region:
    st.session_state.inputs["region"] = region

if st.session_state.get("show_educational", False):
    st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
    with st.expander("Which Region Should I Use?", expanded=False):
        # st.image("educational/images/Terrain_Cats.png", caption="Terrain Types")
        st.markdown(f'<div class="educational-content">{text_content.region_help}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
# Divider between sections
st.markdown("---")
# Section 2: GEOMETRY AND TERRAIN
st.subheader("Geometry")
col1, col2, col3 = st.columns(3)

# North-South Dimension input
with col1:
    NS_dimension = st.number_input("North-South Dimension (m)", min_value=1.0, max_value=500.0, value=float(st.session_state.inputs.get("NS_dimension", 30.0)), step=1.0)

# East-West Dimension input
with col2:
    EW_dimension = st.number_input("East-West Dimension (m)", min_value=1.0, max_value=500.0, value=float(st.session_state.inputs.get("EW_dimension", 30.0)),step=1.0)

# Building Height input
with col3:
    z = st.number_input("Building Height (m)", min_value=1.0, max_value=500.0, value=float(st.session_state.inputs.get("z", 30.0)), step=1.0)

# Save geometry inputs to session state
st.session_state.inputs["NS_dimension"] = NS_dimension
st.session_state.inputs["EW_dimension"] = EW_dimension
st.session_state.inputs["z"] = z

# 3D visualization of the building
building_fig = create_building_visualisation(NS_dimension, EW_dimension, z)
st.plotly_chart(building_fig, width="stretch")

st.markdown("---")
st.subheader("Terrain")

# Init session defaults
if "markers" not in st.session_state:
    st.session_state.markers = []
if "inputs" not in st.session_state:
    st.session_state.inputs = {"altitude": 20.0, "d_sea": 60.0}
st.session_state.inputs.setdefault("altitude", 20.0)
st.session_state.inputs.setdefault("d_sea", 60.0)

region = st.session_state.inputs.get("region")

if region == "United Kingdom":
    # UK: Map + distance to sea option
    use_map = st.checkbox("Use Interactive Map", value=False, help="Uncheck to input values manually")
    if use_map:
        interactive_map_ui()
    else:
        col1, col2 = st.columns(2)
        with col1:
            altitude = st.number_input("Altitude Above Sea Level (m)", min_value=1.0, max_value=500.0, value=float(st.session_state.inputs.get("altitude", 20.0)), step=1.0)
            st.session_state.inputs["altitude"] = altitude
        with col2:
            d_sea = st.number_input("Distance to Sea (km)", min_value=1.0, max_value=1000.0, value=float(st.session_state.inputs.get("d_sea", 60.0)), step=1.0)
            st.session_state.inputs["d_sea"] = d_sea
else:
    # Non-UK: only altitude
    altitude = st.number_input("Altitude Above Sea Level (m)", min_value=1.0, max_value=500.0, value=float(st.session_state.inputs.get("altitude", 20.0)), step=1.0)
    st.session_state.inputs["altitude"] = altitude

def render_terrain_category():
    # Import terrain module based on region from session state
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

    if region == "United Kingdom" and selected_code.lower() == "town":
        d_default = float(st.session_state.inputs.get("d_town_terrain", 5.0))
        d_town_terrain = st.number_input("Distance inside Town Terrain (km)", min_value=0.1, max_value=50.0, value=d_default, step=0.1)
        st.session_state.inputs["d_town_terrain"] = d_town_terrain

    if st.session_state.get("show_educational", False):
        st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
        with st.expander("Which Terrain Type Should I Use?", expanded=False):
            st.image("educational/images/Terrain_Cats.png", caption="Terrain Types")
            st.markdown(f'<div class="educational-content">{text_content.terrain_help}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
# Display the terrain category dropdown list
render_terrain_category()

# Section 3: WIND VELOCITY
st.markdown("---")
st.subheader("Basic Wind Velocity $$v_{b}$$")

if region == "United Kingdom":
    # UK calculation - uses V_b,map with altitude correction
    V_bmap = st.number_input("$$v_{b,map}$$ (m/s)", min_value=0.1, max_value=100.0, value=float(st.session_state.inputs.get("V_bmap", 21.5)), step=0.1, help="Fundamental wind velocity from Figure 3.2")
    st.session_state.inputs["V_bmap"] = V_bmap

    if st.session_state.get("show_educational", False):
        st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
        with st.expander("What $$v_{b,map}$$ Value Should I Use?", expanded=False):
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                st.markdown(f'<div class="educational-content">{text_content.basic_wind_help}</div>', unsafe_allow_html=True)
            with col2:
                st.image("educational/images/Basic_Wind_Map.png", caption="Basic Wind Map", width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Let the user choose whether they want to override standard K, n, return period
    use_custom_values = st.checkbox("Use custom K, n, and return period?")

    if use_custom_values:
        shape_column, exponent_column, period_column = st.columns(3)
        with shape_column:
            K = st.number_input("Shape parameter (K)", min_value=0.0, max_value=5.0, value=0.2, step=0.1, help="Typically 0.2 if unspecified.")
        with exponent_column:
            n = st.number_input("Exponent (n)", min_value=0.0, max_value=5.0, value=0.5, step=0.1, help="Typically 0.5 if unspecified.")
        with period_column:
            return_period = st.number_input("Return Period (years)", min_value=1, max_value=10000, value=50, step=1, help="Typically 50 years.")
        
        p = 1.0 / return_period
        numerator = 1.0 - K * math.log(-math.log(1.0 - p))
        denominator = 1.0 - K * math.log(-math.log(0.98))
        if abs(denominator) < 1e-9:
            st.warning("Denominator is close to zero; check K and standard reference. Setting c_prob = 1.")
            c_prob = 1.0
        else:
            c_prob = (numerator / denominator) ** n
    else:
        c_prob = 1.0

    st.write(f"Probability factor $c_{{prob}}$: {c_prob:.3f}")

    altitude = st.session_state.inputs.get("altitude", 20.0)
    # Altitude correction
    if z <= 10:
        case = "z ≤ 10m"
        altitude_equation = "c_{alt} = 1 + 0.001 × A"
        c_alt = 1 + 0.001 * altitude
    else:
        case = "z > 10m"
        altitude_equation = "c_{alt} = 1 + 0.001 × A × (10/z)^{0.2}"
        c_alt = 1 + 0.001 * altitude * (10 / z) ** 0.2
    st.session_state.inputs["c_alt"] = c_alt
    
    st.write(f"**Case: {case}**")
    st.latex(altitude_equation)
    st.write(f"Where A = {altitude}")
    st.write(f"Therefore, $c_{{alt}}$ = {c_alt:.3f}")
        
    # Calculate V_b0
    V_b0 = V_bmap * c_alt
    st.write(f"$V_{{b0}} = V_{{b,map}} × c_{{alt}} = {V_bmap:.2f} × {c_alt:.3f} = {V_b0:.2f}$ m/s")
        
    # Directional & seasonal factors
    c_dir = 1.0
    c_season = 1.0
    st.write(f"Directional factor $c_{{dir}}$: {c_dir}")
    st.write(f"Seasonal factor $c_{{season}}$: {c_season}")
        
    # Basic Wind Speed with c_prob included (UK)
    V_b = V_b0 * c_dir * c_season * c_prob
    st.session_state.results["V_b"] = V_b
        
    # Display the final result
    st.markdown("**Basic Wind Speed**")
    st.latex(f"V_b = c_{{dir}} × c_{{season}} × c_{{prob}} × V_{{b0}} = {V_b:.2f}\\; m/s")

else:
    # EU calculation - uses V_b,0 directly without altitude correction
    V_b0 = st.number_input("$v_{b,0}$ (m/s)", min_value=0.1, max_value=100.0, value=float(st.session_state.inputs.get("V_b0", 21.5)), step=0.1, help="Basic wind velocity for EU calculation")
    st.session_state.inputs["V_b0"] = V_b0

    if st.session_state.get("show_educational", False):
        st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
        with st.expander("What $v_{b,0}$ Value Should I Use?", expanded=False):
            st.markdown('<div class="educational-content">For EU calculations, use the basic wind velocity value directly from the relevant wind map or standards.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    use_custom_values = st.checkbox("Use custom K, n, and return period?")

    if use_custom_values:
        shape_column, exponent_column, period_column = st.columns(3)
        with shape_column:
            K = st.number_input("Shape parameter (K)", min_value=0.0, max_value=5.0, value=0.2, step=0.1, help="Typically 0.2 if unspecified.")
        with exponent_column:
            n = st.number_input("Exponent (n)", min_value=0.0, max_value=5.0, value=0.5, step=0.1, help="Typically 0.5 if unspecified.")
        with period_column:
            return_period = st.number_input("Return Period (years)", min_value=1, max_value=10000, value=50, step=1, help="Typically 50 years.")
        
        p = 1.0 / return_period
        numerator = 1.0 - K * math.log(-math.log(1.0 - p))
        denominator = 1.0 - K * math.log(-math.log(0.98))
        if abs(denominator) < 1e-9:
            st.warning("Denominator is close to zero; check K and standard reference. Setting c_prob = 1.")
            c_prob = 1.0
        else:
            c_prob = (numerator / denominator) ** n
    else:
        c_prob = 1.0

    st.write(f"Probability factor $c_{{prob}}$: {c_prob:.3f}")
    
    c_dir = 1.0
    c_season = 1.0
    st.write(f"Directional factor $c_{{dir}}$: {c_dir}")
    st.write(f"Seasonal factor $c_{{season}}$: {c_season}")
    
    V_b = c_dir * c_season * c_prob * V_b0
    st.session_state.results["V_b"] = V_b
    
    st.markdown("**Basic Wind Speed**")
    st.latex(f"V_b = c_{{dir}} × c_{{season}} × c_{{prob}} × V_{{b,0}} = {V_b:.2f}\\; m/s")

# ============================================================================
# DISPLACEMENT HEIGHT - Always needed for both UK and EU
# ============================================================================
from calc_engine.common.displacement import calculate_displacement_height, display_displacement_results

st.markdown("---")
st.subheader("Displacement Height $$h_{dis}$$")

# Calculate displacement height
h_dis = calculate_displacement_height(st)
display_displacement_results(st, h_dis)
st.session_state.inputs["h_dis"] = h_dis
z_minus_h_dis = z - h_dis
st.session_state.results["z_minus_h_dis"] = z_minus_h_dis

# Educational text on h_dis calculation
if st.session_state.get("show_educational", False):
    st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
    with st.expander("What Is $$h_{dis}$$ All About?", expanded=False):
        st.image("educational/images/h_dis_diagram.png", width="stretch")
        st.markdown(f'<div class="educational-content">{text_content.h_dis_help}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# PEAK WIND PRESSURE SECTION - Main calculation logic
# ============================================================================

def peak_pressure_section():
    st.markdown("---")
    st.subheader("Basic Wind Pressure $$q_{b}$$")

    # Get region
    region = st.session_state.inputs.get("region", "United Kingdom")

    # Determine region-specific default rho
    default_rho = 1.226 if region == "United Kingdom" else 1.25

    # If the user changed region since last run, reset rho_air to the region default
    last_region = st.session_state.inputs.get("last_region", None)
    if last_region != region:
        st.session_state.inputs["rho_air"] = default_rho
        st.session_state.inputs["last_region"] = region

    initial_rho = st.session_state.inputs.get("rho_air", float(default_rho))

    # Air density input
    rho_air = st.number_input(
        "Air Density (kg/m³)",
        min_value=1.0,
        max_value=2.0,
        value=float(initial_rho),
        step=0.001,
        format="%.3f"
    )
    st.session_state.inputs["rho_air"] = float(rho_air)
    
    # Basic wind pressure calculation
    v_b = st.session_state.results.get("V_b", 0.0)
    q_b = 0.5 * rho_air * (v_b ** 2)
    st.session_state.results["q_b"] = q_b
    
    st.write(f"Basic wind pressure: $q_b = 0.5 \\cdot \\rho \\cdot v_b^2 = 0.5 \\cdot {rho_air:.3f} \\cdot {v_b:.2f}^2 = {q_b:.2f}\\;\\mathrm{{N/m²}}$")
    
    # ========================================================================
    # UK CALCULATION PATH
    # ========================================================================
    if region == "United Kingdom":
        st.markdown("---")
        
        # Educational text on Orography Significance
        if st.session_state.get("show_educational", False):
            st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
            with st.expander("Is Orography Significant?", expanded=False):
                st.image("educational/images/Orography_Diagram.png", width="stretch")
                st.markdown(f'<div class="educational-content">{text_content.orography_help}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # CRITICAL DECISION POINT: Is orography significant?
        is_orography_significant = st.checkbox(
            "Orography is significant", 
            value=st.session_state.inputs.get("is_orography_significant", False),
            help="Check if the site has significant terrain features (hills, cliffs, ridges) per Figure NA.2"
        )
        st.session_state.inputs["is_orography_significant"] = is_orography_significant
        
        # Get common parameters
        from calc_engine.uk.contour_plots import load_contour_data
        from calc_engine.uk.peak_pressure import (
            calculate_uk_peak_pressure_no_orography,
            calculate_uk_peak_pressure_with_orography
        )
        
        # Load the contour data
        contour_data_path = "calc_engine/uk/contour_data.xlsx"
        datasets = load_contour_data(contour_data_path)
        
        # Get parameters from session state
        d_sea = st.session_state.inputs.get("d_sea", 60.0)
        z_minus_h_dis = st.session_state.results.get("z_minus_h_dis", 10.0)
        terrain = st.session_state.inputs.get("terrain_category", "").lower()
        z = st.session_state.inputs.get("z", 30.0)
        
        # ====================================================================
        # PATH 1: OROGRAPHY IS SIGNIFICANT
        # ====================================================================
        if is_orography_significant:           
            # Get orography factor from Annex A
            c_o = st.number_input(
                "Orography factor $c_o(z)$",
                min_value=0.0,
                max_value=5.0,
                value=st.session_state.inputs.get("c_o", 1.0),
                step=0.1,
                format="%.2f",
                help="Enter the orography factor for the site (from Annex A of EN 1991-1-4)"
            )
            st.session_state.inputs["c_o"] = c_o
            
            # Check if we need mean wind velocity (only for z > 50m)
            if z > 50:
                st.markdown("---")
                st.subheader("Mean Wind Velocity $$v_{m}$$")
                
                # Calculate roughness factor for UK
                st.markdown("#### Roughness Factor $C_r(z)$")
                
                from calc_engine.uk.roughness import calculate_uk_roughness
                
                # Calculate UK roughness factor
                c_rz = calculate_uk_roughness(st, datasets)
                
                # Get terrain type for UK calculation
                terrain_type = st.session_state.inputs.get("terrain_type", "")
                
                # Initialize terrain factor
                c_rT = 1.0
                
                # Check if terrain is "Town" for UK region
                if terrain_type == "Town":
                    c_rT = st.session_state.results.get("c_rT", 1.0)
                    st.session_state.results["c_rT"] = c_rT
                
                # Calculate mean wind velocity
                v_mean = v_b * c_rz * c_o
                st.session_state.results["v_mean"] = v_mean
                
                # Display the mean wind velocity result
                st.markdown("#### Mean Wind Velocity $$v_m(z)$$")
                st.write(f"$$v_m(z) = v_b \\cdot c_r(z) \\cdot c_o(z) = {v_b:.2f} \\cdot {c_rz:.3f} \\cdot {c_o:.2f} = {v_mean:.2f}\\;\\mathrm{{m/s}}$$")
            else:
                # For z ≤ 50m, we don't need v_m, but store a placeholder
                st.session_state.results["v_mean"] = 0.0
            
            # Now calculate peak pressure with orography
            st.markdown("---")
            st.subheader("Peak Velocity Pressure $q_p$")
            
            qp_value = calculate_uk_peak_pressure_with_orography(
                st, datasets, q_b, d_sea, z_minus_h_dis, terrain, z, c_o
            )
            st.session_state.results["qp_value"] = qp_value
        
        # ====================================================================
        # PATH 2: OROGRAPHY IS NOT SIGNIFICANT
        # ====================================================================
        else:
           
            # Set c_o to 1.0 for consistency (not used in calculation)
            st.session_state.inputs["c_o"] = 1.0
            
            # No mean wind velocity needed - go straight to peak pressure
            st.session_state.results["v_mean"] = 0.0
            
            st.markdown("---")
            st.subheader("Peak Velocity Pressure $$q_p(z)$$")
            
            qp_value = calculate_uk_peak_pressure_no_orography(
                st, datasets, q_b, d_sea, z_minus_h_dis, terrain
            )
            st.session_state.results["qp_value"] = qp_value
    
    # ========================================================================
    # EU CALCULATION PATH - Keep existing logic
    # ========================================================================
    else:
        # EU always calculates mean wind velocity
        st.markdown("---")
        st.subheader("Mean Wind Velocity $$v_{m}$$")
        
        from calc_engine.eu.roughness import display_eu_roughness_calculation
        
        z_minus_h_dis = st.session_state.results.get("z_minus_h_dis", 10.0)
        terrain_category = st.session_state.inputs.get("terrain_category", "II")
        
        # Calculate and display EU roughness factor
        c_rz = display_eu_roughness_calculation(st, z_minus_h_dis, terrain_category)
        
        # Get orography factor
        c_o = st.session_state.inputs.get("c_o", 1.0)
        
        # Calculate mean wind velocity
        v_mean = v_b * c_rz * c_o
        st.session_state.results["v_mean"] = v_mean
        
        # Display the mean wind velocity result
        st.markdown("#### Mean Wind Velocity $$v_m(z)$$")
        st.write(f"$$v_m(z) = v_b \\cdot c_r(z) \\cdot c_o(z) = {v_b:.2f} \\cdot {c_rz:.2f} \\cdot {c_o:.2f} = {v_mean:.2f}\\;\\mathrm{{m/s}}$$")
        
        # Educational text on Orography Significance (EU version)
        if st.session_state.get("show_educational", False):
            st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
            with st.expander("Is Orography Significant?", expanded=False):
                st.image("educational/images/Orography_Diagram.png", width="stretch")
                st.markdown(f'<div class="educational-content">{text_content.orography_help}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Calculate EU peak pressure
        st.markdown("---")
        st.subheader("Peak Velocity Pressure $$q_p(z)$$")
        
        from calc_engine.eu.peak_pressure import display_eu_peak_pressure_calculation
        
        qp_value = display_eu_peak_pressure_calculation(
            st, z_minus_h_dis, terrain_category, v_b, rho_air, c_o
        )
        st.session_state.results["qp_value"] = qp_value

# Call the peak pressure section
peak_pressure_section()

# Section 5: WIND ZONES
st.markdown("---")
st.subheader("Wind Zones")

st.write("#### Inset Storey")

# Checkbox to opt into adding an inset zone
add_inset = st.checkbox(
    "Add inset zone (upper storey)",
    value=bool(st.session_state.inputs.get("inset_enabled", False)),
    key="ui_add_inset", help="Enable to consider additional wind suction effects from inset zones as per PD 6688-1-4"
)
# persist the checkbox state
st.session_state.inputs["inset_enabled"] = bool(add_inset)

# Educational text on inset zone calculation
if st.session_state.get("show_educational", False):
    st.markdown('<div class="educational-expander">', unsafe_allow_html=True)

    with st.expander("What Are Inset Zones?", expanded=False):
        # st.image("educational/images/h_dis_diagram.png", width="stretch")
        st.markdown(f'<div class="educational-content">{text_content.inset_zone_help}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
if add_inset:
    # Show inputs when inset is enabled
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        north_offset = st.number_input("North offset (m)", min_value=0.0, max_value=1000.0, value=float(st.session_state.inputs.get("north_offset", 0.0)), step=0.1, key="ui_north_offset")
        st.session_state.inputs["north_offset"] = float(north_offset)

    with c2:
        south_offset = st.number_input("South offset (m)", min_value=0.0, max_value=1000.0, value=float(st.session_state.inputs.get("south_offset", 4.0)), step=0.1, key="ui_south_offset")
        st.session_state.inputs["south_offset"] = float(south_offset)

    with c3:
        east_offset = st.number_input("East offset (m)", min_value=0.0, max_value=1000.0, value=float(st.session_state.inputs.get("east_offset", 0.0)), step=0.1, key="ui_east_offset")
        st.session_state.inputs["east_offset"] = float(east_offset)

    with c4:
        west_offset = st.number_input("West offset (m)", min_value=0.0, max_value=1000.0, value=float(st.session_state.inputs.get("west_offset", 4.0)), step=0.1, key="ui_west_offset")
        st.session_state.inputs["west_offset"] = float(west_offset)

    # Inset (upper storey) vertical height
    inset_col1, inset_col2 = st.columns([1, 2])
    with inset_col1:
        inset_height = st.number_input("Inset height H1 (m)", min_value=0.0, max_value=500.0, value=float(st.session_state.inputs.get("inset_height", 10.0)), step=0.1, key="ui_inset_height")
        st.session_state.inputs["inset_height"] = float(inset_height)

    # Call the visualiser with the stored values
    call_inset_height = float(st.session_state.inputs.get("inset_height", 4.0))
    call_north_offset = float(st.session_state.inputs.get("north_offset", 5.0))
    call_south_offset = float(st.session_state.inputs.get("south_offset", 0.0))
    call_east_offset  = float(st.session_state.inputs.get("east_offset", 5.0))
    call_west_offset  = float(st.session_state.inputs.get("west_offset", 0.0))

    results, fig = detect_zone_E_and_visualise(
        st.session_state,
        inset_height=call_inset_height,
        north_offset=call_north_offset,
        south_offset=call_south_offset,
        east_offset=call_east_offset,
        west_offset=call_west_offset,
    )

    # store + display
    st.session_state["inset_results"] = results
    st.session_state["inset_fig"] = fig

    # Store inset results in inputs for export
    st.session_state.results["inset_results"] = results

    st.plotly_chart(fig, width="stretch")
        
    # Display styled dataframe
    styled_df = create_styled_inset_dataframe(results)
    st.dataframe(styled_df)

else:
    # Inset disabled: do NOT show inputs or visualisation.
    # Preserve previously-entered numeric values in session_state.inputs, but do not call the visualiser.
    st.session_state["inset_results"] = None
    st.session_state["inset_fig"] = None   

st.markdown("---")
st.write("#### Funnelling")
# Import required modules
from visualisation.wind_zones import plot_wind_zones
from calc_engine.common.external_pressure import calculate_cpe, display_funnelling_inputs, display_elevation_results

# Add checkbox to control funnelling consideration
consider_funnelling = st.checkbox(
    "Consider Funnelling Effects",
    value=bool(st.session_state.inputs.get("consider_funnelling", False)),
    help="Enable to consider funnelling effects between buildings as per BS EN 1991-1-4"
)

# persist the checkbox state
st.session_state.inputs["consider_funnelling"] = bool(consider_funnelling)
# Educational text on funnelling calculation
if st.session_state.get("show_educational", False):
    st.markdown('<div class="educational-expander">', unsafe_allow_html=True)

    with st.expander("What Is Funnelling?", expanded=False):
        # st.image("educational/images/h_dis_diagram.png", width="stretch")
        st.markdown(f'<div class="educational-content">{text_content.funnelling_help}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
# Display funnelling inputs regardless of whether funnelling is enabled
if consider_funnelling == True:
    north_gap, south_gap, east_gap, west_gap = display_funnelling_inputs()

    # Store gap values in session state
    st.session_state.inputs["north_gap"] = float(north_gap)
    st.session_state.inputs["south_gap"] = float(south_gap)
    st.session_state.inputs["east_gap"] = float(east_gap)
    st.session_state.inputs["west_gap"] = float(west_gap)

st.markdown("---")
st.write('### External Pressure Coefficients $$c_{p,e}$$')

# Loaded area input. This will only appear when region is EU
region = st.session_state.inputs.get("region", "United Kingdom")
if region != "United Kingdom":  # Show for EU region
    loaded_area = st.number_input(
        "Loaded Area (m²)", 
        min_value=0.1, 
        max_value=100.0, 
        value=10.0, 
        step=0.1, 
        help="Area over which the wind load is applied. Used for interpolating between Cpe,1 and Cpe,10 values.", 
        key="loaded_area_input"
    )
    st.session_state.inputs["loaded_area"] = loaded_area

# Automatically calculate cp,e values with or without funnelling based on checkbox
cp_results_by_elevation = calculate_cpe(consider_funnelling=consider_funnelling)
    
# Get building dimensions from session state
h = st.session_state.inputs.get("z", 10.0)  # Building height
NS_dimension = st.session_state.inputs.get("NS_dimension", 20.0)
EW_dimension = st.session_state.inputs.get("EW_dimension", 40.0)

# Display results for each elevation using our new function
elevations = ["North", "East", "South", "West"]
for elevation in elevations:
    display_elevation_results(
        elevation=elevation, 
        cp_results=cp_results_by_elevation, 
        h=h, 
        NS_dimension=NS_dimension, 
        EW_dimension=EW_dimension
    )

# Store overall results for later use (combine all directions)
all_results = []
for direction, df in cp_results_by_elevation.items():
    df_with_direction = df.copy()
    df_with_direction["Wind Direction"] = direction
    all_results.append(df_with_direction)

# STORE CP RESULTS - Combined DataFrame with all directions
cp_results_combined = pd.concat(all_results, ignore_index=True)
st.session_state.results['cp_results'] = cp_results_combined

# Educational text on wind zone plots
if st.session_state.get("show_educational", False):
    st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
    with st.expander("How Are Wind Zones Plotted?", expanded=False):
        st.image("educational/images/wind_zones_diagram.png", width="stretch")
        st.markdown(f'<div class="educational-content">{text_content.wind_zone_help}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Display wind zone plots (using your existing function)
ns_elevation_fig, ew_elevation_fig = plot_wind_zones(st.session_state)

# Display North-South Elevation
st.plotly_chart(ns_elevation_fig, width="stretch")

# Display East-West Elevation
st.plotly_chart(ew_elevation_fig, width="stretch")

# Results Summary section
st.markdown("---")
st.markdown('<div class="pagebreak"></div>', unsafe_allow_html=True)
st.subheader("Net Pressures")

# Educational text on Wind Pressure Profile
if st.session_state.get("show_educational", False):
    st.markdown('<div class="educational-expander">', unsafe_allow_html=True)
    with st.expander("How Is Net Pressure Calculated?", expanded=False):
        st.image("educational/images/We_Wi.png", width="stretch")
        st.markdown(f'<div class="educational-content">{text_content.net_pressure_help}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

from calc_engine.common.pressure_summary import create_pressure_summary, plot_elevation_with_pressures

# Calculate pressure summary
results_by_direction = calculate_cpe()  # Make sure this function exists
summary_df = create_pressure_summary(st.session_state, results_by_direction)

# STORE PRESSURE SUMMARY
st.session_state.results['summary_df'] = summary_df

# Create elevation figures with pressures
elevation_figures = plot_elevation_with_pressures(st.session_state, results_by_direction)

# Display results
st.subheader("Pressure Summary")
st.dataframe(summary_df, hide_index=True, height=35*len(summary_df)+38)

# Display figures
for direction, fig in elevation_figures.items():
    st.plotly_chart(fig, width="stretch")

# 3D Visualization (if educational mode enabled)
if st.session_state.get("show_educational", False):
    st.subheader("3D Wind Visualization") 
    from calc_engine.common.pressure_summary import create_wind_visualization_ui
    create_wind_visualization_ui(st.session_state, results_by_direction)

# Results Summary section
st.markdown("---")
st.subheader("Summary")

summary_paragraphs = generate_pressure_summary_paragraphs(st.session_state, results_by_direction)
for p in summary_paragraphs:
    st.markdown(p)
st.session_state.results['summary_paragraphs'] = summary_paragraphs

# ============================================================================
# SIDEBAR - Report Export
# ============================================================================
st.session_state.show_educational = show_educational

st.sidebar.markdown("---")

st.sidebar.header("📊 Report Export")

# Optional project name input for PDF header
project_name_input = st.sidebar.text_input(
    "Project Name (optional)",
    value=st.session_state.inputs.get("project_name", "") if hasattr(st.session_state, 'inputs') else "",
    help="Customize the PDF report header",
    placeholder="e.g., My Wind Load Project",
    key="pdf_project_name_override"
)

# Generate PDF report
st.sidebar.subheader("📄 PDF Report")
add_pdf_download_button(
    project_name=project_name_input if project_name_input else None
)

st.sidebar.markdown("---")
# ============================================================================
# SIDEBAR - Session Save/Load
# ============================================================================

# Session Save
add_session_save_ui()

st.sidebar.markdown("---")

# Session Load
add_session_load_ui()

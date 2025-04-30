import streamlit as st
import datetime
import math
import pandas as pd
import openpyxl
from auth import authenticate_user
from calc_engine.uk.terrain import get_terrain_categories as get_uk_terrain
from calc_engine.eu.terrain import get_terrain_categories as get_eu_terrain
from visualisation.building_viz import create_building_visualisation
from educational import text_content

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

TT_ORANGE = "rgb(211,69,29)"
# Add print-specific CSS - minimal version
st.markdown(f"""
<style>
/* Your existing print CSS */
@media print {{
    /* Hide UI elements in print mode */
    .stApp header, .stApp footer, .stSidebar, .stButton, 
    .educational-content, .navigation-section {{
        display: none !important;
    }}
    
    /* Hide number input +/- buttons and help icons */
    .stNumberInput button, .stNumberInput svg,
    [data-testid="stToolbar"], 
    .stTooltipIcon,
    .stTabs button[data-baseweb="tab-list"] {{
        display: none !important;
    }}
    
    /* Format printable content */
    .print-friendly {{
        page-break-inside: avoid;
        margin: 20px 0;
    }}
    
    /* Prevent images and charts from being split across pages */
    img, svg, figure, 
    .stPlot, .element-container, 
    [data-testid="stImage"], [data-testid="stPlotlyChart"],
    [data-testid="stDecoration"], [data-testid="stMetric"] {{
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }}
    
    /* Additional print optimization */
    @page {{
        margin: 1cm;
    }}
}}

/* Educational content styling */
.educational-content {{
    font-size: 0.8rem;
    color: {TT_ORANGE};
}}

/* Custom styling for expander when used for educational content */
.educational-expander .streamlit-expanderHeader {{
    background-color: rgba(211, 69, 29, 0.1);
    border-radius: 5px;
    font-weight: bold;
    color: {TT_ORANGE};
}}

.educational-expander .streamlit-expanderContent {{
    background-color: rgba(211, 69, 29, 0.05);
    border-left: 3px solid {TT_ORANGE};
    padding: 10px;
    font-size: 0.8rem;
}}

/* Remove educational content from printing */
@media print {{
    .educational-expander {{
        display: none !important;
    }}
}}
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

# Create three equal-width columns for inputs
col1, col2, col3 = st.columns(3)

# North-South Dimension input
with col1:
    NS_dimension = st.number_input(
        "North-South Dimension (m)",
        min_value=1.0,
        max_value=500.0,
        value=float(st.session_state.inputs.get("NS_dimension", 30.0)),
        step=1.0
    )

# East-West Dimension input
with col2:
    EW_dimension = st.number_input(
        "East-West Dimension (m)",
        min_value=1.0,
        max_value=500.0,
        value=float(st.session_state.inputs.get("EW_dimension", 30.0)),
        step=1.0
    )

# Building Height input
with col3:
    z = st.number_input(
        "Building Height (m)",
        min_value=1.0,
        max_value=500.0,
        value=float(st.session_state.inputs.get("z", 30.0)),
        step=1.0
    )

# Save geometry inputs to session state
st.session_state.inputs["NS_dimension"] = NS_dimension
st.session_state.inputs["EW_dimension"] = EW_dimension
st.session_state.inputs["z"] = z

# 3D visualization of the building
building_fig = create_building_visualisation(
    NS_dimension,
    EW_dimension,
    z
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

    if region == "United Kingdom" and selected_code.lower() == "town":
        d_default = float(st.session_state.inputs.get("d_town_terrain", 5.0))
        d_town_terrain = st.number_input(
            "Distance inside Town Terrain (km)",
            min_value=0.1,
            max_value=50.0,
            value=d_default,
            step=0.1,
        )
        st.session_state.inputs["d_town_terrain"] = d_town_terrain

    # Display educational content if the toggle is enabled in the sidebar
    if st.session_state.get("show_educational", False):
        # Use the direct expander styling from Streamlit
        with st.expander("📚 Educational Content: Terrain Types", expanded=True):
            # Display an image from the educational folder
            st.image("educational/images/Terrain_Cat.png", caption="Terrain Types")
            st.markdown(f'<div class="educational-content">{text_content.terrain_help}</div>', unsafe_allow_html=True)
render_terrain_category()

# Section 3: WIND VELOCITY
st.markdown("---")
st.header("Wind Velocity")
st.subheader("Basic Wind Velocity")

# Vb,map input
V_bmap = st.number_input(
    "$$v_{b,map}$$ (m/s)",
    min_value=0.1,
    max_value=100.0,
    value=float(st.session_state.inputs.get("V_bmap", 21.5)),
    step=0.1,
    help="Fundamental wind velocity from Figure 3.2"
)
st.session_state.inputs["V_bmap"] = V_bmap
# Let the user choose whether they want to override standard K, n, return period
use_custom_values = st.checkbox("Use custom K, n, and return period?")

if use_custom_values:
    # Create three columns for input
    shape_column, exponent_column, period_column = st.columns(3)
    with shape_column:
        K = st.number_input(
            "Shape parameter (K)",
            min_value=0.0,
            max_value=5.0,
            value=0.2,
            step=0.1,
            help="Typically 0.2 if unspecified."
        )
    with exponent_column:
        n = st.number_input(
            "Exponent (n)",
            min_value=0.0,
            max_value=5.0,
            value=0.5,
            step=0.1,
            help="Typically 0.5 if unspecified."
        )
    with period_column:
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

# Display the probability factor
st.write(f"Probability factor $c_{{prob}}$: {c_prob:.3f}")

# Altitude correction - display the case and working
if z <= 10:
    case = "z ≤ 10m"
    altitude_equation = "c_{alt} = 1 + 0.001 × A"
    c_alt = 1 + 0.001 * altitude_factor
else:
    case = "z > 10m"
    altitude_equation = "c_{alt} = 1 + 0.001 × A × (10/z)^{0.2}"
    c_alt = 1 + 0.001 * altitude_factor * (10 / z) ** 0.2

st.write(f"**Case: {case}**")
st.latex(altitude_equation)
st.write(f"Where A = {altitude_factor}")
st.write(f"Therefore, $c_{{alt}}$ = {c_alt:.3f}")
    
# Calculate V_b0
V_b0 = V_bmap * c_alt
st.write(f"$V_{{b0}} = V_{{b,map}} × c_{{alt}} = {V_bmap:.2f} × {c_alt:.3f} = {V_b0:.2f}$ m/s")
    
# Directional & seasonal factors
c_dir = 1.0
c_season = 1.0
st.write(f"Directional factor $c_{{dir}}$: {c_dir}")
st.write(f"Seasonal factor $c_{{season}}$: {c_season}")
    
# Basic Wind Speed with c_prob included
V_b = V_b0 * c_dir * c_season * c_prob
st.session_state.inputs["V_b"] = V_b
    
# Display the final result
st.markdown("**Basic Wind Speed**")
st.latex(f"V_b = V_{{b0}} × c_{{dir}} × c_{{season}} × c_{{prob}} = {V_b:.2f}\\; m/s")

# Import needed modules
from calc_engine.common.displacement import calculate_displacement_height, display_displacement_results
from calc_engine.common.util import get_session_value, store_session_value

def wind_velocity_section():
    """Display the Mean Wind Velocity section."""
    st.subheader("Mean Wind Velocity")
    
    # Calculate displacement height
    h_dis = calculate_displacement_height(st)
    display_displacement_results(st, h_dis)
    
    # Check the region selection
    region = get_session_value(st, "region")
    z_minus_h_dis = get_session_value(st, "z_minus_h_dis")
    
    # Calculate roughness factor based on region
    if region == "United Kingdom":
        st.markdown("#### Roughness Factor $C_r(z)$")
        
        # Import the UK contour plot functions
        from calc_engine.uk.contour_plots import load_contour_data
        from calc_engine.uk.roughness import calculate_uk_roughness
        
        # Load the contour data
        contour_data_path = "calc_engine/uk/contour_data.xlsx"
        datasets = load_contour_data(contour_data_path)
        
        # Calculate UK roughness factor
        c_rz = calculate_uk_roughness(st, datasets)
        
        # Get terrain type for UK calculation
        terrain_type = get_session_value(st, "terrain_type", "")
        
        # Initialize terrain factor
        c_rT = 1.0
        
        # Check if terrain is "Town" for UK region
        if terrain_type == "Town":
            # Get the terrain factor c_rT from session state or use default 1.0
            c_rT = get_session_value(st, "c_rT", 1.0)
            store_session_value(st, "c_rT", c_rT)
    else:
        # Use EU roughness calculation
        from calc_engine.eu.roughness import display_eu_roughness_calculation
        
        # Get terrain category from session state
        terrain_category = get_session_value(st, "terrain_category", "II")
        
        # Calculate and display EU roughness factor
        c_rz = display_eu_roughness_calculation(st, z_minus_h_dis, terrain_category)
        
        # No terrain factor for EU calculation
        c_rT = 1.0
    
    # Calculate mean wind velocity
    v_b = get_session_value(st, "V_b", 0.0)
    c_oz = get_session_value(st, "c_oz", 1.0)
    
    v_mean = v_b * c_rz * c_oz
    store_session_value(st, "v_mean", v_mean)
 
    # Display the mean wind velocity result
    st.markdown("#### Mean Wind Velocity")
    st.write(f"$$v_m(z) = v_b \\cdot c_r(z) \\cdot c_o(z) = {v_b:.2f} \\cdot {c_rz:.2f} \\cdot {c_oz:.2f} = {v_mean:.2f}\\;\\mathrm{{m/s}}$$")

wind_velocity_section()

def peak_pressure_section():
    """Display the Peak Wind Pressure section."""
    st.markdown("---")
    st.header("Peak Wind Pressure")
    
    # Air density input
    rho_air = st.number_input(
        "Air Density (kg/m³)",
        min_value=1.0,
        max_value=2.0,
        value=1.226,
        step=0.001,
        format="%.3f"
    )
    store_session_value(st, "rho_air", rho_air)
    
    # Basic wind pressure calculation
    v_b = get_session_value(st, "V_b", 0.0)
    q_b = 0.5 * rho_air * (v_b ** 2)
    store_session_value(st, "q_b", q_b)
    
    st.write(f"Basic wind pressure: $q_b = 0.5 \\cdot \\rho \\cdot v_b^2 = 0.5 \\cdot {rho_air:.3f} \\cdot {v_b:.2f}^2 = {q_b:.2f}\\;\\mathrm{{N/m²}}$")
    
    # Check the region selection for peak pressure calculation
    region = get_session_value(st, "region")
    z_minus_h_dis = get_session_value(st, "z_minus_h_dis", 10.0)
    
    if region == "United Kingdom":
        from calc_engine.uk.contour_plots import load_contour_data
        from calc_engine.uk.peak_pressure import calculate_uk_peak_pressure
        
        # Load the contour data
        contour_data_path = "calc_engine/uk/contour_data.xlsx"
        datasets = load_contour_data(contour_data_path)
        
        # Calculate UK peak pressure
        qp_value = calculate_uk_peak_pressure(st, datasets, q_b)
    else:
        from calc_engine.eu.peak_pressure import display_eu_peak_pressure_calculation
        
        # Get parameters
        terrain_category = get_session_value(st, "terrain_category", "II")
        c_o = get_session_value(st, "c_oz", 1.0)
        
        # Calculate EU peak pressure
        qp_value = display_eu_peak_pressure_calculation(
            st, z_minus_h_dis, terrain_category, v_b, rho_air, c_o
        )
peak_pressure_section()

# --- Section 5: Wind Pressure Profile ---
st.markdown("---")
st.write("## Wind Pressure Profile")

# Import the pressure profile functions
from calc_engine.common.shape_velocity_profile import (
    get_profile_case, 
    create_wind_pressure_plot, 
    create_pressure_table, 
    calculate_design_pressure
)

# Get the peak velocity pressure from previous calculations
qp_value = st.session_state.inputs.get("qp_value", 0.0)

# Get building height from session state
h = st.session_state.inputs.get("z", 10.0)
NS_dimension = st.session_state.inputs.get("NS_dimension", 20.0)
EW_dimension = st.session_state.inputs.get("EW_dimension", 15.0)

# Create and display plots for both directions
st.write("### North-South Direction")
NS_fig, NS_profile_case = create_wind_pressure_plot(h, NS_dimension, qp_value, "NS")
st.plotly_chart(NS_fig, use_container_width=True)

st.write("### East-West Direction")
EW_fig, EW_profile_case = create_wind_pressure_plot(h, EW_dimension, qp_value, "EW")
st.plotly_chart(EW_fig, use_container_width=True)

# Display tables and design pressures for both directions
st.subheader("Wind Pressure Values at Key Heights")

# NS Direction
st.write("#### North-South Direction")
NS_df = create_pressure_table(h, NS_dimension, qp_value)
st.dataframe(NS_df, hide_index=True)
NS_design_pressure = calculate_design_pressure(h, NS_dimension, qp_value)
st.session_state.inputs["NS_design_pressure"] = NS_design_pressure

# EW Direction
st.write("#### East-West Direction")
EW_df = create_pressure_table(h, EW_dimension, qp_value)
st.dataframe(EW_df, hide_index=True)
EW_design_pressure = calculate_design_pressure(h, EW_dimension, qp_value)
st.session_state.inputs["EW_design_pressure"] = EW_design_pressure

# Section 5: WIND ZONES
st.markdown("---")
st.header("Wind Zones")
# Import required modules
from visualisation.wind_zones import plot_wind_zones
from calc_engine.common.external_pressure import calculate_cpe, display_funnelling_inputs
# Display funnelling inputs regardless of region
north_gap, south_gap, east_gap, west_gap = display_funnelling_inputs()

# Automatically calculate cp,e values without requiring a button click
cp_results_by_direction = calculate_cpe()

st.subheader("External Pressure Coefficients (cp,e)")

# Calculate the required values for display
cp_results_by_elevation = calculate_cpe()  # Run the calculation function

# Get building dimensions from session state
h = st.session_state.inputs.get("z", 10.0)  # Building height
NS_dimension = st.session_state.inputs.get("NS_dimension", 20.0)
EW_dimension = st.session_state.inputs.get("EW_dimension", 40.0)

# Display results for each elevation in separate sections
# North Elevation
st.write("#### North Elevation")
# Calculate values for North elevation
north_h_d = h / NS_dimension
north_b = EW_dimension
north_e = min(north_b, 2*h)
north_gap = st.session_state.inputs.get("north_gap", 10.0)
funnelling_status = ""
if north_gap <= north_e/4:
    funnelling_status = "No Funnelling since **gap ≤ e/4**"
elif north_gap >= north_e:
    funnelling_status = "No Funnelling since **gap ≥ e**"
else:
    funnelling_status = "Funnelling Applied since **e/4 < gap < e**"
st.write(f"h/d = {north_h_d:.2f}, e = {north_e:.2f}m, gap = {north_gap:.2f}m ({funnelling_status})")
st.dataframe(cp_results_by_elevation["North"], hide_index=True)

# East Elevation
st.write("#### East Elevation")
# Calculate values for East elevation
east_h_d = h / EW_dimension
east_b = NS_dimension
east_e = min(east_b, 2*h)
east_gap = st.session_state.inputs.get("east_gap", 10.0)
funnelling_status = ""
if east_gap <= east_e/4:
    funnelling_status = "No Funnelling since **gap ≤ e/4**"
elif east_gap >= east_e:
    funnelling_status = "No Funnelling since **gap ≥ e**"
else:
    funnelling_status = "Funnelling Applied since **e/4 < gap < e**"
st.write(f"h/d = {east_h_d:.2f}, e = {east_e:.2f}m, gap = {east_gap:.2f}m ({funnelling_status})")
st.dataframe(cp_results_by_elevation["East"], hide_index=True)

# South Elevation
st.write("#### South Elevation")
# Calculate values for South elevation
south_h_d = h / NS_dimension
south_b = EW_dimension
south_e = min(south_b, 2*h)
south_gap = st.session_state.inputs.get("south_gap", 10.0)
funnelling_status = ""
if south_gap <= south_e/4:
    funnelling_status = "No Funnelling since **gap ≤ e/4**"
elif south_gap >= south_e:
    funnelling_status = "No Funnelling since **gap ≥ e**"
else:
    funnelling_status = "Funnelling Applied since **e/4 < gap < e**"
st.write(f"h/d = {south_h_d:.2f}, e = {south_e:.2f}m, gap = {south_gap:.2f}m ({funnelling_status})")
st.dataframe(cp_results_by_elevation["South"], hide_index=True)

# West Elevation
st.write("#### West Elevation")
# Calculate values for West elevation
west_h_d = h / EW_dimension
west_b = NS_dimension
west_e = min(west_b, 2*h)
west_gap = st.session_state.inputs.get("west_gap", 10.0)
funnelling_status = ""
if west_gap <= west_e/4:
    funnelling_status = "No Funnelling since **gap ≤ e/4**"
elif west_gap >= west_e:
    funnelling_status = "No Funnelling since **gap ≥ e**"
else:
    funnelling_status = "Funnelling Applied since **e/4 < gap < e**"
st.write(f"h/d = {west_h_d:.2f}, e = {west_e:.2f}m, gap = {west_gap:.2f}m ({funnelling_status})")
st.dataframe(cp_results_by_elevation["West"], hide_index=True)

# Store overall results for later use (combine all directions)
all_results = []
for direction, df in cp_results_by_direction.items():
    df_with_direction = df.copy()
    df_with_direction["Wind Direction"] = direction
    all_results.append(df_with_direction)

st.session_state.cp_results = pd.concat(all_results)

# Display wind zone plots (using your existing function)
ns_elevation_fig, ew_elevation_fig = plot_wind_zones(st.session_state)
# Display North-South Elevation
st.plotly_chart(ns_elevation_fig, use_container_width=True)
# Display East-West Elevation
st.plotly_chart(ew_elevation_fig, use_container_width=True)

# Section 6: RESULTS SUMMARY
st.markdown("---")
st.header("Results Summary")
from calc_engine.common.pressure_summary import create_pressure_summary, plot_elevation_with_pressures, visualize_wind_pressures

results_by_direction = calculate_cpe()  # Make sure this function exists
summary_df = create_pressure_summary(st.session_state, results_by_direction)
elevation_figures = plot_elevation_with_pressures(st.session_state, results_by_direction)

# Display results manually
st.subheader("Pressure Summary")
st.dataframe(summary_df, hide_index=True, height=35*len(summary_df)+38)

# Display figures
for direction, fig in elevation_figures.items():
    st.plotly_chart(fig)

# Toggle educational content in sidebar
st.sidebar.title("Options")
show_educational = st.sidebar.checkbox("Show Educational Content", 
                              value=st.session_state.show_educational)
st.session_state.show_educational = show_educational

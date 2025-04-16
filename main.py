import streamlit as st
import datetime
import math
import os
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
    
    # Display the result
    st.markdown("**Calculated Basic Wind Speed**")
    st.latex(f"V_b = {V_b:.2f}\\; m/s")
    st.write(f"(Probability factor used: {c_prob:.3f})")

st.subheader("Mean Wind Velocity")

region = st.session_state.inputs.get("region", "").lower()

# Check the region selection
region = st.session_state.inputs.get("region")
if region == "United Kingdom":
    st.markdown("### Roughness Factor")
    
    # Import the contour plot functions for UK
    from calc_engine.uk.contour_plots import load_contour_data, get_interpolated_value, display_single_plot
    
    # Get required parameters from session state
    z = st.session_state.inputs.get("height", 10.0)  # Get height from session state
    x_upwind = st.session_state.inputs.get("distance_upwind", 10.0)  # Distance to shoreline
    
    # Create columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Allow user to override the calculated value (optional)
        use_calculated = st.checkbox("Use calculated value from contour plot", value=True)
        
        # Allow user to adjust parameters
        z_input = st.number_input(
            "Height above ground (m)",
            min_value=2.0,
            max_value=200.0,
            value=z,
            format="%.1f"
        )
        st.session_state.inputs["height"] = z_input
        
        x_upwind_input = st.number_input(
            "Distance upwind to shoreline (km)",
            min_value=0.1,
            max_value=100.0,
            value=x_upwind,
            format="%.1f"
        )
        st.session_state.inputs["distance_upwind"] = x_upwind_input
    
    # Load the contour data
    contour_data_path = os.path.join("calc_engine", "uk", "contour_data.xlsx")
    datasets = load_contour_data(contour_data_path)
    
    # Get interpolated c_r(z) value from NA.3
    interpolated_c_r = get_interpolated_value(datasets, "NA.3", x_upwind_input, z_input)
    
    with col2:
        # Display NA.3 plot
        display_single_plot(st, datasets, "NA.3", x_upwind_input, z_input)
    
    # Set c_r based on user's choice
    if use_calculated and interpolated_c_r is not None:
        c_r = interpolated_c_r
        st.success(f"Using calculated value: c_r(z) = {c_r:.3f}")
    else:
        # If user chooses to enter manually or if interpolation failed
        c_r = st.number_input(
            "Enter roughness factor value manually",
            min_value=0.0,
            max_value=5.0,
            value=float(st.session_state.inputs.get("uk_roughness_factor", 1.0)),
            step=0.01,
            format="%.3f"
        )
    
    # Save the UK roughness factor to session state
    st.session_state.inputs["uk_roughness_factor"] = c_r
    
    st.latex(f"c_r(z) = {c_r:.3f}")
    
    # Additional information about the calculation method
    with st.expander("About this calculation"):
        st.info("The roughness factor c_r(z) is interpolated from Figure NA.3 in the UK National Annex to BS EN 1991-1-4. The value depends on the height above ground and the distance upwind to shoreline.")

else:
    # Import the roughness function from the EU module
    from calc_engine.eu import roughness as roughness_module
    
    # Assume that a terrain category was selected via a dropdown earlier, stored in session_state
    terrain_category = st.session_state.inputs.get("terrain_category", "II")  # default to Category II if not set
    
    # Now call the roughness function
    try:
        c_r = roughness_module.calculate_cr(z, terrain_category)
        st.markdown("### Roughness Factor")
        st.write(f"The roughness factor, \\(c_r(z)\\), for terrain category **{terrain_category}** and height **{z} m** is:")
        st.latex(f"c_r(z) = {c_r:.3f}")
    except Exception as e:
        st.error(f"Error calculating roughness factor: {e}")
        
# Section 4: WIND PRESSURE
st.markdown("---")
st.header("Peak Wind Pressure")
st.info("Peak Wind Pressure will be added here")

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

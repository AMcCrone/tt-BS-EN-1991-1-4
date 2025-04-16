import streamlit as st
import datetime
from calc_engine.uk.terrain import get_terrain_categories as get_uk_terrain
from calc_engine.eu.terrain import get_terrain_categories as get_eu_terrain

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
    region_options = ["United Kingdom", "European Union"]
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

# Future sections will go here (terrain categories, building parameters, etc.)
# Section 2: Terrain Categories
st.header("2. Terrain Categories")
st.info("Terrain category inputs will be added here")

# Section 3: Building Parameters
st.markdown("---")
st.header("3. Building Parameters")
st.info("Building parameter inputs will be added here")

# Section 4: Site Conditions
st.markdown("---")
st.header("4. Site Conditions")
st.info("Site condition inputs will be added here")

# Section 5: Calculation Results
st.markdown("---")
st.header("5. Calculation Results")
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

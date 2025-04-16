import streamlit as st
import datetime

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
    st.session_state.region = None
    st.session_state.current_page = "region_selection"
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

# Page routing based on current_page
if st.session_state.current_page == "region_selection":
    # Project Location UI
    st.header("Project Information")
    
    # Create two columns for the form elements
    col1, col2 = st.columns(2)
    
    with col1:
        # Project details
        project_name = st.text_input("Project Name", 
                              value=st.session_state.inputs.get("project_name", ""))
        project_reference = st.text_input("Project Reference", 
                              value=st.session_state.inputs.get("project_reference", ""))
        
        # Location details
        location_name = st.text_input("Location", 
                              value=st.session_state.inputs.get("location_name", ""))
        
    with col2:
        # Country selection
        countries = ["United Kingdom", "Other European Country"]
        country = st.selectbox("Country", 
                       options=countries,
                       index=countries.index(st.session_state.inputs.get("country", "United Kingdom")) 
                       if st.session_state.inputs.get("country") in countries else 0)
        
        # Region selection (for UK)
        if country == "United Kingdom":
            uk_regions = ["England", "Scotland", "Wales", "Northern Ireland"]
            region = st.selectbox("Region", 
                         options=uk_regions,
                         index=uk_regions.index(st.session_state.inputs.get("region", "England")) 
                         if st.session_state.inputs.get("region") in uk_regions else 0)
        else:
            # Terrain category selection for non-UK European countries
            terrain_categories = ["0 - Sea or coastal area", 
                                 "I - Lakes or flat and horizontal area with negligible vegetation",
                                 "II - Area with low vegetation and isolated obstacles",
                                 "III - Area with regular cover of vegetation or buildings",
                                 "IV - Area where at least 15% of surface is covered with buildings"]
            terrain_category = st.selectbox("Terrain Category", 
                                  options=terrain_categories,
                                  index=terrain_categories.index(st.session_state.inputs.get("terrain_category", terrain_categories[0])) 
                                  if st.session_state.inputs.get("terrain_category") in terrain_categories else 0)
    
    # Altitude information
    st.subheader("Altitude Information")
    col3, col4 = st.columns(2)
    
    with col3:
        altitude = st.number_input("Site Altitude Above Sea Level (m)", 
                          min_value=0.0, max_value=1000.0, 
                          value=float(st.session_state.inputs.get("altitude", 0.0)), 
                          step=10.0)
    
    with col4:
        height_above_ground = st.number_input("Height Above Ground / Reference Height (m)", 
                                    min_value=0.0, max_value=500.0, 
                                    value=float(st.session_state.inputs.get("height_above_ground", 10.0)), 
                                    step=1.0)

    st.markdown("---")
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    
    with col_nav3:
        if st.button("Next →"):
            # Save inputs to session state
            st.session_state.inputs["project_name"] = project_name
            st.session_state.inputs["project_reference"] = project_reference
            st.session_state.inputs["location_name"] = location_name
            st.session_state.inputs["country"] = country
            
            if country == "United Kingdom":
                st.session_state.inputs["region"] = region
                st.session_state.region = region
            else:
                st.session_state.inputs["terrain_category"] = terrain_category
            
            st.session_state.inputs["altitude"] = altitude
            st.session_state.inputs["height_above_ground"] = height_above_ground
            
            # Proceed to next page
            st.session_state.current_page = "building_parameters"
            st.experimental_rerun()

# Simple footer
st.markdown(f"""
<div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #f0f2f6; padding: 0.5rem; text-align: center; font-size: 0.8rem; color: #666; border-top: 1px solid #ddd;">
    Wind Load Calculator v{APP_VERSION} | © {datetime.datetime.now().year}
</div>
""", unsafe_allow_html=True)

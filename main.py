import streamlit as st
import datetime

# App version and metadata
APP_VERSION = "1.0.0"
LAST_UPDATED = "April 15, 2025"

# Setup page configuration with a favicon
st.set_page_config(
    page_title="Wind Load Calculator",
    page_icon="🌪️",
    layout="wide"
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
st.image("educational/images/TT_Logo_Stacked_Colour.png", width=300, output_format="PNG")

# Simple title and subtitle using Streamlit's built-in functions
st.title("Wind Load Calculator")
st.caption("BS EN 1991-1-4 Implementation")

# Version information
st.text(f"Version {APP_VERSION} | Last Updated: {LAST_UPDATED}")

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

# Main app content would go here

# Simple footer
st.markdown(f"""
<div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #f0f2f6; padding: 0.5rem; text-align: center; font-size: 0.8rem; color: #666; border-top: 1px solid #ddd;">
    Wind Load Calculator v{APP_VERSION} | © {datetime.datetime.now().year}
</div>
""", unsafe_allow_html=True)

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

# Custom CSS - simplified
st.markdown("""
<style>
    /* Title block styling */
    .title-block {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem;
        border-bottom: 2px solid #4e8df5;
        margin-bottom: 1.5rem;
    }
    
    .logo-container {
        flex: 0 0 auto;
        margin-right: 1rem;
    }
    
    .title-container {
        flex: 1 1 auto;
    }
    
    .version-container {
        flex: 0 0 auto;
        text-align: right;
        font-size: 0.8rem;
        color: #666;
    }
    
    /* Print-specific CSS */
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

# Title block with logo
st.markdown(f"""
<div class="title-block">
    <div class="logo-container">
        <img src="educational/images/tt_logo.png" alt="Company Logo" height="60">
    </div>
    <div class="title-container">
        <h1>Wind Load Calculator</h1>
        <p>BS EN 1991-1-4 Implementation</p>
    </div>
    <div class="version-container">
        <p>Version {APP_VERSION}</p>
        <p>Last Updated: {LAST_UPDATED}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Main app content would go here
# This is just the title block setup as requested

# Simple footer
st.markdown(f"""
<div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #f0f2f6; padding: 0.5rem; text-align: center; font-size: 0.8rem; color: #666; border-top: 1px solid #ddd;">
    Wind Load Calculator v{APP_VERSION} | © {datetime.datetime.now().year}
</div>
""", unsafe_allow_html=True)

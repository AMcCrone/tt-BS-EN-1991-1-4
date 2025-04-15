import streamlit as st
import datetime

# App version and metadata
APP_VERSION = "1.0.0"
LAST_UPDATED = "April 15, 2025"

# Setup page configuration with a favicon
st.set_page_config(
    page_title="Wind Load Calculator",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.region = None
    st.session_state.current_page = "region_selection"
    st.session_state.inputs = {}
    st.session_state.results = {}
    st.session_state.show_educational = True

# Custom CSS for the entire app
st.markdown("""
<style>
    /* Main app styling */
    .main {
        padding: 1rem 1rem;
    }
    
    /* App header styling */
    .app-header {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #4e8df5;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .header-logo {
        text-align: left;
    }
    
    .header-title {
        text-align: center;
        flex-grow: 1;
    }
    
    .header-version {
        text-align: right;
        font-size: 0.8rem;
        color: #666;
    }
    
    /* Section styling */
    .section-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    
    /* Navigation styling */
    .navigation-section {
        display: flex;
        justify-content: space-between;
        margin: 1rem 0;
    }
    
    /* App footer styling */
    .app-footer {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
        border-top: 1px solid #ddd;
        font-size: 0.8rem;
        color: #666;
        text-align: center;
    }
    
    /* Progress indicator */
    .stProgress > div > div > div > div {
        background-color: #4e8df5;
    }
    
    /* Educational content styling */
    .educational-content {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4e8df5;
        margin: 1rem 0;
    }
    
    /* Results highlight */
    .results-highlight {
        font-weight: bold;
        color: #4e8df5;
    }
    
    /* Print-specific styling */
    @media print {
        /* Hide UI elements in print mode */
        .stApp header, .stApp footer, .stSidebar, .stButton, 
        .educational-content, .navigation-section, .app-header .header-version {
            display: none !important;
        }
        
        /* Format printable content */
        .print-friendly {
            page-break-inside: avoid;
            margin: 20px 0;
        }
        
        /* Ensure header prints but simplified */
        .app-header {
            border: none;
            padding: 0;
            margin-bottom: 2rem;
            background: none;
        }
        
        /* Show company info in print */
        .print-company-info {
            display: block !important;
            margin-top: 1rem;
        }
        
        /* Section container without shadows */
        .section-container {
            box-shadow: none;
            border: 1px solid #ddd;
        }
    }
    
    /* Hide print company info normally */
    .print-company-info {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# App Header with Logo, Title and Version
st.markdown(f"""
<div class="app-header">
    <div class="header-logo">
        <span style="font-size: 2rem;">🌪️</span>
    </div>
    <div class="header-title">
        <h1>Wind Load Calculator</h1>
        <p>Professional engineering calculations for structural design</p>
    </div>
    <div class="header-version">
        <p>Version {APP_VERSION}</p>
        <p>Last Updated: {LAST_UPDATED}</p>
    </div>
</div>
<div class="print-company-info">
    <p>Your Company Name</p>
    <p>Report Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
</div>
""", unsafe_allow_html=True)

# Display progress indicator for multi-page workflow
def display_progress():
    workflow_steps = ["Region Selection", "Building Parameters", "Site Conditions", "Calculation Results"]
    
    # Determine current step number
    if st.session_state.current_page == "region_selection":
        current_step = 1
    elif st.session_state.current_page == "building_parameters":
        current_step = 2
    elif st.session_state.current_page == "site_conditions":
        current_step = 3
    elif st.session_state.current_page == "results":
        current_step = 4
    else:
        current_step = 1
    
    # Display progress bar
    progress_percent = current_step / len(workflow_steps)
    st.progress(progress_percent)
    
    # Display step names
    cols = st.columns(len(workflow_steps))
    for i, (col, step) in enumerate(zip(cols, workflow_steps)):
        if i + 1 < current_step:
            col.markdown(f"✅ {step}")
        elif i + 1 == current_step:
            col.markdown(f"**→ {step}**")
        else:
            col.markdown(f"{step}")

# Main app content container
def main():
    display_progress()
    
    # Example section - replace with your actual app logic
    with st.container():
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        
        # Content based on current page
        if st.session_state.current_page == "region_selection":
            st.header("Select Region")
            # Your region selection code here
            
        elif st.session_state.current_page == "building_parameters":
            st.header("Building Parameters")
            # Your building parameters input code here
            
        elif st.session_state.current_page == "site_conditions":
            st.header("Site Conditions")
            # Your site conditions input code here
            
        elif st.session_state.current_page == "results":
            st.header("Calculation Results")
            # Your results display code here
            
            # Example of print-friendly section
            st.markdown('<div class="print-friendly">', unsafe_allow_html=True)
            st.subheader("Summary Report")
            # Your summary report content here
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Educational toggle section
    with st.container():
        show_educational = st.checkbox("Show explanatory information", 
                                       value=st.session_state.show_educational)
        
        if show_educational:
            st.markdown('<div class="educational-content">', unsafe_allow_html=True)
            st.subheader("Understanding Wind Load Calculations")
            st.write("""
            Wind loads are an important consideration in structural design. They represent the force 
            that wind exerts on a structure and are influenced by factors such as:
            
            - Geographic location and wind speed data
            - Building height, shape, and dimensions
            - Surrounding terrain and exposure conditions
            - Building usage and importance
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.session_state.show_educational = show_educational
    
    # Navigation buttons
    st.markdown('<div class="navigation-section">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # Back button if not on first page
    if st.session_state.current_page != "region_selection":
        with col1:
            if st.button("← Back"):
                # Your navigation logic here
                pass
    
    # Next button if not on last page
    if st.session_state.current_page != "results":
        with col3:
            if st.button("Next →"):
                # Your navigation logic here
                pass
    
    # Generate report on results page
    if st.session_state.current_page == "results":
        with col3:
            if st.button("📑 Generate Report"):
                st.info("Preparing PDF report...")
                # Your report generation logic here
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div class="app-footer">
        <p>Wind Load Calculator v{APP_VERSION} | Developed with Streamlit</p>
        <p>© {datetime.datetime.now().year} Your Company Name. All rights reserved.</p>
        <p>For engineering use only. Results should be verified by a licensed professional engineer.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # Add a sidebar for additional options
    with st.sidebar:
        st.image("https://via.placeholder.com/150x100?text=Your+Logo", width=150)
        st.title("Options")
        
        units = st.radio("Units System", ["Imperial (US)", "Metric (SI)"])
        
        st.subheader("About")
        st.write("""
        This application calculates wind loads on structures 
        according to relevant building codes and standards.
        """)
        
        st.subheader("Resources")
        st.markdown("- [User Guide](#)")
        st.markdown("- [Technical Support](#)")
        st.markdown("- [Code References](#)")
        
        st.caption(f"Wind Load Calculator v{APP_VERSION}")
    
    # Main app execution
    main()

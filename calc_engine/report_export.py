"""
Report Export Module for LaTeX Report Generation
Exports essential calculation results (inputs + key outputs) to JSON for LaTeX reports.
Focuses on core variables that are always needed in the report.
"""

import json
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Any, Dict, Optional


class ReportExporter:
    """
    Handles export of essential wind load calculation results for report generation.
    Only exports the core variables needed for the LaTeX report.
    """
    
    def __init__(self, output_folder: str = "streamlit_output"):
        """
        Initialize the report exporter.
        
        Args:
            output_folder: Folder where JSON files will be saved
        """
        self.output_folder = output_folder
        
    def serialize_dataframe(self, df: pd.DataFrame) -> Dict:
        """
        Convert DataFrame to JSON-serializable format.
        """
        if df is None or df.empty:
            return None
            
        return {
            "type": "dataframe",
            "data": df.to_dict(orient='records'),
            "columns": list(df.columns)
        }
    
    def extract_essential_inputs(self) -> Dict:
        """
        Extract only the essential input variables needed for LaTeX report.
        These match the core variables that should always be in the report.
        """
        inputs = {}
        
        # Get the inputs dictionary
        session_inputs = st.session_state.inputs if hasattr(st.session_state, 'inputs') else {}
        
        # Core project information
        inputs["project_name"] = session_inputs.get("project_name", "N/A")
        inputs["project_number"] = session_inputs.get("project_number", "N/A")
        inputs["location"] = session_inputs.get("location", "N/A")
        inputs["region"] = session_inputs.get("region", "N/A")
        
        # Building geometry
        inputs["NS_dimension"] = session_inputs.get("NS_dimension", 0.0)
        inputs["EW_dimension"] = session_inputs.get("EW_dimension", 0.0)
        inputs["z"] = session_inputs.get("z", 0.0)  # Building height
        
        # Site parameters
        inputs["altitude_factor"] = session_inputs.get("altitude_factor", 0.0)
        inputs["d_sea"] = session_inputs.get("d_sea", 0.0)
        inputs["terrain_category"] = session_inputs.get("terrain_category", "N/A")
        
        # Wind parameters
        inputs["V_bmap"] = session_inputs.get("V_bmap", 0.0)  # Basic wind speed
        inputs["V_b"] = session_inputs.get("V_b", 0.0)  # Adjusted basic wind speed
        
        return inputs
    
    def extract_essential_results(self) -> Dict:
        """
        Extract only the essential calculated results needed for LaTeX report.
        """
        results = {}
        
        # Get session inputs for calculated values
        session_inputs = st.session_state.inputs if hasattr(st.session_state, 'inputs') else {}
        
        # Displacement height and adjusted height
        results["h_dis"] = session_inputs.get("h_dis", 0.0)
        results["z_minus_h_dis"] = session_inputs.get("z_minus_h_dis", 0.0)
        
        # Wind velocities and pressures
        results["v_mean"] = session_inputs.get("v_mean", 0.0)  # Mean wind velocity
        results["q_b"] = session_inputs.get("q_b", 0.0)  # Basic wind pressure
        results["q_p"] = session_inputs.get("q_p", 0.0)  # Peak wind pressure
        
        # External pressure coefficient table (cp_results)
        # Check multiple possible locations
        cp_results = None
        if hasattr(st.session_state, 'cp_results') and st.session_state.cp_results is not None:
            cp_results = st.session_state.cp_results
        elif 'cp_results' in session_inputs:
            cp_results = session_inputs['cp_results']
        
        if cp_results is not None:
            results["cp_results"] = self.serialize_dataframe(cp_results)
        
        # Pressure summary table (summary_df)
        # Check all possible locations where this might be stored
        summary_df = None
        if hasattr(st.session_state, 'summary_df') and st.session_state.summary_df is not None:
            summary_df = st.session_state.summary_df
        elif 'summary_df' in session_inputs and session_inputs['summary_df'] is not None:
            summary_df = session_inputs['summary_df']
        elif 'pressure_summary' in session_inputs:
            summary_df = session_inputs['pressure_summary']
        
        if summary_df is not None:
            results["pressure_summary"] = self.serialize_dataframe(summary_df)
        
        return results
    
    def create_export_data(self) -> Dict:
        """
        Create complete export data structure with only essential variables.
        """
        return {
            "inputs": self.extract_essential_inputs(),
            "results": self.extract_essential_results(),
            "_metadata": {
                "exported_at": datetime.now().isoformat(),
                "app_version": "1.0",
                "calculator_type": "wind_load_bs_en_1991",
                "export_type": "essential_report_data"
            }
        }
    
    def save_to_file(self, filename: Optional[str] = None) -> str:
        """
        Save export data to JSON file in the output folder.
        
        Args:
            filename: Optional custom filename. If None, auto-generates from project name.
            
        Returns:
            str: Path to saved file
        """
        # Create output folder if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            project_name = st.session_state.inputs.get("project_name", "Untitled")
            timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M")
            # Clean project name for filename
            safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in project_name)
            filename = f"{safe_name}_Wind Load Analysis_{timestamp}.json"
        
        # Create full path
        filepath = os.path.join(self.output_folder, filename)
        
        # Get export data
        export_data = self.create_export_data()
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def get_export_preview(self) -> Dict:
        """
        Get a preview of what will be exported.
        """
        data = self.create_export_data()
        
        # Count available results
        cp_rows = 0
        pressure_rows = 0
        
        if data["results"].get("cp_results"):
            cp_rows = len(data["results"]["cp_results"]["data"])
        
        if data["results"].get("pressure_summary"):
            pressure_rows = len(data["results"]["pressure_summary"]["data"])
        
        preview = {
            "Input Variables": len([v for v in data["inputs"].values() if v not in ["N/A", 0.0]]),
            "Calculated Results": {
                "CP Results Rows": cp_rows,
                "Pressure Summary Rows": pressure_rows,
                "Has h_dis": data["results"].get("h_dis", 0.0) > 0,
                "Has Peak Pressure": data["results"].get("q_p", 0.0) > 0
            },
            "Metadata": data["_metadata"]
        }
        
        return preview


def add_sidebar_report_export_ui():
    """
    Add report export UI to Streamlit sidebar with download functionality.
    This should be called in main.py AFTER calculations are complete and
    st.session_state.summary_df has been set.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Export for Report")
    
    # Show info about what will be exported
    with st.sidebar.expander("ℹ️ What gets exported?", expanded=False):
        st.markdown("""
        **Essential Inputs:**
        - Project name, number, location
        - Building dimensions (NS, EW, height)
        - Altitude, distance to sea
        - Terrain category
        - Basic wind speed
        
        **Essential Results:**
        - h_dis, z-h_dis
        - Mean wind velocity
        - Basic & peak wind pressure
        - CP coefficient table
        - **Pressure summary table**
        """)
    
    # Validate that we have results to export
    missing_items = []
    if not hasattr(st.session_state, 'cp_results') or st.session_state.cp_results is None:
        missing_items.append("CP results")
    if not hasattr(st.session_state, 'summary_df') or st.session_state.summary_df is None:
        missing_items.append("Pressure summary")
    
    if missing_items:
        st.sidebar.warning(f"⚠️ Missing: {', '.join(missing_items)}. Complete calculations first.")
        return
    
    # Custom filename option
    use_custom_filename = st.sidebar.checkbox(
        "Custom filename",
        value=False,
        help="Check to specify a custom filename"
    )
    
    custom_filename = None
    if use_custom_filename:
        custom_filename = st.sidebar.text_input(
            "Filename",
            value="",
            placeholder="my_report.json"
        )
        if custom_filename and not custom_filename.endswith('.json'):
            custom_filename += '.json'
    
    # Generate export data
    try:
        exporter = ReportExporter()
        export_data = exporter.create_export_data()
        
        # Convert to JSON string
        json_string = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Generate filename for download
        if custom_filename:
            download_filename = custom_filename
        else:
            project_name = st.session_state.inputs.get("project_name", "Untitled")
            timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M")
            safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in project_name)
            download_filename = f"{safe_name}_Wind Load Analysis_{timestamp}.json"
        
        # Create two columns for the buttons
        col1, col2 = st.sidebar.columns([1, 1])
        
        with col1:
            st.download_button(
                label="⬇️ Download",
                data=json_string,
                file_name=download_filename,
                mime="application/json",
                help="Download JSON file to your browser's download folder",
                use_container_width=True
            )
        
        with col2:
            if st.button("💾 Save Local", help="Save to streamlit_output/ folder", use_container_width=True):
                try:
                    output_folder = "streamlit_output"
                    os.makedirs(output_folder, exist_ok=True)
                    
                    filepath = os.path.join(output_folder, download_filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(json_string)
                    
                    file_size = os.path.getsize(filepath)
                    file_size_kb = file_size / 1024
                    
                    st.sidebar.success(f"✅ Saved to `{filepath}`")
                    st.sidebar.info(f"📦 Size: {file_size_kb:.1f} KB")
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Save failed: {str(e)}")
        
        # Show preview with pressure_summary status
        preview = exporter.get_export_preview()
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Export includes:**")
        st.sidebar.markdown(f"- {preview['Input Variables']} essential inputs")
        st.sidebar.markdown(f"- {preview['Calculated Results']['CP Results Rows']} CP coefficients")
        
        # Highlight pressure summary status
        pressure_rows = preview['Calculated Results']['Pressure Summary Rows']
        if pressure_rows > 0:
            st.sidebar.markdown(f"- ✅ {pressure_rows} pressure summary rows")
        else:
            st.sidebar.markdown(f"- ⚠️ No pressure summary data")
            
    except Exception as e:
        st.sidebar.error(f"❌ Export preparation failed: {str(e)}")
        st.sidebar.exception(e)


def show_export_statistics():
    """
    Display statistics about available export data (for debugging).
    """
    st.subheader("Export Data Preview")
    
    exporter = ReportExporter()
    preview = exporter.get_export_preview()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Input Variables", preview["Input Variables"])
        st.metric("CP Results", preview["Calculated Results"]["CP Results Rows"])
    
    with col2:
        st.metric("Pressure Results", preview["Calculated Results"]["Pressure Summary Rows"])
        st.write(f"**Has Peak Pressure:** {preview['Calculated Results']['Has Peak Pressure']}")
    
    # Show full preview
    if st.checkbox("Show detailed preview"):
        data = exporter.create_export_data()
        st.json(data)

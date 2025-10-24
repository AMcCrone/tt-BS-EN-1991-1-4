"""
Report Export Module for LaTeX Report Generation
Exports complete calculation results (inputs + outputs) to JSON for use with LaTeX helper script.
This is separate from JSON_save_load.py which is for session state persistence.
"""

import json
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Any, Dict, Optional
import plotly.graph_objects as go


class ReportExporter:
    """
    Handles export of complete wind load calculation results for report generation.
    Includes both inputs and calculated results (DataFrames, figures, etc.)
    """
    
    def __init__(self, output_folder: str = "streamlit_output"):
        """
        Initialize the report exporter.
        
        Args:
            output_folder: Folder where JSON files will be saved (same level as main.py)
        """
        self.output_folder = output_folder
        
    def serialize_dataframe(self, df: pd.DataFrame) -> Dict:
        """
        Convert DataFrame to JSON-serializable format with type information.
        """
        if df is None or df.empty:
            return None
            
        return {
            "type": "dataframe",
            "data": df.to_dict(orient='records'),
            "columns": list(df.columns),
            "index": list(df.index) if not isinstance(df.index, pd.RangeIndex) else None
        }
    
    def serialize_plotly_figure(self, fig: go.Figure) -> Dict:
        """
        Convert Plotly figure to JSON-serializable format.
        """
        if fig is None:
            return None
            
        return {
            "type": "plotly_figure",
            "data": fig.to_dict()
        }
    
    def extract_inputs(self) -> Dict:
        """
        Extract all input variables from session state.
        These are the user-entered values.
        """
        inputs = {}
        
        # Get the inputs dictionary if it exists
        if hasattr(st.session_state, 'inputs'):
            inputs = st.session_state.inputs.copy()
        
        return inputs
    
    def extract_results(self) -> Dict:
        """
        Extract all calculated results from session state.
        These are the outputs of the calculations.
        """
        results = {}
        
        # 1. Pressure Summary DataFrame (summary_df)
        if hasattr(st.session_state, 'summary_df') and st.session_state.summary_df is not None:
            results["pressure_summary"] = self.serialize_dataframe(st.session_state.summary_df)
        
        # 2. External Pressure Coefficients (cp_results) - combined all directions
        if hasattr(st.session_state, 'cp_results') and st.session_state.cp_results is not None:
            results["cp_results"] = self.serialize_dataframe(st.session_state.cp_results)
        
        # 3. External Pressure Coefficients per elevation (cp_results_by_elevation)
        if hasattr(st.session_state, 'cp_results_by_elevation'):
            results["cp_results_by_elevation"] = {}
            for direction, df in st.session_state.cp_results_by_elevation.items():
                results["cp_results_by_elevation"][direction] = self.serialize_dataframe(df)
        
        # 4. Inset zone results
        if hasattr(st.session_state, 'inset_results') and st.session_state.inset_results is not None:
            results["inset_results"] = st.session_state.inset_results
        
        # 5. Inset figure (3D visualization)
        if hasattr(st.session_state, 'inset_fig') and st.session_state.inset_fig is not None:
            results["inset_fig"] = self.serialize_plotly_figure(st.session_state.inset_fig)
        
        # 6. Direction factors (if applicable)
        if st.session_state.inputs.get("use_direction_factor", False):
            from calc_engine.common.pressure_summary import get_direction_factor
            rotation = st.session_state.inputs.get("building_rotation", 0)
            direction_factors = get_direction_factor(rotation, True)
            results["direction_factors"] = direction_factors
        
        # 7. Key calculated intermediate values
        results["calculated_values"] = {
            "q_b": st.session_state.inputs.get("q_b"),
            "v_mean": st.session_state.inputs.get("v_mean"),
            "c_rz": st.session_state.inputs.get("c_rz"),
            "c_oz": st.session_state.inputs.get("c_oz"),
            "c_rT": st.session_state.inputs.get("c_rT"),
        }
        
        return results
    
    def extract_app_state(self) -> Dict:
        """
        Extract application state (settings, toggles, etc.)
        """
        return {
            "region": st.session_state.inputs.get("region"),
            "inset_enabled": st.session_state.inputs.get("inset_enabled", False),
            "consider_funnelling": st.session_state.inputs.get("consider_funnelling", False),
            "use_direction_factor": st.session_state.inputs.get("use_direction_factor", False),
            "building_rotation": st.session_state.inputs.get("building_rotation", 0),
            "use_custom_values": st.session_state.inputs.get("use_custom_values", False),
            "use_map": st.session_state.inputs.get("use_map", False),
            "orography_significant": st.session_state.inputs.get("orography_significant", False),
            "terrain_category": st.session_state.inputs.get("terrain_category", ""),
            "show_educational": st.session_state.get("show_educational", False)
        }
    
    def create_export_data(self) -> Dict:
        """
        Create complete export data structure.
        """
        return {
            "inputs": self.extract_inputs(),
            "session_state": {
                "show_educational": st.session_state.get("show_educational", False),
                "markers": st.session_state.get("markers", []),
                "inset_results": st.session_state.get("inset_results"),
                "inset_fig": self.serialize_plotly_figure(st.session_state.get("inset_fig")),
                "inset_fig_type": "dataframe",  # metadata
                "cp_results": self.serialize_dataframe(st.session_state.get("cp_results")),
                "cp_results_type": "dataframe"  # metadata
            },
            "app_state": self.extract_app_state(),
            "_metadata": {
                "saved_at": datetime.now().isoformat(),
                "app_version": "1.0",
                "calculator_type": "wind_load_bs_en_1991",
                "total_variables": len(self.extract_inputs())
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
        Get a preview of what will be exported (for debugging/display).
        """
        data = self.create_export_data()
        
        preview = {
            "Input Variables": len(data["inputs"]),
            "Calculated Results": {
                "Pressure Summary Rows": len(data["session_state"]["cp_results"]["data"]) if data["session_state"]["cp_results"] else 0,
                "CP Results Rows": len(data["session_state"]["cp_results"]["data"]) if data["session_state"]["cp_results"] else 0,
                "Inset Results": "Yes" if data["session_state"]["inset_results"] else "No",
                "Direction Factors": "Yes" if "direction_factors" in data.get("results", {}) else "No"
            },
            "Metadata": data["_metadata"]
        }
        
        return preview


def add_sidebar_report_export_ui():
    """
    Add report export UI to Streamlit sidebar.
    This should be called in main.py after calculations are complete.
    """
    st.sidebar.markdown("---")  # Separator from save/load section
    st.sidebar.subheader("📊 Export for Report")
    
    # Show info about what will be exported
    with st.sidebar.expander("ℹ️ What gets exported?", expanded=False):
        st.markdown("""
        **Inputs:**
        - Project details
        - Building geometry
        - Wind parameters
        - All calculation inputs
        
        **Results:**
        - Pressure summary table
        - CP coefficients per elevation
        - Inset zone results
        - Direction factors (if used)
        - All calculated values
        """)
    
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
    
    # Export button
    if st.sidebar.button("📄 Export Report Data", help="Export inputs and results for LaTeX report"):
        try:
            exporter = ReportExporter()
            
            # Validate that we have results to export
            if not hasattr(st.session_state, 'cp_results') or st.session_state.cp_results is None:
                st.sidebar.warning("⚠️ No calculation results found. Please complete the calculations first.")
                return
            
            # Save to file
            filepath = exporter.save_to_file(custom_filename)
            
            # Get file info
            file_size = os.path.getsize(filepath)
            file_size_kb = file_size / 1024
            
            # Success message
            st.sidebar.success(f"✅ Exported successfully!")
            st.sidebar.info(f"📁 **File:** `{os.path.basename(filepath)}`\n\n📦 **Size:** {file_size_kb:.1f} KB")
            
            # Show preview of what was exported
            preview = exporter.get_export_preview()
            st.sidebar.markdown("**Exported:**")
            st.sidebar.markdown(f"- {preview['Input Variables']} input variables")
            st.sidebar.markdown(f"- {preview['Calculated Results']['Pressure Summary Rows']} pressure results")
            
        except Exception as e:
            st.sidebar.error(f"❌ Export failed: {str(e)}")
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
        st.write(f"**Inset Results:** {preview['Calculated Results']['Inset Results']}")
    
    # Show full preview
    if st.checkbox("Show detailed preview"):
        data = exporter.create_export_data()
        st.json(data)

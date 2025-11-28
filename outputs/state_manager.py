"""
Unified State Management for Wind Load Calculator
Handles session save/load and PDF data export with automatic variable detection.
"""

import json
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


class StateManager:
    """
    Centralized state management for the wind load calculator.
    Automatically detects and handles all variables in session state.
    """
    
    # Define which top-level session state keys to exclude from save/load
    EXCLUDED_KEYS = [
        'initialized',
        'show_educational',
        'results',  # Never save results - recalculate on load
        # Streamlit internals
        'FormSubmitter',
        'file_uploader',
        '_last_form_id',
        '_submit_button_key',
        'file_uploader_key',
        '_widgets',
        '_widget_ids',
        '_script_run_ctx',
        '_session_state',
        'session_state',
        # DataFrames stored at top level (handled separately)
        'cp_results',
        'summary_df',
        'inset_results'
    ]
    
    def __init__(self):
        """Initialize the state manager."""
        pass
    
    # ========================================================================
    # SERIALIZATION HELPERS
    # ========================================================================
    
    def serialize_value(self, value: Any) -> Any:
        """Convert any value to JSON-serializable format."""
        if value is None:
            return None
        elif isinstance(value, (bool, int, float, str)):
            return value
        elif isinstance(value, pd.DataFrame):
            return self.serialize_dataframe(value)
        elif isinstance(value, (list, tuple)):
            return [self.serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}
        elif isinstance(value, datetime):
            return value.isoformat()
        else:
            # For other types, convert to string
            try:
                return str(value)
            except:
                return f"<{type(value).__name__}>"
    
    def serialize_dataframe(self, df: pd.DataFrame) -> Optional[Dict]:
        """Convert DataFrame to JSON-serializable format."""
        if df is None or df.empty:
            return None
        return {
            "_type": "dataframe",
            "data": df.to_dict(orient='records'),
            "columns": list(df.columns)
        }
    
    def deserialize_dataframe(self, data: Dict) -> Optional[pd.DataFrame]:
        """Convert serialized dict back to DataFrame."""
        if data is None or data.get("_type") != "dataframe":
            return None
        return pd.DataFrame(data["data"], columns=data["columns"])
    
    # ========================================================================
    # SESSION SAVE/LOAD (Inputs Only)
    # ========================================================================
    
    def get_session_inputs(self) -> Dict[str, Any]:
        """
        Extract all user inputs from session state.
        This excludes results and other non-input variables.
        """
        if not hasattr(st.session_state, 'inputs'):
            return {}
        
        # Serialize the entire inputs dictionary
        return self.serialize_value(st.session_state.inputs)
    
    def save_session(self, filename: Optional[str] = None) -> str:
        """
        Save user inputs to JSON (for session save/load).
        Results are NOT saved - they will be recalculated on load.
        
        Returns:
            str: JSON string ready for download
        """
        # Generate filename if not provided
        if filename is None:
            project_name = st.session_state.inputs.get("project_name", "Project")
            date_str = datetime.now().strftime('%y%m%d')
            filename = f"{date_str}_{project_name}_Wind Load Session.json"
        
        data = {
            "inputs": self.get_session_inputs(),
            "_metadata": {
                "filename": filename,
                "saved_at": datetime.now().isoformat(),
                "version": "2.0",
                "type": "session_save",
                "description": "User inputs only - results will be recalculated on load"
            }
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def load_session(self, json_content: str) -> bool:
        """
        Load user inputs from JSON and restore to session state.
        Results will be recalculated automatically by the app.
        
        Args:
            json_content: JSON string from uploaded file
            
        Returns:
            bool: True if successful
        """
        try:
            data = json.loads(json_content)
            
            if 'inputs' not in data:
                st.error("Invalid session file: missing 'inputs' key")
                return False
            
            # Restore inputs
            if not hasattr(st.session_state, 'inputs'):
                st.session_state.inputs = {}
            
            st.session_state.inputs.update(data['inputs'])
            
            # Clear results so they get recalculated
            if hasattr(st.session_state, 'results'):
                st.session_state.results = {}
            
            # Clear top-level DataFrames
            for key in ['cp_results', 'summary_df', 'inset_results']:
                if hasattr(st.session_state, key):
                    delattr(st.session_state, key)
            
            # Show success message
            metadata = data.get('_metadata', {})
            st.success(f"✅ Session loaded from {metadata.get('filename', 'file')}")
            
            return True
            
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {str(e)}")
            return False
        except Exception as e:
            st.error(f"Error loading session: {str(e)}")
            return False
    
    # ========================================================================
    # PDF EXPORT (Inputs + Results)
    # ========================================================================
    
    def get_pdf_inputs(self) -> Dict[str, Any]:
        """
        Extract essential inputs needed for PDF generation.
        """
        if not hasattr(st.session_state, 'inputs'):
            return {}
        
        inputs = st.session_state.inputs
        
        # Core project information
        pdf_inputs = {
            "project_name": inputs.get("project_name", "N/A"),
            "project_number": inputs.get("project_number", "N/A"),
            "location": inputs.get("location", "N/A"),
            "region": inputs.get("region", "N/A"),
            
            # Building geometry
            "NS_dimension": inputs.get("NS_dimension", 0.0),
            "EW_dimension": inputs.get("EW_dimension", 0.0),
            "z": inputs.get("z", 0.0),
            
            # Site parameters
            "c_alt": inputs.get("c_alt", 0.0),
            "altitude": inputs.get("altitude", 0.0),
            "d_sea": inputs.get("d_sea", 0.0),
            "d_town_terrain": inputs.get("d_town_terrain", 0.0),
            "terrain_category": inputs.get("terrain_category", "N/A"),
            "terrain_type": inputs.get("terrain_type", "N/A"),
            "rho_air": inputs.get("rho_air", 0.0),
            
            # Wind parameters
            "V_bmap": inputs.get("V_bmap", 0.0),
            "V_b0": inputs.get("V_b0", 0.0),
            
            # UK-specific
            "is_orography_significant": inputs.get("is_orography_significant", False),
            
            # Funnelling
            "consider_funnelling": inputs.get("consider_funnelling", False),
        }
        
        # Conditional inputs
        if pdf_inputs["consider_funnelling"]:
            pdf_inputs.update({
                "north_gap": inputs.get("north_gap", 0.0),
                "south_gap": inputs.get("south_gap", 0.0),
                "east_gap": inputs.get("east_gap", 0.0),
                "west_gap": inputs.get("west_gap", 0.0),
            })
        
        # Inset zone
        pdf_inputs["inset_enabled"] = inputs.get("inset_enabled", False)
        if pdf_inputs["inset_enabled"]:
            pdf_inputs.update({
                "inset_height": inputs.get("inset_height", 0.0),
                "north_offset": inputs.get("north_offset", 0.0),
                "south_offset": inputs.get("south_offset", 0.0),
                "east_offset": inputs.get("east_offset", 0.0),
                "west_offset": inputs.get("west_offset", 0.0),
            })
            if hasattr(st.session_state, 'inset_results'):
                pdf_inputs["inset_results"] = st.session_state.inset_results
        
        return pdf_inputs
    
    def get_pdf_results(self) -> Dict[str, Any]:
        """
        Extract essential results needed for PDF generation.
        Checks both st.session_state.results and st.session_state.inputs
        for backwards compatibility.
        """
        results = st.session_state.results
        
        results_dict = {}
        
        # Get from results namespace (preferred)
        if hasattr(st.session_state, 'results'):
            results_dict = st.session_state.results
        
        # Fallback to inputs namespace for backwards compatibility
        if hasattr(st.session_state, 'inputs'):
            inputs_dict = st.session_state.inputs
        else:
            inputs_dict = {}
        
        # Helper function to get value from either location
        def get_result(key, default=0.0):
            return results_dict.get(key, inputs_dict.get(key, default))
        
        pdf_results = {
            # Displacement height
            "h_dis": get_result("h_dis"),
            "z_minus_h_dis": get_result("z_minus_h_dis"),
            
            # Wind velocities and pressures
            "V_b": get_result("V_b"),
            "v_mean": get_result("v_mean"),
            "q_b": get_result("q_b"),
            "q_p": get_result("q_p"),
            
            # UK-specific factors
            "c_ez": get_result("c_ez"),
            "c_eT": get_result("c_eT"),
            "i_vz": get_result("i_vz"),
            "k_iT": get_result("k_iT"),
            "c_rz": get_result("c_rz"),
            "c_rT": get_result("c_rT"),
            "c_o": get_result("c_o", 1.0),

            # EU-specific factors
            "z_0": get_result("z_0"),
            "z_min": get_result("z_min"),
            "k_r": get_result("k_r"),

            # Add summary paragraphs
            "summary_paragraphs": get_result("summary_paragraphs", []),
        }
        
        # DataFrames - check multiple locations
        # CP results
        cp_results = None
        if hasattr(st.session_state, 'cp_results'):
            cp_results = st.session_state.cp_results
        elif 'cp_results' in results_dict:
            cp_results = results_dict['cp_results']
        elif 'cp_results' in inputs_dict:
            cp_results = inputs_dict['cp_results']
        
        if cp_results is not None:
            pdf_results["cp_results"] = self.serialize_dataframe(cp_results)
        
        # Pressure summary
        summary_df = None
        if hasattr(st.session_state, 'summary_df'):
            summary_df = st.session_state.summary_df
        elif 'summary_df' in results_dict:
            summary_df = results_dict['summary_df']
        elif 'summary_df' in inputs_dict:
            summary_df = inputs_dict['summary_df']
        elif 'pressure_summary' in results_dict:
            summary_df = results_dict['pressure_summary']
        elif 'pressure_summary' in inputs_dict:
            summary_df = inputs_dict['pressure_summary']
        
        if summary_df is not None:
            pdf_results["pressure_summary"] = self.serialize_dataframe(summary_df)
        
        return pdf_results
    
    def export_for_pdf(self, filename: Optional[str] = None) -> str:
        """
        Export inputs and results for PDF generation.
        
        Returns:
            str: JSON string ready for download
        """
        # Generate filename if not provided
        if filename is None:
            project_name = st.session_state.inputs.get("project_name", "Untitled")
            timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M")
            safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' 
                               for c in project_name)
            filename = f"{safe_name}_Wind Load Results_{timestamp}.json"
        
        data = {
            "inputs": self.get_pdf_inputs(),
            "results": self.get_pdf_results(),
            "_metadata": {
                "filename": filename,
                "exported_at": datetime.now().isoformat(),
                "version": "2.0",
                "type": "pdf_export",
                "description": "Complete inputs and results for PDF generation"
            }
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)


# ============================================================================
# UI FUNCTIONS FOR SIDEBAR
# ============================================================================

def add_session_save_ui():
    """Add session save UI to sidebar."""
    st.sidebar.header("💾 Save Session")
    
    manager = StateManager()
    
    # Generate filename
    project_name = st.session_state.inputs.get("project_name", "Project")
    date_str = datetime.now().strftime('%y%m%d')
    filename = f"{date_str}_{project_name}_Wind Load Session.json"
    
    # Generate JSON
    json_content = manager.save_session(filename)
    
    # Download button
    st.sidebar.download_button(
        label="📥 Download Session",
        data=json_content,
        file_name=filename,
        mime="application/json",
        help="Download session file (inputs only)",
        use_container_width=True
    )


def add_session_load_ui():
    """Add session load UI to sidebar."""
    st.sidebar.subheader("📂 Load Session")
    
    uploaded_file = st.sidebar.file_uploader(
        "Choose session file",
        type=['json'],
        help="Upload a previously saved session file",
        key="session_uploader"
    )
    
    if uploaded_file is not None:
        if st.sidebar.button("Load Session", use_container_width=True):
            json_content = uploaded_file.read().decode('utf-8')
            manager = StateManager()
            
            if manager.load_session(json_content):
                st.rerun()


def add_pdf_export_ui():
    """Add PDF data export UI to sidebar."""
    st.sidebar.subheader("📊 Export Data (JSON)")
    
    manager = StateManager()
    
    # Generate filename
    project_name = st.session_state.inputs.get("project_name", "Untitled") if hasattr(st.session_state, 'inputs') else "Untitled"
    timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M")
    safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' 
                       for c in project_name)
    filename = f"{safe_name}_Wind Load Results_{timestamp}.json"
    
    # Generate JSON
    try:
        json_content = manager.export_for_pdf(filename)
        
        st.sidebar.download_button(
            label="⬇️ Download JSON",
            data=json_content,
            file_name=filename,
            mime="application/json",
            help="Download complete results as JSON",
            use_container_width=True
        )
    except Exception as e:
        st.sidebar.error(f"❌ Export failed: {str(e)}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def save_session_to_json() -> str:
    """Convenience function to get session JSON string."""
    manager = StateManager()
    return manager.save_session()


def load_session_from_json(json_content: str) -> bool:
    """Convenience function to load session from JSON string."""
    manager = StateManager()
    return manager.load_session(json_content)


def export_pdf_data() -> str:
    """Convenience function to get PDF export JSON string."""
    manager = StateManager()
    return manager.export_for_pdf()

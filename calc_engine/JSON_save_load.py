import json
import streamlit as st
from datetime import datetime
from typing import Any, Dict, List

class AutomaticJSONHandler:
    """
    Simple JSON save/load handler for Streamlit session state.
    """
    
    def __init__(self, excluded_keys: List[str] = None):
        self.excluded_keys = excluded_keys or []
        # Common Streamlit keys to exclude
        self.excluded_keys.extend([
            'FormSubmitter',
            'file_uploader',
            '_last_form_id',
            '_submit_button_key',
            'file_uploader_key'
        ])
    
    def get_all_session_variables(self) -> Dict[str, Any]:
        """Get all session variables, excluding internal ones."""
        variables = {}
        for key, value in st.session_state.items():
            if key in self.excluded_keys or key.startswith('_'):
                continue
            try:
                # Simple JSON serialization test
                json.dumps(value)
                variables[key] = value
            except:
                # Convert non-serializable to string
                variables[key] = str(value)
        return variables
    
    def create_json_string(self) -> str:
        """Create JSON string from session variables."""
        try:
            data = {
                'variables': self.get_all_session_variables(),
                'timestamp': datetime.now().isoformat(),
                'total_variables': len(self.get_all_session_variables())
            }
            return json.dumps(data, indent=2)
        except Exception as e:
            st.error(f"Error creating JSON: {str(e)}")
            return ""
    
    def load_from_json_string(self, json_content: str) -> bool:
        """Load variables from JSON string into session state."""
        try:
            data = json.loads(json_content)
            if 'variables' not in data:
                st.error("Invalid JSON: missing 'variables'")
                return False
            
            # Load all variables
            for key, value in data['variables'].items():
                st.session_state[key] = value
            
            st.success(f"Loaded {len(data['variables'])} variables")
            return True
            
        except Exception as e:
            st.error(f"Error loading JSON: {str(e)}")
            return False

def generate_filename():
    """Generate filename: ProjectName_Wind Load Analysis_DD.MM.YYYY_HH.MM.json"""
    timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M")
    project_name = st.session_state.get("project_name", "")
    
    if project_name:
        return f"{project_name}_Wind Load Analysis_{timestamp}.json"
    else:
        return f"Wind Load Analysis_{timestamp}.json"

def JSON_generator(filename: str):
    """Generate downloadable JSON file."""
    handler = AutomaticJSONHandler()
    json_content = handler.create_json_string()
    
    if json_content:
        st.sidebar.download_button(
            label="⬇️ Download JSON",
            data=json_content,
            file_name=filename,
            mime="application/json"
        )

def JSON_loader(uploaded_file):
    """Load uploaded JSON file."""
    if uploaded_file is not None:
        try:
            json_content = uploaded_file.read().decode('utf-8')
            handler = AutomaticJSONHandler()
            if handler.load_from_json_string(json_content):
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

def add_sidebar_save_ui():
    """Simple save UI in sidebar."""
    st.sidebar.subheader("💾 Save Session")
    
    filename = st.sidebar.text_input("Filename:", value=generate_filename())
    
    if st.sidebar.button("Generate Download"):
        JSON_generator(filename)

def add_sidebar_upload_ui():
    """Simple upload UI in sidebar."""
    st.sidebar.subheader("📂 Load Session")
    
    uploaded_file = st.sidebar.file_uploader(
        "Choose JSON file",
        type=['json']
    )
    
    if uploaded_file is not None:
        JSON_loader(uploaded_file)

import json
import streamlit as st
import os
from typing import Any, Dict, List, Union
from datetime import datetime
import zipfile
import io

class AutomaticJSONHandler:
    """
    Automatic JSON save/load handler for Streamlit session state variables.
    This class automatically detects and handles all session state variables
    without requiring manual updates when new variables are added.
    """
    
    def __init__(self, excluded_keys: List[str] = None):
        """
        Initialize the handler with optional excluded keys.
        
        Args:
            excluded_keys: List of session state keys to exclude from save/load
        """
        self.excluded_keys = excluded_keys or []
        # Add common Streamlit internal keys that shouldn't be saved
        self.excluded_keys.extend([
            'FormSubmitter',
            'file_uploader',
            '_last_form_id',
            '_submit_button_key',
            'file_uploader_key',
            # Add more problematic Streamlit internals
            '_widgets',
            '_widget_ids',
            '_script_run_ctx',
            '_session_state',
            'session_state'
        ])
    
    def serialize_value(self, value: Any) -> Any:
        """
        Serialize a value to be JSON-compatible.
        Handles various data types including custom objects.
        """
        if value is None:
            return None
        elif isinstance(value, (bool, int, float, str)):
            return value
        elif isinstance(value, (list, tuple)):
            return [self.serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}
        elif hasattr(value, '__dict__'):
            # Handle custom objects by converting to dict
            return {
                '_type': type(value).__name__,
                '_module': type(value).__module__,
                'data': self.serialize_value(value.__dict__)
            }
        else:
            # For other types, try to convert to string
            try:
                return str(value)
            except:
                return f"<{type(value).__name__} object>"
    
    def get_all_session_variables(self) -> Dict[str, Any]:
        """
        Automatically extract all relevant variables from session state.
        """
        variables = {}
        
        for key, value in st.session_state.items():
            # Skip excluded keys
            if key in self.excluded_keys:
                continue
                
            # Skip keys that start with underscore (usually internal)
            if key.startswith('_'):
                continue
                
            variables[key] = self.serialize_value(value)
        
        return variables
    
    def save_to_json(self, filename: str, include_metadata: bool = True) -> str:
        """
        Save all session state variables to JSON string.
        
        Args:
            filename: Name for the file (used in metadata)
            include_metadata: Whether to include metadata like timestamp
            
        Returns:
            str: JSON string if successful, empty string otherwise
        """
        try:
            data = {
                'variables': self.get_all_session_variables()
            }
            
            if include_metadata:
                data['metadata'] = {
                    'filename': filename,
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0',
                    'total_variables': len(data['variables'])
                }
            
            return json.dumps(data, indent=2, default=str)
            
        except Exception as e:
            st.error(f"Error creating JSON: {str(e)}")
            return ""
    
    def save_to_folder(self, folder_path: str, filename: str, include_metadata: bool = True) -> bool:
        """
        Save session state variables to a JSON file in a specified folder.
        
        Args:
            folder_path: Path to the folder where the file should be saved
            filename: Name of the JSON file
            include_metadata: Whether to include metadata like timestamp
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create folder if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)
            
            full_path = os.path.join(folder_path, filename)
            json_content = self.save_to_json(filename, include_metadata)
            
            if json_content:
                with open(full_path, 'w') as f:
                    f.write(json_content)
                return True
            return False
            
        except Exception as e:
            st.error(f"Error saving to folder: {str(e)}")
            return False
    
    def load_from_json(self, json_content: str) -> bool:
        """
        Load variables from JSON string into session state.
        
        Args:
            json_content: JSON string content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = json.loads(json_content)
            
            if 'variables' not in data:
                st.error("Invalid JSON format: missing 'variables' key")
                return False
            
            variables = data['variables']
            
            # Load variables into session state
            for key, value in variables.items():
                st.session_state[key] = value
            
            # Display success message
            if 'metadata' in data:
                metadata = data['metadata']
                st.success(f"Loaded {metadata.get('total_variables', len(variables))} variables from {metadata.get('filename', 'file')}")
            else:
                st.success(f"Loaded {len(variables)} variables successfully")
            
            # Ensure checkbox states are properly handled
            ensure_checkbox_states()
            return True
            
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {str(e)}")
            return False
        except Exception as e:
            st.error(f"Error loading from JSON: {str(e)}")
            return False

def ensure_checkbox_states():
    """
    Ensure that checkbox states are properly handled after loading.
    Call this function after loading to make sure UI elements reflect loaded state.
    """
    # Handle the inset zone checkbox specifically
    if "inset_enabled" in st.session_state:
        st.session_state["inset_enabled"] = bool(st.session_state["inset_enabled"])
    
    # Add handling for other checkboxes as needed
    checkbox_keys = [key for key in st.session_state.keys() if key.endswith('_enabled') or 'checkbox' in key.lower()]
    for key in checkbox_keys:
        if key in st.session_state:
            st.session_state[key] = bool(st.session_state[key])

def show_variable_summary():
    """
    Display a summary of all variables that would be saved.
    Useful for debugging.
    """
    handler = AutomaticJSONHandler()
    variables = handler.get_all_session_variables()
    
    st.subheader("Session Variables Summary")
    st.write(f"**Total variables to be saved:** {len(variables)}")
    
    # Categorize variables
    boolean_vars = {k: v for k, v in variables.items() if isinstance(v, bool)}
    string_vars = {k: v for k, v in variables.items() if isinstance(v, str)}
    numeric_vars = {k: v for k, v in variables.items() if isinstance(v, (int, float))}
    other_vars = {k: v for k, v in variables.items() if not isinstance(v, (bool, str, int, float))}
    
    col1, col2 = st.columns(2)
    
    with col1:
        if boolean_vars:
            st.write("**Boolean Variables:**")
            for k, v in boolean_vars.items():
                st.write(f"• {k}: {v}")
        
        if numeric_vars:
            st.write("**Numeric Variables:**")
            for k, v in numeric_vars.items():
                st.write(f"• {k}: {v}")
    
    with col2:
        if string_vars:
            st.write("**String Variables:**")
            for k, v in string_vars.items():
                display_v = v[:50] + "..." if len(str(v)) > 50 else v
                st.write(f"• {k}: {display_v}")
        
        if other_vars:
            st.write("**Other Variables:**")
            for k, v in other_vars.items():
                st.write(f"• {k}: {type(v).__name__}")
    
    if st.checkbox("Show full JSON preview"):
        st.json(variables)

# Sidebar UI functions (what you were trying to import)
def add_sidebar_save_ui():
    """
    Add save functionality to sidebar with automatic filename generation.
    """
    st.sidebar.subheader("💾 Save Session")
    
    # Get project name from session state or use default
    project_name = st.session_state.get("project_name", "Project")
    
    # Generate automatic filename: YYMMDD_Project Name_Wind Load Calculation.json
    date_str = datetime.now().strftime('%y%m%d')
    filename = f"{date_str}_{project_name}_Wind Load Calculation.json"
    
    if st.sidebar.button("📥 Download", help="Download JSON file"):
        JSON_generator(filename)

def add_sidebar_upload_ui():
    """
    Add upload functionality to sidebar.
    """
    st.sidebar.subheader("📂 Load Session")
    
    uploaded_file = st.sidebar.file_uploader(
        "Choose JSON file",
        type=['json'],
        help="Upload a previously saved session file"
    )
    
    if uploaded_file is not None:
        if st.sidebar.button("Load Session"):
            JSON_loader(uploaded_file)

def JSON_generator(filename: str = "session_data.json"):
    """
    Generate and download JSON file with session data.
    """
    handler = AutomaticJSONHandler()
    json_content = handler.save_to_json(filename)
    
    if json_content:
        variables = handler.get_all_session_variables()
        
        # Create download button
        st.sidebar.download_button(
            label="⬇️ Download JSON",
            data=json_content,
            file_name=filename,
            mime="application/json",
            help=f"Download session data with {len(variables)} variables"
        )
        
        st.sidebar.success(f"Ready to download {len(variables)} variables!")
    else:
        st.sidebar.error("Failed to generate JSON")

def JSON_loader(uploaded_file):
    """
    Load JSON file and restore session state.
    """
    try:
        # Read the uploaded file
        json_content = uploaded_file.read().decode('utf-8')
        
        # Load into session state
        handler = AutomaticJSONHandler()
        success = handler.load_from_json(json_content)
        
        if success:
            st.sidebar.success("Session loaded successfully!")
            # Force a rerun to update the UI
            st.rerun()
        else:
            st.sidebar.error("Failed to load session")
            
    except Exception as e:
        st.sidebar.error(f"Error loading file: {str(e)}")

# Legacy functions for backward compatibility
def save_wind_load_config(filename: str = "wind_load_config.json") -> bool:
    """
    Save wind load application configuration including all checkboxes and inputs.
    """
    excluded_keys = ['file_uploader_key']
    handler = AutomaticJSONHandler(excluded_keys)
    return handler.save_to_folder("./", filename)

def load_wind_load_config(filename: str = "wind_load_config.json") -> bool:
    """
    Load wind load application configuration.
    """
    try:
        with open(filename, 'r') as f:
            json_content = f.read()
        
        excluded_keys = ['file_uploader_key']
        handler = AutomaticJSONHandler(excluded_keys)
        return handler.load_from_json(json_content)
    except FileNotFoundError:
        st.error(f"File not found: {filename}")
        return False

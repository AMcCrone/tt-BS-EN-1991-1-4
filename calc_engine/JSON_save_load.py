import json
import streamlit as st
from typing import Any, Dict, List, Union
from datetime import datetime

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
            '_submit_button_key'
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
    
    def save_to_json(self, filename: str, include_metadata: bool = True) -> bool:
        """
        Save all session state variables to JSON file.
        
        Args:
            filename: Path to save the JSON file
            include_metadata: Whether to include metadata like timestamp
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = {
                'variables': self.get_all_session_variables()
            }
            
            if include_metadata:
                data['metadata'] = {
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0',
                    'total_variables': len(data['variables'])
                }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            st.error(f"Error saving to JSON: {str(e)}")
            return False
    
    def load_from_json(self, filename: str, merge_with_existing: bool = True) -> bool:
        """
        Load variables from JSON file into session state.
        
        Args:
            filename: Path to the JSON file
            merge_with_existing: If True, merge with existing session state.
                               If False, replace existing session state.
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
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
                st.success(f"Loaded {metadata.get('total_variables', len(variables))} variables")
            else:
                st.success(f"Loaded {len(variables)} variables successfully")
            
            return True
            
        except FileNotFoundError:
            st.error(f"File not found: {filename}")
            return False
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {str(e)}")
            return False
        except Exception as e:
            st.error(f"Error loading from JSON: {str(e)}")
            return False

# Convenience functions for your wind load app
def save_wind_load_config(filename: str = "wind_load_config.json") -> bool:
    """
    Save wind load application configuration including all checkboxes and inputs.
    """
    # Define any keys you want to exclude from saving
    excluded_keys = [
        'file_uploader_key',  # Example of keys to exclude
        # Add other keys you don't want to save
    ]
    
    handler = AutomaticJSONHandler(excluded_keys)
    return handler.save_to_json(filename)

def load_wind_load_config(filename: str = "wind_load_config.json") -> bool:
    """
    Load wind load application configuration.
    """
    excluded_keys = [
        'file_uploader_key',
        # Add other keys you don't want to load
    ]
    
    handler = AutomaticJSONHandler(excluded_keys)
    success = handler.load_from_json(filename)
    
    if success:
        # Ensure checkbox states are properly handled
        ensure_checkbox_states()
    
    return success

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
    
    st.subheader("Variable Summary")
    st.write(f"Total variables: {len(variables)}")
    
    boolean_vars = [k for k, v in variables.items() if isinstance(v, bool)]
    if boolean_vars:
        st.write("**Boolean Variables (Checkboxes):**")
        st.write(", ".join(boolean_vars))
    
    if st.checkbox("Show all variables"):
        st.json(variables)

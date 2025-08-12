import streamlit as st
import json
import datetime
from io import StringIO

def JSON_generator():
    """
    Generate JSON file containing all relevant session state data for the wind load calculator.
    Handles conditional variables based on app forks and user selections.
    """
    # Core project information
    core_inputs = [
        "project_name", "project_number", "location", "region",
        "NS_dimension", "EW_dimension", "z", "altitude_factor", 
        "V_bmap", "V_b"
    ]
    
    # Terrain-related variables
    terrain_inputs = [
        "terrain_category", "d_town_terrain", "d_sea"
    ]
    
    # Map-related variables (conditional on use_map checkbox)
    map_inputs = [
        "markers"  # This stores the interactive map markers
    ]
    
    # Wind velocity and pressure variables
    wind_inputs = [
        "v_mean", "rho_air", "q_b", "loaded_area"
    ]
    
    # Displacement and roughness variables
    displacement_inputs = [
        "h_dis", "z_minus_h_dis", "c_rz", "c_oz", "c_rT", "terrain_type"
    ]
    
    # Inset zone variables (conditional on inset_enabled checkbox)
    inset_inputs = [
        "inset_enabled", "north_offset", "south_offset", 
        "east_offset", "west_offset", "inset_height"
    ]
    
    # Funnelling variables (conditional on consider_funnelling checkbox)
    funnelling_inputs = [
        "consider_funnelling", "north_gap", "south_gap", 
        "east_gap", "west_gap"
    ]
    
    # UK-specific directional factor variables (conditional on region == "United Kingdom")
    uk_directional_inputs = [
        "use_direction_factor", "building_rotation"
    ]
    
    # Custom wind parameters (conditional on use_custom_values checkbox)
    custom_wind_inputs = [
        "use_custom_values", "K", "n", "return_period", "c_prob"
    ]
    
    # UI state variables (checkboxes and toggles)
    ui_state_inputs = [
        "show_educational", "use_map", "add_inset", "use_custom_values"
    ]
    
    # Combine all input categories
    all_input_keys = (core_inputs + terrain_inputs + map_inputs + wind_inputs + 
                     displacement_inputs + inset_inputs + funnelling_inputs + 
                     uk_directional_inputs + custom_wind_inputs + ui_state_inputs)
    
    # Start with the main inputs dictionary
    data_to_save = {}
    
    # Save inputs from st.session_state.inputs
    if hasattr(st.session_state, 'inputs') and st.session_state.inputs:
        data_to_save["inputs"] = {}
        for key in all_input_keys:
            if key in st.session_state.inputs:
                value = st.session_state.inputs[key]
                # Handle serializable data types
                if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                    data_to_save["inputs"][key] = value
                else:
                    data_to_save["inputs"][key] = str(value)
    
    # Save direct session state variables (not in inputs dict)
    direct_session_keys = [
        "show_educational", "markers", "inset_results", "inset_fig",
        "cp_results", "h_dis", "z_minus_h_dis", "c_rz", "c_oz", "c_rT",
        "terrain_type", "v_mean", "rho_air", "q_b"
    ]
    
    data_to_save["session_state"] = {}
    for key in direct_session_keys:
        if key in st.session_state:
            value = st.session_state[key]
            # Handle different data types
            if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                data_to_save["session_state"][key] = value
            elif hasattr(value, 'to_dict'):  # For pandas DataFrames
                try:
                    data_to_save["session_state"][key] = value.to_dict()
                    data_to_save["session_state"][key + "_type"] = "dataframe"
                except:
                    data_to_save["session_state"][key] = str(value)
            else:
                # For complex objects like Plotly figures, store as string
                data_to_save["session_state"][key] = str(value)
    
    # Save app state flags to help with reconstruction
    data_to_save["app_state"] = {
        "region": st.session_state.inputs.get("region", "United Kingdom"),
        "inset_enabled": st.session_state.inputs.get("inset_enabled", False),
        "consider_funnelling": st.session_state.inputs.get("consider_funnelling", False),
        "use_direction_factor": st.session_state.inputs.get("use_direction_factor", False),
        "use_custom_values": st.session_state.inputs.get("use_custom_values", False),
        "use_map": st.session_state.get("use_map", False),
        "terrain_category": st.session_state.inputs.get("terrain_category", ""),
        "show_educational": st.session_state.get("show_educational", False)
    }
    
    # Add metadata
    data_to_save["_metadata"] = {
        "saved_at": datetime.datetime.now().isoformat(),
        "app_version": "1.0",
        "calculator_type": "wind_load_bs_en_1991",
        "total_variables": len([k for section in data_to_save.values() 
                               if isinstance(section, dict) for k in section.keys()])
    }
    
    return data_to_save

def JSON_loader(uploaded_file):
    """
    Load JSON data back into session state, handling the different app forks.
    Returns success status and message.
    """
    try:
        # Read the uploaded file
        if hasattr(uploaded_file, 'getvalue'):
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        else:
            stringio = StringIO(uploaded_file)
        
        data = json.load(stringio)
        
        # Validate the file format
        if "_metadata" not in data:
            return False, "Invalid file format: Missing metadata"
        
        metadata = data.get("_metadata", {})
        
        # Clear existing state to avoid conflicts (optional - comment out if you want to merge)
        # st.session_state.inputs = {}
        
        # Initialize inputs dictionary if it doesn't exist
        if not hasattr(st.session_state, 'inputs'):
            st.session_state.inputs = {}
        
        # Load inputs data
        if "inputs" in data:
            for key, value in data["inputs"].items():
                st.session_state.inputs[key] = value
        
        # Load direct session state variables
        if "session_state" in data:
            for key, value in data["session_state"].items():
                if key.endswith("_type") and value == "dataframe":
                    # Skip type markers
                    continue
                elif key + "_type" in data["session_state"] and data["session_state"][key + "_type"] == "dataframe":
                    # Reconstruct DataFrame
                    try:
                        import pandas as pd
                        st.session_state[key] = pd.DataFrame.from_dict(value)
                    except:
                        st.session_state[key] = value
                else:
                    st.session_state[key] = value
        
        # Load app state flags
        if "app_state" in data:
            app_state = data["app_state"]
            
            # Set key app state variables
            st.session_state.inputs["region"] = app_state.get("region", "United Kingdom")
            st.session_state.inputs["inset_enabled"] = app_state.get("inset_enabled", False)
            st.session_state.inputs["consider_funnelling"] = app_state.get("consider_funnelling", False)
            st.session_state.inputs["use_direction_factor"] = app_state.get("use_direction_factor", False)
            st.session_state.inputs["use_custom_values"] = app_state.get("use_custom_values", False)
            st.session_state.inputs["terrain_category"] = app_state.get("terrain_category", "")
            st.session_state.show_educational = app_state.get("show_educational", False)
        
        # Force rerun to update the UI with loaded values
        # Note: st.rerun() should be called by the main app after this function returns True
        
        saved_time = metadata.get("saved_at", "Unknown time")
        total_vars = metadata.get("total_variables", "Unknown number of")
        
        return True, f"✅ Successfully loaded {total_vars} variables from file saved at {saved_time}"
        
    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON file format: {str(e)}"
    except KeyError as e:
        return False, f"❌ Missing required data in file: {str(e)}"
    except Exception as e:
        return False, f"❌ Error loading file: {str(e)}"

def create_download_filename():
    """Generate a descriptive filename for the JSON download."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Try to get project name for filename
    project_name = ""
    if hasattr(st.session_state, 'inputs') and st.session_state.inputs:
        project_name = st.session_state.inputs.get("project_name", "")
    
    if project_name:
        # Clean project name for filename
        clean_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_name = clean_name.replace(' ', '_')
        return f"WindLoad_{clean_name}_{timestamp}.json"
    else:
        return f"WindLoad_Calculation_{timestamp}.json"

# Example usage functions that you can add to your main.py:

def add_save_load_ui():
    """
    Add save/load UI to your Streamlit app. 
    Call this function where you want the save/load interface to appear.
    """
    st.markdown("---")
    st.header("💾 Save & Load Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Save Current Settings")
        if st.button("📁 Generate Download File", type="primary"):
            try:
                data = JSON_generator()
                json_string = json.dumps(data, indent=2)
                filename = create_download_filename()
                
                st.download_button(
                    label="⬇️ Download Configuration",
                    data=json_string,
                    file_name=filename,
                    mime="application/json",
                    help="Save all your current inputs and calculations"
                )
                
                total_vars = data["_metadata"]["total_variables"]
                st.success(f"✅ Ready to download {total_vars} variables!")
                
            except Exception as e:
                st.error(f"❌ Error generating save file: {str(e)}")
    
    with col2:
        st.subheader("Load Previous Settings")
        uploaded_file = st.file_uploader(
            "Upload Configuration File",
            type=['json'],
            help="Load previously saved wind load calculation settings"
        )
        
        if uploaded_file is not None:
            success, message = JSON_loader(uploaded_file)
            
            if success:
                st.success(message)
                # Force a rerun to update the UI
                st.rerun()
            else:
                st.error(message)

# Validation function to help debug save/load issues
def validate_session_state():
    """
    Debug function to show what's currently in session state.
    Useful for troubleshooting save/load issues.
    """
    st.write("### Session State Debug Info")
    
    if hasattr(st.session_state, 'inputs'):
        st.write("**st.session_state.inputs:**")
        st.json(dict(st.session_state.inputs))
    
    st.write("**Direct session state keys:**")
    direct_keys = [key for key in st.session_state.keys() 
                   if key not in ['inputs'] and not key.startswith('_')]
    st.json({key: str(st.session_state[key])[:100] + "..." 
             if len(str(st.session_state[key])) > 100 
             else st.session_state[key] 
             for key in direct_keys})

import streamlit as st

def get_session_value(st, key, default_value=None):
    """Get a value from session state with a default fallback.
    
    Args:
        st: Streamlit object
        key: The session state key
        default_value: Default value if key doesn't exist
        
    Returns:
        The value from session state or the default
    """
    return st.session_state.inputs.get(key, default_value)

def store_session_value(st, key, value):
    """Store a value in session state.
    
    Args:
        st: Streamlit object
        key: The session state key
        value: The value to store
    """
    st.session_state.inputs[key] = value

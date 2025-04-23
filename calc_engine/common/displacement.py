import streamlit as st

def calculate_displacement_height(st):
    """Calculate displacement height based on user inputs.
    
    Args:
        st: Streamlit object
        
    Returns:
        float: The calculated displacement height
    """
    use_standard = st.checkbox("Use standard $h_{{dis}}$ = 15m", 
                              help="In the absence of more accurate information, the obstruction height may be taken as h_ave = 15m for terrain category IV")
    
    if use_standard:
        h_dis = 15.0
    else:
        col1, col2 = st.columns(2)
        with col1:
            x = st.number_input("Distance to other buildings (m)", value=10.0, min_value=0.0)
        with col2:
            h_ave = st.number_input("Average height h_ave (m)", value=5.0, min_value=0.1)
        
        h = st.session_state.inputs.get("z", 30.0)
        
        if x <= 2 * h_ave:
            h_dis = min(0.8 * h_ave, 0.6 * h)
        elif x < 6 * h_ave:
            h_dis = min(1.2 * h_ave - 0.2 * x, 0.6 * h)
        else:
            h_dis = 0
    
    return h_dis

def display_displacement_results(st, h_dis):
    """Display displacement height calculation results.
    
    Args:
        st: Streamlit object
        h_dis: Calculated displacement height
    """
    # Get height z from session state
    z = st.session_state.inputs.get("z", 30.0)
    z_minus_h_dis = z - h_dis
    
    # Store the calculated value in session state
    st.session_state.inputs["z_minus_h_dis"] = z_minus_h_dis
    
    st.write(f"Displacement height $h_{{dis}}$: {h_dis:.2f} m")
    st.write(f"Effective height ($z - h_{{dis}}$): {z_minus_h_dis:.2f} m")

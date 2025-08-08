import streamlit as st

def calculate_displacement_height(st):
    """
    Calculate displacement height based on user inputs.

    - h_ave defaults to 15 m.
    - Uses h_ave to compute h_dis with the same piecewise rules.
    - Returns only h_dis (as before).
    """
    col1, col2 = st.columns(2)
    with col1:
        x = st.number_input(
            "Distance to other buildings (m)",
            min_value=0.0,
            value=float(st.session_state.inputs.get("x", 10.0)),
            step=1.0,
            format="%.1f"
        )
    with col2:
        h_ave = st.number_input(
            "Average obstruction height h_ave (m)",
            min_value=0.1,
            value=float(st.session_state.inputs.get("h_ave", 15.0)),
            step=0.1,
            format="%.1f"
        )

    # Save inputs for reuse elsewhere
    st.session_state.inputs["x"] = float(x)
    st.session_state.inputs["h_ave"] = float(h_ave)

    # Reference height
    z = float(st.session_state.inputs.get("z", 30.0))

    # Calculate h_dis from h_ave
    if x <= 2.0 * h_ave:
        h_dis = min(0.8 * h_ave, 0.6 * z)
    elif x < 6.0 * h_ave:
        h_dis = min(1.2 * h_ave - 0.2 * x, 0.6 * z)
    else:
        h_dis = 0.0

    return float(h_dis)


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

import streamlit as st

def display_contour_plot_with_override(st, datasets, plot_name, x_value, y_value, description, value_label, store_key=None):
    """Display a contour plot with consistent formatting and override option.
    
    Args:
        st: Streamlit object
        datasets: Loaded contour plot datasets
        plot_name: The name of the plot (e.g., "NA.3")
        x_value: The x-axis value for interpolation
        y_value: The y-axis value for interpolation
        description: Description text for the plot
        value_label: Label for the interpolated value
        store_key: Session state key to store the result (optional)
    
    Returns:
        float: The interpolated or manually entered value
    """
    from calc_engine.uk.contour_plots import get_interpolated_value, display_single_plot
    from calc_engine.common.util import store_session_value
    
    st.markdown(f"##### {plot_name} Plot ({description})")
    
    # Allow user to override the calculated value
    use_calculated = st.checkbox(f"Use calculated value from {plot_name} contour plot", value=True, key=f"use_calc_{plot_name}")
    
    # Display the plot
    display_single_plot(st, datasets, plot_name, x_value, y_value)
    
    # Calculate the interpolated value
    interpolated_value = get_interpolated_value(datasets, plot_name, x_value, y_value)
    
    if use_calculated and interpolated_value is not None:
        final_value = interpolated_value
        st.latex(f"{value_label} = {final_value:.3f}")
    else:
        # Manual override if needed
        final_value = st.number_input(
            f"Enter {description.lower()} value manually",
            min_value=0.70,
            max_value=4.50,
            value=float(st.session_state.inputs.get(store_key, 1.00)) if store_key else 1.00,
            step=0.01,
            format="%.3f",
            key=f"manual_{plot_name}"
        )
        st.latex(f"{value_label} = {final_value:.3f}")
    
    # Store the value if a key is provided
    if store_key:
        store_session_value(st, store_key, final_value)
    
    return final_value

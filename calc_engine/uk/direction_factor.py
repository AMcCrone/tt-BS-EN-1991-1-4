# Add to main.py if wanting to include directional factor
# Wind pressure parameters
st.markdown("---")
st.header("Wind Directional Factor, $c_{dir}$")

# Only show directional factor option for UK region
if st.session_state.inputs.get("region") == "United Kingdom":
    # Directional factor checkbox
    use_direction_factor = st.checkbox(
        "Use UK directional factor (c_dir)", 
        value=st.session_state.inputs.get("use_direction_factor", False),
        help="Apply UK directional factor based on wind direction"
    )
    st.session_state.inputs["use_direction_factor"] = use_direction_factor
    # Create a two-column layout
    col1, col2 = st.columns([1, 1])
    
    with col1:        
        # Building rotation dropdown (only shown if directional factor is enabled)
        if use_direction_factor:
            rotation_options = {
                "0°": 0,
                "30°": 30,
                "60°": 60, 
                "90°": 90,
                "120°": 120,
                "150°": 150,
                "180°": 180,
                "210°": 210,
                "240°": 240,
                "270°": 270,
                "300°": 300,
                "330°": 330
            }
            
            rotation_label = st.selectbox(
                "Building rotation (clockwise from north)",
                options=list(rotation_options.keys()),
                index=0,
                help="Rotate the building orientation clockwise from north"
            )
            
            # Store the selected rotation angle in session state
            st.session_state.inputs["building_rotation"] = rotation_options[rotation_label]
            
            # Display the directional factors for the selected rotation
            st.write("Directional factors for the current orientation:")
            
            # Get the directional factors based on the rotation
            from calc_engine.common.pressure_summary import get_direction_factor
            direction_factors = get_direction_factor(
                st.session_state.inputs["building_rotation"], 
                st.session_state.inputs["use_direction_factor"]
            )
            
            # Display factors as a table
            factor_data = pd.DataFrame({
                "Direction": list(direction_factors.keys()),
                "c_dir": list(direction_factors.values())
            })
            st.dataframe(factor_data, hide_index=True, height=35*len(factor_data)+38)

        else:
            st.markdown("Uniform $$c_{dir}=1.0$$ applied.")
    
    
    # Show the visualization in the second column
    with col2:
        if use_direction_factor:
            # Get building dimensions from session state
            NS_dimension = st.session_state.inputs.get("NS_dimension", 20.0)
            EW_dimension = st.session_state.inputs.get("EW_dimension", 40.0)
            rotation_angle = st.session_state.inputs["building_rotation"]
            
            # Import the visualization function
            from visualisation.directional_viz import create_direction_viz
            
            # Create and display the visualization
            direction_viz = create_direction_viz(rotation_angle, NS_dimension, EW_dimension, height=300, width=300)
            st.plotly_chart(direction_viz)
else:
    # For non-UK regions, set directional factor to 1.0 (not used)
    st.session_state.inputs["use_direction_factor"] = False
    st.session_state.inputs["building_rotation"] = 0
    st.write("Wind directional factors are only available for UK region.")

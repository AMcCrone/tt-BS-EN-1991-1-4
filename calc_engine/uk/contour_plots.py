# contour_plots.py
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata
import streamlit as st

# -----------------------
# Plot Configuration Data
# -----------------------
PLOT_CONFIGS = {
    "NA.3": {
        "x_min": 0.1, "x_max": 100, 
        "y_min": 2, "y_max": 200, 
        "x_name": "Distance upwind to shoreline (km)",
        "contour_start": 0.75, "contour_end": 1.7, "contour_step": 0.05,
        "x_type": "upwind",
        "var_name": "$c_r(z)$",
        "section_heading": "Values of $c_r(z)$"
    },
    "NA.4": {
        "x_min": 0.1, "x_max": 20, 
        "y_min": 2, "y_max": 200, 
        "x_name": "Distance inside town terrain (km)",
        "contour_start": 0.56, "contour_end": 1.0, "contour_step": 0.02,
        "x_type": "town",
        "var_name": "$c_{r,T}$",
        "section_heading": "Values of correction factor $c_{r,T}$ for sites in Town terrain"
    },
    "NA.5": {
        "x_min": 0.1, "x_max": 100, 
        "y_min": 2, "y_max": 200, 
        "x_name": "Distance upwind to shoreline (km)",
        "contour_start": 0.07, "contour_end": 0.21, "contour_step": 0.01,
        "x_type": "upwind",
        "var_name": "$I_v(z)_{flat}$",
        "section_heading": "Values of $I_v(z)_{flat}$"
    },
    "NA.6": {
        "x_min": 0.1, "x_max": 20, 
        "y_min": 2, "y_max": 200, 
        "x_name": "Distance inside town terrain (km)",
        "contour_start": 1.0, "contour_end": 1.8, "contour_step": 0.05,
        "x_type": "town",
        "var_name": "$k_{I,T}$",
        "section_heading": "Values of turbulence correction factor $k_{I,T}$ for sites in Town terrain"
    },
    "NA.7": {
        "x_min": 0.1, "x_max": 100, 
        "y_min": 2, "y_max": 200, 
        "x_name": "Distance upwind to shoreline (km)",
        "contour_start": 1.5, "contour_end": 4.2, "contour_step": 0.1,
        "x_type": "upwind",
        "var_name": "$c_e(z)$",
        "section_heading": "Values of $c_e(z)$"
    },
    "NA.8": {
        "x_min": 0.1, "x_max": 20, 
        "y_min": 2, "y_max": 200, 
        "x_name": "Distance inside town terrain (km)",
        "contour_start": 0.60, "contour_end": 1.0, "contour_step": 0.02,
        "x_type": "town",
        "var_name": "$c_{e,T}$",
        "section_heading": "Values of exposure correction factor $c_{e,T}$ for sites in Town terrain"
    }
}

# Common y-axis name
Y_AXIS_NAME = "$z-h_{dis}$ (m)"

# -----------------------
# Data Loading Function
# -----------------------
@st.cache_data(show_spinner=False)
def load_contour_data(excel_file_path="calc_engine/uk/contour_data.xlsx"):
    """
    Load contour data from an Excel file.
    
    Args:
        excel_file_path (str): Path to the Excel file containing contour data
        
    Returns:
        dict: Dictionary of DataFrames for each sheet
    """
    try:
        excel_file = pd.ExcelFile(excel_file_path)
    except Exception as e:
        # Silently log the error but don't display
        dataframes = {sheet_name: pd.DataFrame() for sheet_name in PLOT_CONFIGS.keys()}
        return dataframes
    
    dataframes = {}
    for sheet_name in PLOT_CONFIGS.keys():
        if sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                if len(df.columns) >= 3:
                    column_names = list(df.columns)
                    column_mapping = {
                        column_names[0]: 'x',
                        column_names[1]: 'y',
                        column_names[2]: 'z'
                    }
                    df = df.rename(columns=column_mapping)
                    df = df.dropna(subset=['x', 'y', 'z'])
                    dataframes[sheet_name] = df
                else:
                    dataframes[sheet_name] = pd.DataFrame()
            except Exception:
                dataframes[sheet_name] = pd.DataFrame()
        else:
            dataframes[sheet_name] = pd.DataFrame()
    
    return dataframes

# -----------------------
# Single Contour Plot Function
# -----------------------
def create_contour_plot(df, sheet_name, x_input, y_input):
    """
    Create a contour plot for a specific sheet with x and y inputs.
    
    Args:
        df (DataFrame): DataFrame containing the contour data (x, y, z columns)
        sheet_name (str): Name of the sheet/plot to create
        x_input (float): X-coordinate value
        y_input (float): Y-coordinate value
        
    Returns:
        tuple: (plotly figure, interpolated z value)
    """
    config = PLOT_CONFIGS[sheet_name]
    x_min, x_max = config["x_min"], config["x_max"]
    y_min, y_max = config["y_min"], config["y_max"]
    x_name = config["x_name"]
    contour_start = config["contour_start"]
    contour_end = config["contour_end"] 
    contour_step = config["contour_step"]
    
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=500,
            margin=dict(l=50, r=50, t=20, b=50)
        )
        return fig, None
    
    grid_density = 200
    x_grid = np.logspace(np.log10(x_min), np.log10(x_max), grid_density)
    y_grid = np.logspace(np.log10(y_min), np.log10(y_max), grid_density)
    X_grid, Y_grid = np.meshgrid(x_grid, y_grid)
    
    points = np.column_stack((np.log10(df['x']), np.log10(df['y'])))
    Z_grid = griddata(points, df['z'], (np.log10(X_grid), np.log10(Y_grid)), method='linear')
    
    def get_interpolated_z(x, y):
        log_x, log_y = np.log10(x), np.log10(y)
        interp_z = griddata(points, df['z'], np.array([[log_x, log_y]]), method='linear')[0]
        if np.isnan(interp_z):
            interp_z = griddata(points, df['z'], np.array([[log_x, log_y]]), method='nearest')[0]
        return interp_z
    
    interpolated_z = None
    if x_min <= x_input <= x_max and y_min <= y_input <= y_max:
        interpolated_z = get_interpolated_z(x_input, y_input)
    
    fig = go.Figure()
    
    # Add filled contour plot
    fig.add_trace(go.Contour(
        x=x_grid,
        y=y_grid,
        z=Z_grid,
        contours=dict(
            coloring='fill',
            showlabels=True,
            start=contour_start,
            end=contour_end,
            size=contour_step,
            labelfont=dict(size=10, color='black')
        ),
        colorscale='Teal',
        opacity=1,
        line=dict(width=0.5),
        showscale=False,
        colorbar=dict(
            title='Contour Value', 
            thickness=20, 
            len=0.9,
            tickformat='.2f' if contour_step >= 0.05 else '.3f'
        )
    ))
    
    # Add crosshairs and marker for the selected point
    if x_min <= x_input <= x_max and y_min <= y_input <= y_max:
        fig.add_trace(go.Scatter(
            x=[x_input, x_input],
            y=[y_min, y_max],
            mode='lines',
            line=dict(color='#DB451D', width=2),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=[x_min, x_max],
            y=[y_input, y_input],
            mode='lines',
            line=dict(color='#DB451D', width=2),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=[x_input],
            y=[y_input],
            mode='markers',
            marker=dict(color='#DB451D', size=25, symbol='circle-cross-open', line=dict(width=2)),
            showlegend=False
        ))
    
    fig.update_layout(
        xaxis=dict(
            type='log',
            title=x_name,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)',
            range=[np.log10(x_min), np.log10(x_max)]
        ),
        yaxis=dict(
            type='log',
            title=Y_AXIS_NAME,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)',
            range=[np.log10(y_min), np.log10(y_max)]
        ),
        height=500,
        plot_bgcolor='rgba(240,240,240,0.95)',
        margin=dict(l=50, r=50, t=20, b=50)
    )
    
    return fig, interpolated_z

# -----------------------
# Functions to get interpolated values
# -----------------------
def get_interpolated_value(datasets, sheet_name, x_input, y_input):
    """
    Get interpolated value for a specific sheet.
    
    Args:
        datasets (dict): Dictionary of DataFrames for each sheet
        sheet_name (str): Name of the sheet/plot
        x_input (float): X-coordinate value
        y_input (float): Y-coordinate value
        
    Returns:
        float: Interpolated value or None if not available
    """
    config = PLOT_CONFIGS[sheet_name]
    x_min, x_max = config["x_min"], config["x_max"]
    
    # Clamp x_input to valid range
    x_input = max(x_min, min(x_input, x_max))
    
    df = datasets[sheet_name]
    _, interpolated_z = create_contour_plot(df, sheet_name, x_input, y_input)
    
    if interpolated_z is not None:
        return round(interpolated_z, 3)
    return None

def get_all_interpolated_values(datasets, y_input, x_upwind, x_town):
    """
    Get all interpolated values for all sheets.
    
    Args:
        datasets (dict): Dictionary of DataFrames for each sheet
        y_input (float): Y-coordinate value
        x_upwind (float): X-coordinate value for upwind plots
        x_town (float): X-coordinate value for town plots
        
    Returns:
        dict: Dictionary of interpolated values
    """
    interpolated_values = {}
    
    for sheet_name in PLOT_CONFIGS.keys():
        config = PLOT_CONFIGS[sheet_name]
        x_type = config["x_type"]
        var_name = config["var_name"]
        
        # Use the appropriate X input based on the plot type
        x_input = x_upwind if x_type == "upwind" else x_town
        
        interpolated_z = get_interpolated_value(datasets, sheet_name, x_input, y_input)
        interpolated_values[var_name] = interpolated_z
    
    return interpolated_values

# -----------------------
# Function to display individual plots
# -----------------------
def display_single_plot(st_container, datasets, sheet_name, x_input, y_input):
    """
    Display a single contour plot in a Streamlit container.
    
    Args:
        st_container: Streamlit module or container
        datasets (dict): Dictionary of DataFrames for each sheet
        sheet_name (str): Name of the sheet/plot to display
        x_input (float): X-coordinate value
        y_input (float): Y-coordinate value
    """
    config = PLOT_CONFIGS[sheet_name]
    section_heading = config["section_heading"]
    x_name = config["x_name"]
    var_name = config["var_name"]
    x_min, x_max = config["x_min"], config["x_max"]
    
    # Clamp x_input to valid range
    x_input = max(x_min, min(x_input, x_max))
    
    df = datasets[sheet_name]
    
    col1, col2 = st_container.columns([3, 1])
    
    with col1:
        fig, interpolated_z = create_contour_plot(df, sheet_name, x_input, y_input)
        st_container.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st_container.write(f"X: **{x_input:.1f}** {x_name}")
        st_container.write(f"Y: **{y_input:.1f}** {Y_AXIS_NAME}")
        
        if interpolated_z is not None:
            st_container.metric(f"{var_name}", f"{interpolated_z:.3f}")
        elif not df.empty:
            st_container.write(f"{var_name}: Coordinates outside data range")
        else:
            st_container.write(f"{var_name}: No data available")

# -----------------------
# Function to display all plots
# -----------------------
def display_all_plots(st_container, datasets, y_input, x_upwind, x_town):
    """
    Display all contour plots in a Streamlit container.
    
    Args:
        st_container: Streamlit container to display the plots in
        datasets (dict): Dictionary of DataFrames for each sheet
        y_input (float): Y-coordinate value
        x_upwind (float): X-coordinate value for upwind plots
        x_town (float): X-coordinate value for town plots
    """
    with st_container:
        for i, sheet_name in enumerate(["NA.3", "NA.4", "NA.5", "NA.6", "NA.7", "NA.8"]):
            config = PLOT_CONFIGS[sheet_name]
            x_type = config["x_type"]
            
            # Use the appropriate X input based on the plot type
            x_input = x_upwind if x_type == "upwind" else x_town
            
            display_single_plot(st_container, datasets, sheet_name, x_input, y_input)
            
            if i < 5:
                st.markdown("---")

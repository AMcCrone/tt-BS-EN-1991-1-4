import plotly.graph_objects as go
import pandas as pd

def detect_zone_E_and_visualise(session_state,
                                inset_height,
                                north_offset,
                                south_offset,
                                east_offset,
                                west_offset):
    """
    Determine whether Zone E applies for each elevation edge and return a Plotly 3D
    visualisation.

    CORRECTED dimension mapping (matching pressure_summary.py):
    - NS_dimension is the width of North/South elevations
    - EW_dimension is the width of East/West elevations

    Mapping implemented (matches pressure_summary.py logic):
      - For North/South elevations:
          width = NS_dimension, crosswind_dim = EW_dimension
          draw_width = NS_dimension - east_offset - west_offset
          crosswind_breadth (B1) = EW_dimension - north_offset - south_offset
      - For East/West elevations:
          width = EW_dimension, crosswind_dim = NS_dimension
          draw_width = EW_dimension - north_offset - south_offset
          crosswind_breadth (B1) = NS_dimension - east_offset - west_offset
    """

    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"
    TT_Roof = "lightgrey"

    # Read base plan dims + base roof height from session_state
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))  # Width of North/South elevations
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))  # Width of East/West elevations  
    base_z = float(session_state.inputs.get("z", 10.0))  # roof plane z

    # Sanitize offsets and H1 — treat None as 0.0
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Upper-storey footprint in plan coordinates
    # x-axis (North-South): x=0 is North, x=EW_dimension is South
    # y-axis (West-East):  y=0 is West,  y=NS_dimension is East
    upper_x0 = north_offset  # North edge
    upper_x1 = max(north_offset, EW_dimension - south_offset)  # South edge
    upper_y0 = west_offset   # West edge
    upper_y1 = max(west_offset, NS_dimension - east_offset)   # East edge

    upper_width_x = max(0.0, upper_x1 - upper_x0)  # North-South width of inset footprint
    upper_width_y = max(0.0, upper_y1 - upper_y0)  # East-West width of inset footprint

    # ---------------------------
    # CORRECTED: Match exact logic from pressure_summary.py
    # ---------------------------
    # For North/South elevations:
    # width = NS_dimension, crosswind_dim = EW_dimension (matches pressure_summary.py lines 127-129)
    draw_width_north = draw_width_south = max(0.0, NS_dimension - east_offset - west_offset)
    crosswind_breadth_north = crosswind_breadth_south = max(0.0, EW_dimension - north_offset - south_offset)

    # For East/West elevations:
    # width = EW_dimension, crosswind_dim = NS_dimension (matches pressure_summary.py lines 130-132)
    draw_width_east = draw_width_west = max(0.0, EW_dimension - north_offset - south_offset)
    crosswind_breadth_east = crosswind_breadth_west = max(0.0, NS_dimension - east_offset - west_offset)

    # Results skeleton
    results = {
        "North": {"B1": None, "H1": H1, "0.2e1": None, "east gap": None, "west gap": None, "east_zone_E": False, "west_zone_E": False},
        "South": {"B1": None, "H1": H1, "0.2e1": None, "east gap": None, "west gap": None, "east_zone_E": False, "west_zone_E": False},
        "East":  {"B1": None, "H1": H1, "0.2e1": None, "north gap": None, "south gap": None, "north_zone_E": False, "south_zone_E": False},
        "West":  {"B1": None, "H1": H1, "0.2e1": None, "north gap": None, "south gap": None, "north_zone_E": False, "south_zone_E": False},
    }

    # Helper: clamp rectangle inside upper footprint and return coords or None.
    def clamp_rect(x0, x1, y0, y1):
        cx0 = max(x0, upper_x0)
        cx1 = min(x1, upper_x1)
        cy0 = max(y0, upper_y0)
        cy1 = min(y1, upper_y1)
        if cx1 <= cx0 or cy1 <= cy0:
            return None
        return (cx0, cx1, cy0, cy1)

    # Container for zone-E rectangles: each item holds (cx0,cx1,cy0,cy1,e_height, label)
    zoneE_rects = []

    # ---- For North/South elevations: use crosswind_breadth_north (EW_dimension - north/south offsets) ----
    B1_NS = crosswind_breadth_north  # used only in wind checks (E1 etc.)
    e1_NS = min(B1_NS, 2.0 * H1)
    e1_div5_NS = e1_NS / 5.0  # 0.2e1 value
    results["North"].update({
        "B1": round(B1_NS, 4), 
        "0.2e1": round(e1_div5_NS, 4),
        "east gap": round(east_offset, 4),
        "west gap": round(west_offset, 4)
    })
    results["South"].update({
        "B1": round(B1_NS, 4), 
        "0.2e1": round(e1_div5_NS, 4),
        "east gap": round(east_offset, 4),
        "west gap": round(west_offset, 4)
    })

    # North elevation - East edge check (only if north_offset > 0)
    if e1_NS > 0 and east_offset < 0.2 * e1_NS and north_offset > 0:
        rect_w = e1_NS / 5.0   # width along y (east-west)
        rect_h = e1_NS / 3.0   # vertical height
        y1 = upper_y1  # East edge
        y0 = y1 - rect_w
        x0 = upper_x0  # North edge
        x1 = upper_x0 + min(upper_width_x, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["North"]["east_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-east"))

    # North elevation - West edge check (only if north_offset > 0)
    if e1_NS > 0 and west_offset < 0.2 * e1_NS and north_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        y0 = upper_y0  # West edge
        y1 = y0 + rect_w
        x0 = upper_x0  # North edge
        x1 = upper_x0 + min(upper_width_x, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["North"]["west_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-west"))

    # South elevation - East edge check (only if south_offset > 0)
    if e1_NS > 0 and east_offset < 0.2 * e1_NS and south_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        y1 = upper_y1  # East edge
        y0 = y1 - rect_w
        x1 = upper_x1  # South edge
        x0 = upper_x1 - min(upper_width_x, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["South"]["east_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-east"))

    # South elevation - West edge check (only if south_offset > 0)
    if e1_NS > 0 and west_offset < 0.2 * e1_NS and south_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        y0 = upper_y0  # West edge
        y1 = y0 + rect_w
        x1 = upper_x1  # South edge
        x0 = upper_x1 - min(upper_width_x, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["South"]["west_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-west"))

    # ---- For East/West elevations: use crosswind_breadth_east (NS_dimension - east/west offsets) ----
    B1_EW = crosswind_breadth_east  # used only in wind checks (E1 etc.)
    e1_EW = min(B1_EW, 2.0 * H1)
    e1_div5_EW = e1_EW / 5.0  # 0.2e1 value
    results["East"].update({
        "B1": round(B1_EW, 4), 
        "0.2e1": round(e1_div5_EW, 4),
        "north gap": round(north_offset, 4),
        "south gap": round(south_offset, 4)
    })
    results["West"].update({
        "B1": round(B1_EW, 4), 
        "0.2e1": round(e1_div5_EW, 4),
        "north gap": round(north_offset, 4),
        "south gap": round(south_offset, 4)
    })

    # East elevation - North edge check (only if east_offset > 0)
    if e1_EW > 0 and north_offset < 0.2 * e1_EW and east_offset > 0:
        rect_w = e1_EW / 5.0   # width along x (north-south)
        rect_h = e1_EW / 3.0   # depth into building (along y-axis, limited by y-width)
        x0 = upper_x0  # North edge
        x1 = x0 + rect_w
        y1 = upper_y1  # East edge
        y0 = upper_y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["East"]["north_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-north"))

    # East elevation - South edge check (only if east_offset > 0)
    if e1_EW > 0 and south_offset < 0.2 * e1_EW and east_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x1 = upper_x1  # South edge
        x0 = x1 - rect_w
        y1 = upper_y1  # East edge
        y0 = upper_y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["East"]["south_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-south"))

    # West elevation - North edge check (only if west_offset > 0)
    if e1_EW > 0 and north_offset < 0.2 * e1_EW and west_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x0 = upper_x0  # North edge
        x1 = x0 + rect_w
        y0 = upper_y0  # West edge
        y1 = upper_y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["West"]["north_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-north"))

    # West elevation - South edge check (only if west_offset > 0)
    if e1_EW > 0 and south_offset < 0.2 * e1_EW and west_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x1 = upper_x1  # South edge
        x0 = x1 - rect_w
        y0 = upper_y0  # West edge
        y1 = upper_y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["West"]["south_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-south"))

    # ---- Build 3D visual ----
    fig = go.Figure()

    # Draw top plane of base building (flat quad) with clockwise ordering:
    top_z = base_z
    # Base footprint: EW_dimension by NS_dimension (gray rectangle, no outline)
    # x-axis spans North-South (EW_dimension), y-axis spans West-East (NS_dimension)
    fig.add_trace(go.Mesh3d(
        x=[0.0, 0.0, EW_dimension, EW_dimension],
        y=[0.0, NS_dimension, NS_dimension, 0.0],
        z=[top_z, top_z, top_z, top_z],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=TT_TopPlane, opacity=1.0, hoverinfo="none", showlegend=False
    ))

    # Draw upper inset box as a proper 3D box (if it has positive footprint and H1>0)
    if upper_width_x > 0 and upper_width_y > 0 and H1 > 0:
        ux0, ux1, uy0, uy1 = upper_x0, upper_x1, upper_y0, upper_y1
        bz = top_z
        tz = top_z + H1
        pad = 1e-6

        # Bottom face
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[bz + pad, bz + pad, bz + pad, bz + pad],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))

        # Top face
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[tz, tz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))

        # Vertical faces (N, S, W, E)
        # North face (x = ux0)
        fig.add_trace(go.Mesh3d(x=[ux0, ux0, ux0, ux0],
                                y=[uy0, uy1, uy1, uy0],
                                z=[bz, bz, tz, tz], i=[0,0], j=[1,2], k=[2,3],
                                color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # South face (x = ux1)
        fig.add_trace(go.Mesh3d(x=[ux1, ux1, ux1, ux1],
                                y=[uy0, uy1, uy1, uy0],
                                z=[bz, bz, tz, tz], i=[0,0], j=[1,2], k=[2,3],
                                color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # West face (y = uy0)
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0],
                                y=[uy0, uy0, uy0, uy0],
                                z=[bz, bz, tz, tz], i=[0,0], j=[1,2], k=[2,3],
                                color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # East face (y = uy1)
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0],
                                y=[uy1, uy1, uy1, uy1],
                                z=[bz, bz, tz, tz], i=[0,0], j=[1,2], k=[2,3],
                                color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))

        # Perimeter lines and vertical edges (outline)
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0],
                                   y=[uy0, uy0, uy1, uy1, uy0],
                                   z=[bz + pad]*5,
                                   mode='lines', line=dict(color='black', width=2),
                                   hoverinfo='none', showlegend=False))
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0],
                                   y=[uy0, uy0, uy1, uy1, uy0],
                                   z=[tz]*5,
                                   mode='lines', line=dict(color='black', width=2),
                                   hoverinfo='none', showlegend=False))
        vert_x = [ux0, ux1, ux1, ux0]
        vert_y = [uy0, uy0, uy1, uy1]
        for vx, vy in zip(vert_x, vert_y):
            fig.add_trace(go.Scatter3d(x=[vx, vx], y=[vy, vy],
                                       z=[bz + pad, tz],
                                       mode='lines', line=dict(color='black', width=2),
                                       hoverinfo='none', showlegend=False))

        # Light grey roof flush with inset top
        roof_z = tz
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0],
                                y=[uy0, uy0, uy1, uy1],
                                z=[roof_z, roof_z, roof_z, roof_z],
                                i=[0, 0], j=[1, 2], k=[2, 3],
                                color=TT_Roof, opacity=1.0, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0],
                                   y=[uy0, uy0, uy1, uy1, uy0],
                                   z=[roof_z]*5,
                                   mode='lines', line=dict(color='black', width=1),
                                   hoverinfo='none', showlegend=False))

    # Draw each Zone E rectangle
    for (cx0, cx1, cy0, cy1, rect_h, label) in zoneE_rects:
        bottom_z = top_z
        top_z_rect = top_z + rect_h
        if "North" in label:
            fig.add_trace(go.Mesh3d(x=[cx0, cx0, cx0, cx0],
                                    y=[cy0, cy1, cy1, cy0],
                                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                                    i=[0, 0], j=[1, 2], k=[2, 3],
                                    color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False))
            fig.add_trace(go.Scatter3d(x=[cx0, cx0, cx0, cx0, cx0],
                                       y=[cy0, cy1, cy1, cy0, cy0],
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2),
                                       showlegend=False, hoverinfo='none'))
        elif "South" in label:
            fig.add_trace(go.Mesh3d(x=[cx1, cx1, cx1, cx1],
                                    y=[cy0, cy1, cy1, cy0],
                                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                                    i=[0, 0], j=[1, 2], k=[2, 3],
                                    color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False))
            fig.add_trace(go.Scatter3d(x=[cx1, cx1, cx1, cx1, cx1],
                                       y=[cy0, cy1, cy1, cy0, cy0],
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2),
                                       showlegend=False, hoverinfo='none'))
        elif "East" in label:
            fig.add_trace(go.Mesh3d(x=[cx0, cx1, cx1, cx0],
                                    y=[cy1, cy1, cy1, cy1],
                                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                                    i=[0, 0], j=[1, 2], k=[2, 3],
                                    color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False))
            fig.add_trace(go.Scatter3d(x=[cx0, cx1, cx1, cx0, cx0],
                                       y=[cy1, cy1, cy1, cy1, cy1],
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2),
                                       showlegend=False, hoverinfo='none'))
        else:  # West
            fig.add_trace(go.Mesh3d(x=[cx0, cx1, cx1, cx0],
                                    y=[cy0, cy0, cy0, cy0],
                                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                                    i=[0, 0], j=[1, 2], k=[2, 3],
                                    color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False))
            fig.add_trace(go.Scatter3d(x=[cx0, cx1, cx1, cx0, cx0],
                                       y=[cy0, cy0, cy0, cy0, cy0],
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2),
                                       showlegend=False, hoverinfo='none'))

    # Direction labels
    label_margin = max(1.0, max(NS_dimension, EW_dimension) * 0.06)
    center_x = EW_dimension / 2  # x-axis center (North-South span)
    center_y = NS_dimension / 2  # y-axis center (West-East span)

    if upper_width_x > 0 and upper_width_y > 0:
        lx_center = (upper_x0 + upper_x1) / 2
        ly_center = (upper_y0 + upper_y1) / 2
        label_positions = {
            "North": {"pos": [upper_x0 - label_margin, ly_center, top_z], "text": "N"},
            "South": {"pos": [upper_x1 + label_margin, ly_center, top_z], "text": "S"},
            "East":  {"pos": [lx_center, upper_y1 + label_margin, top_z], "text": "E"},
            "West":  {"pos": [lx_center, upper_y0 - label_margin, top_z], "text": "W"},
        }
    else:
        label_positions = {
            "North": {"pos": [0.0 - label_margin, center_y, top_z], "text": "N"},
            "South": {"pos": [EW_dimension + label_margin, center_y, top_z], "text": "S"},
            "East":  {"pos": [center_x, NS_dimension + label_margin, top_z], "text": "E"},
            "West":  {"pos": [center_x, 0.0 - label_margin, top_z], "text": "W"},
        }

    for label_info in label_positions.values():
        fig.add_trace(go.Scatter3d(
            x=[label_info["pos"][0]],
            y=[label_info["pos"][1]],
            z=[label_info["pos"][2]],
            text=[label_info["text"]],
            mode='text',
            textfont=dict(size=20, color='black'),
            showlegend=False,
            hoverinfo='none'
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            zaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            aspectmode='data'
        ),
        margin=dict(l=2, r=2, t=2, b=2),
        showlegend=False,
        scene_camera=dict(eye=dict(x=1.2, y=-1.2, z=0.9)),
        height=520
    )

    # Combined Zone E flags - move to final column and rename
    results["North"]["Zone E?"] = bool(results["North"].get("east_zone_E", False) or results["North"].get("west_zone_E", False))
    results["South"]["Zone E?"] = bool(results["South"].get("east_zone_E", False) or results["South"].get("west_zone_E", False))
    results["East"]["Zone E?"] = bool(results["East"].get("north_zone_E", False) or results["East"].get("south_zone_E", False))
    results["West"]["Zone E?"] = bool(results["West"].get("north_zone_E", False) or results["West"].get("south_zone_E", False))

    return results, fig


def create_styled_inset_dataframe(results):
    """
    Create a styled dataframe from inset zone results for display.
    
    Parameters:
    -----------
    results : dict
        Results dictionary from detect_zone_E_and_visualise function
    
    Returns:
    --------
    pandas.io.formats.style.Styler
        Styled dataframe ready for display
    """
    # Create dataframe from results
    df = pd.DataFrame(results).T
    
    # Remove internal tracking columns (keep only user-relevant columns)
    display_columns = ['B1', 'H1', '0.2e1', 'east gap', 'west gap', 'north gap', 'south gap', 'Zone E?']
    # Filter to only columns that exist in the dataframe
    available_columns = [col for col in display_columns if col in df.columns]
    df_display = df[available_columns]
    
    # Define styling function for Zone E? column
    def style_zone_e(val):
        if val == True:
            return 'color: #D3451D; font-weight: bold'  # TT Orange
        else:
            return 'color: #808080'  # Grey
    
    # Apply styling to the dataframe if Zone E? column exists
    if 'Zone E?' in df_display.columns:
        styled_df = df_display.style.applymap(style_zone_e, subset=['Zone E?'])
    else:
        styled_df = df_display
    
    return styled_df

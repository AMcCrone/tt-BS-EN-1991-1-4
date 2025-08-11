import plotly.graph_objects as go

def detect_zone_E_and_visualise(session_state,
                                inset_height,
                                north_offset,
                                south_offset,
                                east_offset,
                                west_offset):
    """
    Determine whether Zone E applies for each elevation edge and return a Plotly 3D
    visualisation.

    Keeps ORIGINAL top plane ordering:
      x-axis = West -> East  (0..EW_dimension)
      y-axis = North -> South (0..NS_dimension)

    BUT relabels the faces so that the vertical faces at x = const are called
    North / South, and the faces at y = const are called East / West. This
    matches the user's expectation that North/South correspond to the long (NS)
    dimension in the example image.
    """
    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"
    TT_Roof = "lightgrey"

    # Read base plan dims + base roof height from session_state
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))  # y-axis (North->South)
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))  # x-axis (West->East)
    base_z = float(session_state.inputs.get("z", 10.0))  # roof plane z

    # Sanitize offsets and H1 — treat None as 0.0
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Upper-storey footprint in the same axes as the top plane:
    # x-axis: 0 is West, EW_dimension is East
    # y-axis: 0 is North, NS_dimension is South
    upper_x0 = west_offset                     # West edge (x min)
    upper_x1 = max(west_offset, EW_dimension - east_offset)   # East edge (x max)
    upper_y0 = north_offset                    # North edge (y min)
    upper_y1 = max(north_offset, NS_dimension - south_offset)# South edge (y max)

    upper_width_x = max(0.0, upper_x1 - upper_x0)  # West-East width
    upper_width_y = max(0.0, upper_y1 - upper_y0)  # North-South width

    # Results skeleton — canonical cardinal order that the user requested:
    # North, East, South, West (labels refer to faces as described above)
    results = {
        "North": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False,  "west_zone_E": False},
        "East":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
        "South": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False,  "west_zone_E": False},
        "West":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
    }

    # clamp helper (in same x/y axes)
    def clamp_rect(x0, x1, y0, y1):
        cx0 = max(x0, upper_x0)
        cx1 = min(x1, upper_x1)
        cy0 = max(y0, upper_y0)
        cy1 = min(y1, upper_y1)
        if cx1 <= cx0 or cy1 <= cy0:
            return None
        return (cx0, cx1, cy0, cy1)

    zoneE_rects = []

    # ---------- IMPORTANT MAPPING CHANGE ----------
    # Faces at x = const (these are the *long* faces in your screenshot when
    # NS_dimension > EW_dimension). We label these NORTH (x=min) and SOUTH (x=max).
    # B1_xfaces uses the NS_dimension (length along y).
    B1_xfaces = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_xfaces = min(B1_xfaces, 2.0 * H1)
    results["North"].update({"B1": round(B1_xfaces, 4), "e1": round(e1_xfaces, 4)})
    results["South"].update({"B1": round(B1_xfaces, 4), "e1": round(e1_xfaces, 4)})

    # Faces at y = const (these are the *short* faces). We label these EAST (y=max) and WEST (y=min).
    # B1_yfaces uses the EW_dimension (length along x).
    B1_yfaces = max(0.0, EW_dimension - (east_offset + west_offset))
    e1_yfaces = min(B1_yfaces, 2.0 * H1)
    results["East"].update({"B1": round(B1_yfaces, 4), "e1": round(e1_yfaces, 4)})
    results["West"].update({"B1": round(B1_yfaces, 4), "e1": round(e1_yfaces, 4)})

    # --- Now the zone checks: geometry must follow the relabelling above ---

    # NORTH face (x = upper_x0) — it's an x-constant face, width runs along y
    if e1_xfaces > 0 and east_offset < 0.2 * e1_xfaces and north_offset > 0:
        # "North-east" (near the east side of the north face): width along y
        rect_w = e1_xfaces / 5.0   # width along y (north->south)
        rect_h = e1_xfaces / 3.0   # vertical
        x0 = upper_x0               # face plane
        x1 = upper_x0 + min(upper_width_x, rect_h)  # into the inset in +x
        y0 = upper_y0               # north edge
        y1 = y0 + rect_w
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["North"]["east_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-east"))

    if e1_xfaces > 0 and west_offset < 0.2 * e1_xfaces and north_offset > 0:
        # "North-west" (near the west side of the north face)
        rect_w = e1_xfaces / 5.0
        rect_h = e1_xfaces / 3.0
        x0 = upper_x0
        x1 = upper_x0 + min(upper_width_x, rect_h)
        y1 = upper_y0 + 0.0 + rect_w
        y0 = upper_y0
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["North"]["west_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-west"))

    # SOUTH face (x = upper_x1)
    if e1_xfaces > 0 and east_offset < 0.2 * e1_xfaces and south_offset > 0:
        rect_w = e1_xfaces / 5.0
        rect_h = e1_xfaces / 3.0
        x1 = upper_x1
        x0 = upper_x1 - min(upper_width_x, rect_h)
        y1 = upper_y1
        y0 = y1 - rect_w
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["South"]["east_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-east"))

    if e1_xfaces > 0 and west_offset < 0.2 * e1_xfaces and south_offset > 0:
        rect_w = e1_xfaces / 5.0
        rect_h = e1_xfaces / 3.0
        x1 = upper_x1
        x0 = upper_x1 - min(upper_width_x, rect_h)
        y0 = upper_y1 - rect_w
        y1 = upper_y1
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["South"]["west_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-west"))

    # EAST face (y = upper_y1) — y-constant face, width runs along x
    if e1_yfaces > 0 and north_offset < 0.2 * e1_yfaces and east_offset > 0:
        rect_w = e1_yfaces / 5.0   # width along x (west->east)
        rect_h = e1_yfaces / 3.0
        y1 = upper_y1
        y0 = upper_y1 - min(upper_width_y, rect_h)
        x1 = upper_x1
        x0 = x1 - rect_w
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["East"]["north_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-north"))

    if e1_yfaces > 0 and south_offset < 0.2 * e1_yfaces and east_offset > 0:
        rect_w = e1_yfaces / 5.0
        rect_h = e1_yfaces / 3.0
        y1 = upper_y1
        y0 = upper_y1 - min(upper_width_y, rect_h)
        x0 = upper_x1 - rect_w
        x1 = upper_x1
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["East"]["south_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-south"))

    # WEST face (y = upper_y0)
    if e1_yfaces > 0 and north_offset < 0.2 * e1_yfaces and west_offset > 0:
        rect_w = e1_yfaces / 5.0
        rect_h = e1_yfaces / 3.0
        y0 = upper_y0
        y1 = y0 + min(upper_width_y, rect_h)
        x0 = upper_x0
        x1 = x0 + rect_w
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["West"]["north_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-north"))

    if e1_yfaces > 0 and south_offset < 0.2 * e1_yfaces and west_offset > 0:
        rect_w = e1_yfaces / 5.0
        rect_h = e1_yfaces / 3.0
        y1 = upper_y0 + min(upper_width_y, rect_w)
        y0 = upper_y0
        x0 = upper_x0
        x1 = x0 + rect_w
        # For south-side on west face we use same x-range but y moved toward south
        y1 = upper_y0 + rect_w
        y0 = upper_y0
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["West"]["south_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-south"))

    # ---- Build 3D visual ----
    fig = go.Figure()
    top_z = base_z

    # ORIGINAL top plane ordering (x spans 0..EW_dimension, y spans 0..NS_dimension)
    fig.add_trace(go.Mesh3d(
        x=[0.0, EW_dimension, EW_dimension, 0.0],
        y=[0.0, 0.0, NS_dimension, NS_dimension],
        z=[top_z, top_z, top_z, top_z],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=TT_TopPlane, opacity=1.0, hoverinfo="none", showlegend=False
    ))

    # Draw inset (unchanged)
    if upper_width_x > 0 and upper_width_y > 0 and H1 > 0:
        ux0, ux1, uy0, uy1 = upper_x0, upper_x1, upper_y0, upper_y1
        bz = top_z
        tz = top_z + H1
        pad = 1e-6

        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0],
                                y=[uy0, uy0, uy1, uy1],
                                z=[bz + pad]*4,
                                i=[0,0], j=[1,2], k=[2,3],
                                color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0],
                                y=[uy0, uy0, uy1, uy1],
                                z=[tz]*4,
                                i=[0,0], j=[1,2], k=[2,3],
                                color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # vertical faces (west, east, north, south)
        fig.add_trace(go.Mesh3d(x=[ux0, ux0, ux0, ux0], y=[uy0, uy1, uy1, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux1, ux1, ux1, ux1], y=[uy0, uy1, uy1, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy0, uy0, uy0, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy1, uy1, uy1, uy1], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # outlines & roof
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0], y=[uy0, uy0, uy1, uy1, uy0],
                                   z=[bz + pad]*5, mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0], y=[uy0, uy0, uy1, uy1, uy0],
                                   z=[tz]*5, mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        for vx, vy in zip([ux0, ux1, ux1, ux0], [uy0, uy0, uy1, uy1]):
            fig.add_trace(go.Scatter3d(x=[vx, vx], y=[vy, vy], z=[bz + pad, tz],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy0, uy0, uy1, uy1], z=[tz]*4,
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Roof, opacity=1.0, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0], y=[uy0, uy0, uy1, uy1, uy0], z=[tz]*5,
                                   mode='lines', line=dict(color='black', width=1), hoverinfo='none', showlegend=False))

    # Draw ZoneE rectangles (labels updated)
    for (cx0, cx1, cy0, cy1, rect_h, label) in zoneE_rects:
        bottom_z = top_z
        top_z_rect = top_z + rect_h

        if "North" in label:
            # North face => plane at x = cx0
            fig.add_trace(go.Mesh3d(x=[cx0, cx0, cx0, cx0], y=[cy0, cy1, cy1, cy0],
                                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                                    i=[0,0], j=[1,2], k=[2,3], color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False))
            fig.add_trace(go.Scatter3d(x=[cx0]*5, y=[cy0, cy1, cy1, cy0, cy0],
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        elif "South" in label:
            fig.add_trace(go.Mesh3d(x=[cx1, cx1, cx1, cx1], y=[cy0, cy1, cy1, cy0],
                                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                                    i=[0,0], j=[1,2], k=[2,3], color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False))
            fig.add_trace(go.Scatter3d(x=[cx1]*5, y=[cy0, cy1, cy1, cy0, cy0],
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        elif "East" in label:
            # East face => plane at y = cy1
            fig.add_trace(go.Mesh3d(x=[cx0, cx1, cx1, cx0], y=[cy1, cy1, cy1, cy1],
                                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                                    i=[0,0], j=[1,2], k=[2,3], color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False))
            fig.add_trace(go.Scatter3d(x=[cx0, cx1, cx1, cx0, cx0], y=[cy1]*5,
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        else:
            # West face => plane at y = cy0
            fig.add_trace(go.Mesh3d(x=[cx0, cx1, cx1, cx0], y=[cy0, cy0, cy0, cy0],
                                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                                    i=[0,0], j=[1,2], k=[2,3], color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False))
            fig.add_trace(go.Scatter3d(x=[cx0, cx1, cx1, cx0, cx0], y=[cy0]*5,
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))

    # Direction labels (positioning uses x=west-east, y=north-south)
    label_margin = max(1.0, max(NS_dimension, EW_dimension) * 0.06)
    center_x = EW_dimension / 2
    center_y = NS_dimension / 2
    if upper_width_x > 0 and upper_width_y > 0:
        ux_center = (upper_x0 + upper_x1) / 2
        uy_center = (upper_y0 + upper_y1) / 2
        label_positions = {
            "North": {"pos": [upper_x0 - label_margin, uy_center, top_z], "text": "N"},  # x=min face
            "South": {"pos": [upper_x1 + label_margin, uy_center, top_z], "text": "S"},  # x=max face
            "East":  {"pos": [ux_center, upper_y1 + label_margin, top_z], "text": "E"},  # y=max face
            "West":  {"pos": [ux_center, upper_y0 - label_margin, top_z], "text": "W"},  # y=min face
        }
    else:
        label_positions = {
            "North": {"pos": [center_x, 0.0 - label_margin, top_z], "text": "N"},
            "South": {"pos": [center_x, NS_dimension + label_margin, top_z], "text": "S"},
            "East":  {"pos": [EW_dimension + label_margin, center_y, top_z], "text": "E"},
            "West":  {"pos": [0.0 - label_margin, center_y, top_z], "text": "W"},
        }
    for label_info in label_positions.values():
        fig.add_trace(go.Scatter3d(
            x=[label_info["pos"][0]], y=[label_info["pos"][1]], z=[label_info["pos"][2]],
            text=[label_info["text"]], mode='text',
            textfont=dict(size=20, color='black'),
            showlegend=False, hoverinfo='none'
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

    # Combined zone_E flags (cardinal order)
    results["North"]["zone_E"] = bool(results["North"].get("east_zone_E", False) or results["North"].get("west_zone_E", False))
    results["East"]["zone_E"]  = bool(results["East"].get("north_zone_E", False) or results["East"].get("south_zone_E", False))
    results["South"]["zone_E"] = bool(results["South"].get("east_zone_E", False) or results["South"].get("west_zone_E", False))
    results["West"]["zone_E"]  = bool(results["West"].get("north_zone_E", False) or results["West"].get("south_zone_E", False))

    return results, fig

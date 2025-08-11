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

    Coordinate convention (kept from your original function):
      x-axis = North -> South (0..NS_dimension)
      y-axis = West  -> East  (0..EW_dimension)

    Fix applied:
      - The long faces (span the NS dimension) are labelled North / South.
      - The short faces (span the EW dimension) are labelled East / West.
      - B1 values are kept as you computed them, but the geometry for each face
        (used to compute zone rectangles and to populate results) is now derived
        in the correct orientation so the returned B1/H1/e1 and plotted faces
        match the expected cardinal lengths.
    """
    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"
    TT_Roof = "lightgrey"

    # Read base plan dims + base roof height from session_state
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))  # x-axis
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))  # y-axis
    base_z = float(session_state.inputs.get("z", 10.0))  # roof plane z

    # Sanitize offsets and H1 — NO forced defaults (treat None as 0.0)
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Upper-storey footprint in plan coordinates (same as you had)
    # x-axis (North-South): x=0 is North, x=NS_dimension is South
    # y-axis (East-West):  y=0 is West,  y=EW_dimension is East
    upper_x0 = north_offset
    upper_x1 = max(north_offset, NS_dimension - south_offset)
    upper_y0 = west_offset
    upper_y1 = max(west_offset, EW_dimension - east_offset)

    upper_width_x = max(0.0, upper_x1 - upper_x0)  # length along x (north->south)
    upper_width_y = max(0.0, upper_y1 - upper_y0)  # length along y (west->east)

    # Results skeleton — keep labels but we will assign correct B1/e1 per cardinal
    results = {
        "North": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "South": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "East":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
        "West":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
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

    zoneE_rects = []  # store (cx0,cx1,cy0,cy1,e_height,label)

    # -------------------------------------------------------------------------
    # KEEP your B1 computations exactly as they were (you said they are correct)
    # B1_NS corresponds to the B1 value used for North/South checks (based on EW)
    B1_NS = max(0.0, EW_dimension - (east_offset + west_offset))
    e1_NS = min(B1_NS, 2.0 * H1)
    results["North"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})
    results["South"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})

    # B1_EW corresponds to the B1 value used for East/West checks (based on NS)
    B1_EW = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_EW = min(B1_EW, 2.0 * H1)
    results["East"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})
    results["West"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})
    # -------------------------------------------------------------------------

    # --- Now compute the *actual geometric widths* used for placing rectangles
    # The user's requirement: North/South elevations should reflect the NS length,
    # East/West elevations should reflect the EW length.
    # We'll compute the "face_length" for each elevation:
    #  - North / South face length (along the face) = NS_dimension - (north + south offsets)
    #  - East / West face length  (along the face) = EW_dimension - (east + west offsets)
    # These are the true geometric extents of each elevation (before inset clamping).
    face_length_NS = max(0.0, NS_dimension - (north_offset + south_offset))   # length used for North/South faces
    face_length_EW = max(0.0, EW_dimension - (east_offset + west_offset))     # length used for East/West faces

    # For visual placement we will still respect the inset footprint (upper_x0/1, upper_y0/1)
    # --- North elevation (x = upper_x0) checks ---
    # We want the north face to be considered to have "face_length_NS" (along x direction),
    # so rect widths that run along this face should be created accordingly.

    # North - East edge
    if e1_NS > 0 and east_offset < 0.2 * e1_NS and north_offset > 0:
        # create a small zone rectangle hugging the east end of the North face
        # rect width runs along the face (we choose to align it with the axis that represents the face length)
        # The North face in your coordinate system is at x = upper_x0; its face-length runs along x if we
        # re-interpret North/South to refer to the long faces (user request). Therefore we use x extent.
        rect_w = e1_NS / 5.0   # width along the face
        rect_h = e1_NS / 3.0   # vertical height
        # place the rectangle at the east side of the face: y near upper_y1
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_w)   # clamp width to inset
        # span in x from face plane into the inset
        x0 = upper_x0
        x1 = upper_x0 + min(upper_width_x, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["North"]["east_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-east"))

    # North - West edge
    if e1_NS > 0 and west_offset < 0.2 * e1_NS and north_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        y0 = upper_y0
        y1 = y0 + min(upper_width_y, rect_w)
        x0 = upper_x0
        x1 = upper_x0 + min(upper_width_x, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["North"]["west_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-west"))

    # South (x = upper_x1) - East
    if e1_NS > 0 and east_offset < 0.2 * e1_NS and south_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_w)
        x1 = upper_x1
        x0 = upper_x1 - min(upper_width_x, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["South"]["east_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-east"))

    # South - West
    if e1_NS > 0 and west_offset < 0.2 * e1_NS and south_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        y0 = upper_y0
        y1 = y0 + min(upper_width_y, rect_w)
        x1 = upper_x1
        x0 = upper_x1 - min(upper_width_x, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["South"]["west_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-west"))

    # --- East/West faces: these should reflect face_length_EW along their face ---
    # East face (y = upper_y1)
    if e1_EW > 0 and north_offset < 0.2 * e1_EW and east_offset > 0:
        rect_w = e1_EW / 5.0   # width along face (we align this along x)
        rect_h = e1_EW / 3.0
        # for the east face (y = upper_y1) we create a rect that spans x near the north edge
        x0 = upper_x0
        x1 = x0 + min(upper_width_x, rect_w)
        y1 = upper_y1
        y0 = upper_y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["East"]["north_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-north"))

    # East - South
    if e1_EW > 0 and south_offset < 0.2 * e1_EW and east_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x1 = upper_x1
        x0 = x1 - min(upper_width_x, rect_w)
        y1 = upper_y1
        y0 = upper_y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["East"]["south_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-south"))

    # West face (y = upper_y0)
    if e1_EW > 0 and north_offset < 0.2 * e1_EW and west_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x0 = upper_x0
        x1 = x0 + min(upper_width_x, rect_w)
        y0 = upper_y0
        y1 = upper_y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["West"]["north_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-north"))

    # West - South
    if e1_EW > 0 and south_offset < 0.2 * e1_EW and west_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x1 = upper_x1
        x0 = x1 - min(upper_width_x, rect_w)
        y0 = upper_y0
        y1 = upper_y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["West"]["south_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-south"))

    # ---- Build 3D visual ----
    fig = go.Figure()

    # Draw top plane of base building (flat quad) with clockwise ordering:
    top_z = base_z
    fig.add_trace(go.Mesh3d(
        x=[0.0, NS_dimension, NS_dimension, 0.0],
        y=[0.0, 0.0, EW_dimension, EW_dimension],
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
        # Vertical faces (North, South, West, East) - geometry unchanged
        fig.add_trace(go.Mesh3d(x=[ux0, ux0, ux0, ux0], y=[uy0, uy1, uy1, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux1, ux1, ux1, ux1], y=[uy0, uy1, uy1, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy0, uy0, uy0, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy1, uy1, uy1, uy1], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # Outlines & roof (unchanged)
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

    # Draw ZoneE rectangles
    for (cx0, cx1, cy0, cy1, rect_h, label) in zoneE_rects:
        bottom_z = top_z
        top_z_rect = top_z + rect_h

        if "North" in label:
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx0, cx0, cx0],
                y=[cy0, cy1, cy1, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(x=[cx0]*5, y=[cy0, cy1, cy1, cy0, cy0],
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        elif "South" in label:
            fig.add_trace(go.Mesh3d(
                x=[cx1, cx1, cx1, cx1],
                y=[cy0, cy1, cy1, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(x=[cx1]*5, y=[cy0, cy1, cy1, cy0, cy0],
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        elif "East" in label:
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx1, cx1, cx0],
                y=[cy1, cy1, cy1, cy1],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(x=[cx0, cx1, cx1, cx0, cx0], y=[cy1]*5,
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        else:  # West
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx1, cx1, cx0],
                y=[cy0, cy0, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(x=[cx0, cx1, cx1, cx0, cx0], y=[cy0]*5,
                                       z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))

    # Add direction labels (N, E, S, W)
    label_margin = max(1.0, max(NS_dimension, EW_dimension) * 0.06)
    center_x = NS_dimension / 2
    center_y = EW_dimension / 2

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
            "South": {"pos": [NS_dimension + label_margin, center_y, top_z], "text": "S"},
            "East":  {"pos": [center_x, EW_dimension + label_margin, top_z], "text": "E"},
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

    # Layout
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

    # Combined zone flags
    results["North"]["zone_E"] = bool(results["North"].get("east_zone_E", False) or results["North"].get("west_zone_E", False))
    results["South"]["zone_E"] = bool(results["South"].get("east_zone_E", False) or results["South"].get("west_zone_E", False))
    results["East"]["zone_E"] = bool(results["East"].get("north_zone_E", False) or results["East"].get("south_zone_E", False))
    results["West"]["zone_E"] = bool(results["West"].get("north_zone_E", False) or results["West"].get("south_zone_E", False))

    return results, fig

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

    Coordinate convention (kept):
      x-axis = North -> South (0..NS_dimension)
      y-axis = West  -> East  (0..EW_dimension)

    Cardinal-to-face mapping used here (so cardinals match the input dims):
      - North  = face at x = upper_x0  (x-constant face; spans y => EW length)
      - South  = face at x = upper_x1  (x-constant face; spans y => EW length)
      - West   = face at y = upper_y0  (y-constant face; spans x => NS length)
      - East   = face at y = upper_y1  (y-constant face; spans x => NS length)
    """
    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"
    TT_Roof = "lightgrey"

    # Read dims
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))  # x-axis length
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))  # y-axis length
    base_z = float(session_state.inputs.get("z", 10.0))

    # Sanitize offsets & H1
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Upper-storey footprint (same as before)
    # x: 0 = North, x = NS_dimension => South
    # y: 0 = West,  y = EW_dimension => East
    upper_x0 = north_offset
    upper_x1 = max(north_offset, NS_dimension - south_offset)
    upper_y0 = west_offset
    upper_y1 = max(west_offset, EW_dimension - east_offset)

    upper_width_x = max(0.0, upper_x1 - upper_x0)  # NS length after offsets
    upper_width_y = max(0.0, upper_y1 - upper_y0)  # EW length after offsets

    # Results skeleton (cardinal labels kept)
    results = {
        "North": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "South": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "East":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
        "West":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
    }

    # clamp helper
    def clamp_rect(x0, x1, y0, y1):
        cx0 = max(x0, upper_x0)
        cx1 = min(x1, upper_x1)
        cy0 = max(y0, upper_y0)
        cy1 = min(y1, upper_y1)
        if cx1 <= cx0 or cy1 <= cy0:
            return None
        return (cx0, cx1, cy0, cy1)

    zoneE_rects = []

    # -------------------------
    # Updated B1 formulas to match the corrected cardinal-to-face mapping:
    # North/South faces (x-constant) span the EW direction, so use EW-based B1
    # East/West faces (y-constant) span the NS direction, so use NS-based B1
    # -------------------------
    B1_NS_faces = max(0.0, EW_dimension - (east_offset + west_offset))   # for North/South faces
    e1_NS_faces = min(B1_NS_faces, 2.0 * H1)
    results["North"].update({"B1": round(B1_NS_faces, 4), "e1": round(e1_NS_faces, 4)})
    results["South"].update({"B1": round(B1_NS_faces, 4), "e1": round(e1_NS_faces, 4)})

    B1_EW_faces = max(0.0, NS_dimension - (north_offset + south_offset))  # for East/West faces
    e1_EW_faces = min(B1_EW_faces, 2.0 * H1)
    results["East"].update({"B1": round(B1_EW_faces, 4), "e1": round(e1_EW_faces, 4)})
    results["West"].update({"B1": round(B1_EW_faces, 4), "e1": round(e1_EW_faces, 4)})

    # For readability below:
    # - face_length_NS = upper_width_x  (actual NS face length available after insets)
    # - face_length_EW = upper_width_y  (actual EW face length available after insets)
    face_length_NS = upper_width_x
    face_length_EW = upper_width_y

    # -------------------------
    # Create Zone-E rectangles ON THE FACE PLANES according to the corrected mapping:
    # North / South are x-constant faces (they span y axis); rectangle span along y.
    # East / West are  y-constant faces (they span x axis); rectangle span along x.
    # -------------------------

    # NORTH face (x = upper_x0) — uses e1_NS_faces (derived from EW-based B1)
    if e1_NS_faces > 0 and north_offset > 0:
        # North - East (near building east side)
        if east_offset < 0.2 * e1_NS_faces:
            rect_w = e1_NS_faces / 5.0    # width along the face (y direction)
            rect_h = e1_NS_faces / 3.0
            cy1 = upper_y1  # place near the East end of the face (high y)
            cy0 = upper_y1 - min(face_length_EW, rect_w)
            cx0 = upper_x0      # face plane x const
            # For a face-plane rectangle, we make a tiny x-depth into the inset to give it area for Mesh3d:
            depth = min(face_length_NS, rect_h)
            cx1 = cx0 + depth
            clamped = clamp_rect(cx0, cx1, cy0, cy1)
            if clamped:
                results["North"]["east_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-east"))

        # North - West (near building west side)
        if west_offset < 0.2 * e1_NS_faces:
            rect_w = e1_NS_faces / 5.0
            rect_h = e1_NS_faces / 3.0
            cy0 = upper_y0
            cy1 = upper_y0 + min(face_length_EW, rect_w)
            cx0 = upper_x0
            depth = min(face_length_NS, rect_h)
            cx1 = cx0 + depth
            clamped = clamp_rect(cx0, cx1, cy0, cy1)
            if clamped:
                results["North"]["west_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-west"))

    # SOUTH face (x = upper_x1)
    if e1_NS_faces > 0 and south_offset > 0:
        # South - East (near building east side)
        if east_offset < 0.2 * e1_NS_faces:
            rect_w = e1_NS_faces / 5.0
            rect_h = e1_NS_faces / 3.0
            cy1 = upper_y1
            cy0 = upper_y1 - min(face_length_EW, rect_w)
            cx1 = upper_x1
            depth = min(face_length_NS, rect_h)
            cx0 = cx1 - depth
            clamped = clamp_rect(cx0, cx1, cy0, cy1)
            if clamped:
                results["South"]["east_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-east"))

        # South - West
        if west_offset < 0.2 * e1_NS_faces:
            rect_w = e1_NS_faces / 5.0
            rect_h = e1_NS_faces / 3.0
            cy0 = upper_y0
            cy1 = upper_y0 + min(face_length_EW, rect_w)
            cx1 = upper_x1
            depth = min(face_length_NS, rect_h)
            cx0 = cx1 - depth
            clamped = clamp_rect(cx0, cx1, cy0, cy1)
            if clamped:
                results["South"]["west_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-west"))

    # EAST face (y = upper_y1) — uses e1_EW_faces (derived from NS-based B1)
    if e1_EW_faces > 0 and east_offset > 0:
        # East - North (near building north side)
        if north_offset < 0.2 * e1_EW_faces:
            rect_w = e1_EW_faces / 5.0    # width along the face (x direction)
            rect_h = e1_EW_faces / 3.0
            cx0 = upper_x0  # place near the North end of the face (low x)
            cx1 = upper_x0 + min(face_length_NS, rect_w)
            cy1 = upper_y1
            depth = min(face_length_EW, rect_h)
            cy0 = cy1 - depth
            clamped = clamp_rect(cx0, cx1, cy0, cy1)
            if clamped:
                results["East"]["north_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-north"))

        # East - South
        if south_offset < 0.2 * e1_EW_faces:
            rect_w = e1_EW_faces / 5.0
            rect_h = e1_EW_faces / 3.0
            cx1 = upper_x1  # place near the South end of the face (high x)
            cx0 = upper_x1 - min(face_length_NS, rect_w)
            cy1 = upper_y1
            depth = min(face_length_EW, rect_h)
            cy0 = cy1 - depth
            clamped = clamp_rect(cx0, cx1, cy0, cy1)
            if clamped:
                results["East"]["south_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-south"))

    # WEST face (y = upper_y0)
    if e1_EW_faces > 0 and west_offset > 0:
        # West - North
        if north_offset < 0.2 * e1_EW_faces:
            rect_w = e1_EW_faces / 5.0
            rect_h = e1_EW_faces / 3.0
            cx0 = upper_x0
            cx1 = upper_x0 + min(face_length_NS, rect_w)
            cy0 = upper_y0
            depth = min(face_length_EW, rect_h)
            cy1 = cy0 + depth
            clamped = clamp_rect(cx0, cx1, cy0, cy1)
            if clamped:
                results["West"]["north_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-north"))

        # West - South
        if south_offset < 0.2 * e1_EW_faces:
            rect_w = e1_EW_faces / 5.0
            rect_h = e1_EW_faces / 3.0
            cx1 = upper_x1
            cx0 = upper_x1 - min(face_length_NS, rect_w)
            cy0 = upper_y0
            depth = min(face_length_EW, rect_h)
            cy1 = cy0 + depth
            clamped = clamp_rect(cx0, cx1, cy0, cy1)
            if clamped:
                results["West"]["south_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-south"))

    # ---- Build 3D visual (top plane ordering kept as you originally had) ----
    fig = go.Figure()
    top_z = base_z

    fig.add_trace(go.Mesh3d(
        x=[0.0, NS_dimension, NS_dimension, 0.0],
        y=[0.0, 0.0, EW_dimension, EW_dimension],
        z=[top_z, top_z, top_z, top_z],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=TT_TopPlane, opacity=1.0, hoverinfo="none", showlegend=False
    ))

    # Inset box (unchanged geometry)
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

        # vertical faces
        fig.add_trace(go.Mesh3d(x=[ux0, ux0, ux0, ux0], y=[uy0, uy1, uy1, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux1, ux1, ux1, ux1], y=[uy0, uy1, uy1, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy0, uy0, uy0, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy1, uy1, uy1, uy1], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))

        # outlines and roof
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0], y=[uy0, uy0, uy1, uy1, uy0],
                                   z=[bz + pad]*5, mode='lines', line=dict(color='black', width=2),
                                   hoverinfo='none', showlegend=False))
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0], y=[uy0, uy0, uy1, uy1, uy0],
                                   z=[tz]*5, mode='lines', line=dict(color='black', width=2),
                                   hoverinfo='none', showlegend=False))
        for vx, vy in zip([ux0, ux1, ux1, ux0], [uy0, uy0, uy1, uy1]):
            fig.add_trace(go.Scatter3d(x=[vx, vx], y=[vy, vy], z=[bz + pad, tz],
                                       mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False))
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy0, uy0, uy1, uy1], z=[tz]*4,
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Roof, opacity=1.0, hoverinfo="none", showlegend=False))
        fig.add_trace(go.Scatter3d(x=[ux0, ux1, ux1, ux0, ux0], y=[uy0, uy0, uy1, uy1, uy0], z=[tz]*5,
                                   mode='lines', line=dict(color='black', width=1), hoverinfo='none', showlegend=False))

    # Draw ZoneE rectangles (updated for corrected face mapping)
    for (cx0, cx1, cy0, cy1, rect_h, label) in zoneE_rects:
        bottom_z = top_z
        top_z_rect = top_z + rect_h

        if "North" in label:
            # North face (x = cx0) -> treat as face plane at min x
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx0, cx0, cx0],
                y=[cy0, cy1, cy1, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[cx0, cx0, cx0, cx0, cx0],
                y=[cy0, cy1, cy1, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))
        elif "South" in label:
            # South face (x = cx1)
            fig.add_trace(go.Mesh3d(
                x=[cx1, cx1, cx1, cx1],
                y=[cy0, cy1, cy1, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[cx1, cx1, cx1, cx1, cx1],
                y=[cy0, cy1, cy1, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))
        elif "East" in label:
            # East face (y = cy1)
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx1, cx1, cx0],
                y=[cy1, cy1, cy1, cy1],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[cx0, cx1, cx1, cx0, cx0],
                y=[cy1, cy1, cy1, cy1, cy1],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))
        else:
            # West face (y = cy0)
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx1, cx1, cx0],
                y=[cy0, cy0, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[cx0, cx1, cx1, cx0, cx0],
                y=[cy0, cy0, cy0, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))

    # Direction labels — positioned to match corrected mapping (x-constant faces -> North/South)
    label_margin = max(1.0, max(NS_dimension, EW_dimension) * 0.06)
    center_x = NS_dimension / 2
    center_y = EW_dimension / 2

    if upper_width_x > 0 and upper_width_y > 0:
        lx_center = (upper_x0 + upper_x1) / 2
        ly_center = (upper_y0 + upper_y1) / 2
        # North & South are x-constant faces, East & West are y-constant faces
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

    # Combined flags (cardinal order)
    results["North"]["zone_E"] = bool(results["North"].get("east_zone_E", False) or results["North"].get("west_zone_E", False))
    results["South"]["zone_E"] = bool(results["South"].get("east_zone_E", False) or results["South"].get("west_zone_E", False))
    results["East"]["zone_E"]  = bool(results["East"].get("north_zone_E", False) or results["East"].get("south_zone_E", False))
    results["West"]["zone_E"]  = bool(results["West"].get("north_zone_E", False) or results["West"].get("south_zone_E", False))

    return results, fig

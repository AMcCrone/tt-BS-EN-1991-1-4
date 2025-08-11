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

    Coordinate convention:
      x-axis = North -> South (0..NS_dimension)
      y-axis = West  -> East  (0..EW_dimension)
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

    # Sanitize offsets and H1 — treat None as 0.0
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Upper-storey footprint in plan coordinates (same as you had)
    # x-axis (North-South): x=0 is North, x=NS_dimension is South
    # y-axis (West-East):    y=0 is West,  y=EW_dimension is East
    upper_x0 = north_offset
    upper_x1 = max(north_offset, NS_dimension - south_offset)
    upper_y0 = west_offset
    upper_y1 = max(west_offset, EW_dimension - east_offset)

    upper_width_x = max(0.0, upper_x1 - upper_x0)  # North-South footprint length
    upper_width_y = max(0.0, upper_y1 - upper_y0)  # West-East footprint length

    # Results skeleton
    results = {
        "North": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "South": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "East":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
        "West":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
    }

    def clamp_rect(x0, x1, y0, y1):
        cx0 = max(x0, upper_x0)
        cx1 = min(x1, upper_x1)
        cy0 = max(y0, upper_y0)
        cy1 = min(y1, upper_y1)
        if cx1 <= cx0 or cy1 <= cy0:
            return None
        return (cx0, cx1, cy0, cy1)

    zoneE_rects = []

    # ---- Keep your original B1 calculations (they were correct) ----
    # For North/South checks B1 is based on EW dimension
    B1_NS = max(0.0, EW_dimension - (east_offset + west_offset))
    e1_NS = min(B1_NS, 2.0 * H1)
    results["North"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})
    results["South"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})

    # For East/West checks B1 is based on NS dimension
    B1_EW = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_EW = min(B1_EW, 2.0 * H1)
    results["East"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})
    results["West"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})

    # ----- Compute explicit corner coordinates (remove ambiguity) -----
    # corners: (x, y)
    NW = (upper_x0, upper_y0)
    NE = (upper_x0, upper_y1)
    SW = (upper_x1, upper_y0)
    SE = (upper_x1, upper_y1)

    # A small helper to add a corner-based rectangle and tag it with the face it belongs to.
    # This ensures plotting uses the explicit face plane rather than inferring it from coordinates.
    def add_corner_rect(corner_x, corner_y, inward_along_x_sign, inward_along_y_sign,
                        rect_w, rect_h, face, label):
        """
        corner_x, corner_y : coordinates of the corner on the inset footprint
        inward_along_x_sign : +1 if depth into inset increases x, -1 if decreases x
        inward_along_y_sign : +1 if width along face increases y, -1 if decreases y
        rect_w : desired width along the face (along the face axis)
        rect_h : desired depth (how far into the inset the rectangle reaches)
        face : one of "North","South","East","West" -> explicit face the rectangle belongs to
        label : textual label (e.g. "South-east")
        """
        # depth (perpendicular into inset) and width (along-face)
        depth = min(upper_width_x, rect_h)   # use x-extent for depth clamp where appropriate
        width = min(upper_width_y, rect_w)   # use y-extent for face-width clamp where appropriate

        # Compute x-range (depth into inset)
        if inward_along_x_sign > 0:
            x0 = corner_x
            x1 = corner_x + min(upper_width_x, rect_h)
        else:
            x1 = corner_x
            x0 = corner_x - min(upper_width_x, rect_h)

        # Compute y-range (along-face width)
        if inward_along_y_sign > 0:
            y0 = corner_y
            y1 = corner_y + min(upper_width_y, rect_w)
        else:
            y1 = corner_y
            y0 = corner_y - min(upper_width_y, rect_w)

        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            # Append face explicitly so drawing uses the face plane
            zoneE_rects.append({
                "x0": clamped[0], "x1": clamped[1],
                "y0": clamped[2], "y1": clamped[3],
                "h": rect_h, "label": label, "face": face
            })
            return True
        return False

    # ---- Place corner rectangles using the correct corner coordinates and the explicit face tag ----
    # NE, NW, SE, SW corners defined earlier:
    NW = (upper_x0, upper_y0)
    NE = (upper_x0, upper_y1)
    SW = (upper_x1, upper_y0)
    SE = (upper_x1, upper_y1)

    # NORTH face (y = upper_y0) uses e1_NS
    if e1_NS > 0 and north_offset > 0:
        if east_offset < 0.2 * e1_NS:
            rect_w = e1_NS / 5.0
            rect_h = e1_NS / 3.0
            # north-east: corner is (upper_x0, upper_y1) but face is NORTH (y = upper_y0)
            add_ok = add_corner_rect(NE[0], NE[1], inward_along_x_sign=+1, inward_along_y_sign=-1,
                                     rect_w=rect_w, rect_h=rect_h, face="North", label="North-east")
            if add_ok:
                results["North"]["east_zone_E"] = True
        if west_offset < 0.2 * e1_NS:
            rect_w = e1_NS / 5.0
            rect_h = e1_NS / 3.0
            add_ok = add_corner_rect(NW[0], NW[1], inward_along_x_sign=+1, inward_along_y_sign=+1,
                                     rect_w=rect_w, rect_h=rect_h, face="North", label="North-west")
            if add_ok:
                results["North"]["west_zone_E"] = True

    # SOUTH face (y = upper_y1)
    if e1_NS > 0 and south_offset > 0:
        if east_offset < 0.2 * e1_NS:
            rect_w = e1_NS / 5.0
            rect_h = e1_NS / 3.0
            add_ok = add_corner_rect(SE[0], SE[1], inward_along_x_sign=-1, inward_along_y_sign=-1,
                                     rect_w=rect_w, rect_h=rect_h, face="South", label="South-east")
            if add_ok:
                results["South"]["east_zone_E"] = True
        if west_offset < 0.2 * e1_NS:
            rect_w = e1_NS / 5.0
            rect_h = e1_NS / 3.0
            add_ok = add_corner_rect(SW[0], SW[1], inward_along_x_sign=-1, inward_along_y_sign=+1,
                                     rect_w=rect_w, rect_h=rect_h, face="South", label="South-west")
            if add_ok:
                results["South"]["west_zone_E"] = True

    # EAST face (x = upper_x1) uses e1_EW
    if e1_EW > 0 and east_offset > 0:
        if north_offset < 0.2 * e1_EW:
            rect_w = e1_EW / 5.0
            rect_h = e1_EW / 3.0
            add_ok = add_corner_rect(NE[0], NE[1], inward_along_x_sign=-1, inward_along_y_sign=-1,
                                     rect_w=rect_w, rect_h=rect_h, face="East", label="East-north")
            if add_ok:
                results["East"]["north_zone_E"] = True
        if south_offset < 0.2 * e1_EW:
            rect_w = e1_EW / 5.0
            rect_h = e1_EW / 3.0
            add_ok = add_corner_rect(SE[0], SE[1], inward_along_x_sign=-1, inward_along_y_sign=-1,
                                     rect_w=rect_w, rect_h=rect_h, face="East", label="East-south")
            if add_ok:
                results["East"]["south_zone_E"] = True

    # WEST face (x = upper_x0)
    if e1_EW > 0 and west_offset > 0:
        if north_offset < 0.2 * e1_EW:
            rect_w = e1_EW / 5.0
            rect_h = e1_EW / 3.0
            add_ok = add_corner_rect(NW[0], NW[1], inward_along_x_sign=+1, inward_along_y_sign=+1,
                                     rect_w=rect_w, rect_h=rect_h, face="West", label="West-north")
            if add_ok:
                results["West"]["north_zone_E"] = True
        if south_offset < 0.2 * e1_EW:
            rect_w = e1_EW / 5.0
            rect_h = e1_EW / 3.0
            add_ok = add_corner_rect(SW[0], SW[1], inward_along_x_sign=+1, inward_along_y_sign=+1,
                                     rect_w=rect_w, rect_h=rect_h, face="West", label="West-south")
            if add_ok:
                results["West"]["south_zone_E"] = True

    # ---- DRAW using the explicit face tag (replace the previous draw loop) ----
    for rect in zoneE_rects:
        cx0, cx1 = rect["x0"], rect["x1"]
        cy0, cy1 = rect["y0"], rect["y1"]
        rect_h = rect["h"]
        label = rect["label"]
        face = rect["face"]

        bottom_z = top_z
        top_z_rect = top_z + rect_h

        if face == "North":
            # North face: y = upper_y0 (plane), x spans cx0..cx1
            y_plane = upper_y0
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx1, cx1, cx0],
                y=[y_plane, y_plane, y_plane, y_plane],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0,0], j=[1,2], k=[2,3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[cx0, cx1, cx1, cx0, cx0],
                y=[y_plane]*5,
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))
        elif face == "South":
            y_plane = upper_y1
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx1, cx1, cx0],
                y=[y_plane, y_plane, y_plane, y_plane],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0,0], j=[1,2], k=[2,3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[cx0, cx1, cx1, cx0, cx0],
                y=[y_plane]*5,
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))
        elif face == "East":
            x_plane = upper_x1
            fig.add_trace(go.Mesh3d(
                x=[x_plane, x_plane, x_plane, x_plane],
                y=[cy0, cy1, cy1, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0,0], j=[1,2], k=[2,3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[x_plane]*5,
                y=[cy0, cy1, cy1, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))
        else:  # West
            x_plane = upper_x0
            fig.add_trace(go.Mesh3d(
                x=[x_plane, x_plane, x_plane, x_plane],
                y=[cy0, cy1, cy1, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0,0], j=[1,2], k=[2,3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[x_plane]*5,
                y=[cy0, cy1, cy1, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))

    # Direction labels (we keep your existing styling / positions)
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

    # Combined flags
    results["North"]["zone_E"] = bool(results["North"].get("east_zone_E", False) or results["North"].get("west_zone_E", False))
    results["South"]["zone_E"] = bool(results["South"].get("east_zone_E", False) or results["South"].get("west_zone_E", False))
    results["East"]["zone_E"] = bool(results["East"].get("north_zone_E", False) or results["East"].get("south_zone_E", False))
    results["West"]["zone_E"] = bool(results["West"].get("north_zone_E", False) or results["West"].get("south_zone_E", False))

    return results, fig

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

    Coordinate convention used here:
      x-axis = North -> South (0..NS_dimension)
      y-axis = West  -> East  (0..EW_dimension)

    Cardinal-face mapping:
      - North  = face at y = upper_y0  (y-constant face that spans x -> NS length)
      - South  = face at y = upper_y1  (y-constant face that spans x -> NS length)
      - West   = face at x = upper_x0  (x-constant face that spans y -> EW length)
      - East   = face at x = upper_x1  (x-constant face that spans y -> EW length)
    """
    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"
    TT_Roof = "lightgrey"

    # Read base plan dims + base roof height from session_state
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))  # x-axis length (North->South)
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))  # y-axis length (West->East)
    base_z = float(session_state.inputs.get("z", 10.0))  # roof plane z

    # Sanitize offsets and H1 — treat None as 0.0
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Upper-storey footprint in plan coordinates
    # x-axis (North-South): x=0 is North, x=NS_dimension is South
    # y-axis (West-East):    y=0 is West,  y=EW_dimension is East
    upper_x0 = north_offset
    upper_x1 = max(north_offset, NS_dimension - south_offset)
    upper_y0 = west_offset
    upper_y1 = max(west_offset, EW_dimension - east_offset)

    upper_width_x = max(0.0, upper_x1 - upper_x0)  # available NS length after offsets
    upper_width_y = max(0.0, upper_y1 - upper_y0)  # available EW length after offsets

    # Results dict skeleton (canonical cardinals)
    results = {
        "North": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "East":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
        "South": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "West":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
    }

    # Helper to clamp rectangle inside inset footprint
    def clamp_rect(x0, x1, y0, y1):
        cx0 = max(x0, upper_x0)
        cx1 = min(x1, upper_x1)
        cy0 = max(y0, upper_y0)
        cy1 = min(y1, upper_y1)
        if cx1 <= cx0 or cy1 <= cy0:
            return None
        return (cx0, cx1, cy0, cy1)

    # zoneE_rects will store dicts with explicit 'face' tag so drawing is unambiguous
    zoneE_rects = []

    # -------------------------------------------------------------------------
    # B1 / e1 calculations
    # - B1_long: NS-based (used for North/South faces, long faces)
    # - B1_short: EW-based (used for East/West faces, short faces)
    # Keep these calculations consistent and assign to the appropriate cardinals.
    # -------------------------------------------------------------------------
    B1_short = max(0.0, EW_dimension - (east_offset + west_offset))   # short ends (EW direction)
    e1_short = min(B1_short, 2.0 * H1)
    results["East"].update({"B1": round(B1_short, 4), "e1": round(e1_short, 4)})
    results["West"].update({"B1": round(B1_short, 4), "e1": round(e1_short, 4)})

    B1_long = max(0.0, NS_dimension - (north_offset + south_offset))  # long faces (NS direction)
    e1_long = min(B1_long, 2.0 * H1)
    results["North"].update({"B1": round(B1_long, 4), "e1": round(e1_long, 4)})
    results["South"].update({"B1": round(B1_long, 4), "e1": round(e1_long, 4)})

    # Precompute corners (x, y) on the inset footprint
    # NW = top-left (north-west), NE = top-right (north-east), etc. (in x,y axes)
    NW = (upper_x0, upper_y0)
    NE = (upper_x0, upper_y1)
    SW = (upper_x1, upper_y0)
    SE = (upper_x1, upper_y1)

    # Helper to add a corner-shaped rectangle tagged with an explicit face
    def add_corner_rect(corner_x, corner_y, inward_x_sign, inward_y_sign, rect_w, rect_h, face, label):
        """
        corner_x, corner_y : coordinates of the corner on inset footprint
        inward_x_sign : +1 if depth into inset increases x (southwards), -1 if decreases x (northwards)
        inward_y_sign : +1 if width along face increases y (west->east), -1 otherwise
        rect_w : width along the face axis (along-face)
        rect_h : depth into the inset (perpendicular to face)
        face : "North","South","East","West" (explicit face the rect belongs to)
        label : textual label for debug / later
        """
        # depth: how far into the inset along x (we clamp to available upper_width_x)
        depth = min(upper_width_x, rect_h)
        # width: along-face width along y (clamp to upper_width_y)
        width = min(upper_width_y, rect_w)

        # compute x-range (depth into inset)
        if inward_x_sign > 0:
            x0 = corner_x
            x1 = corner_x + depth
        else:
            x1 = corner_x
            x0 = corner_x - depth

        # compute y-range (along-face width)
        if inward_y_sign > 0:
            y0 = corner_y
            y1 = corner_y + width
        else:
            y1 = corner_y
            y0 = corner_y - width

        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({
                "x0": clamped[0], "x1": clamped[1],
                "y0": clamped[2], "y1": clamped[3],
                "h": rect_h, "label": label, "face": face
            })
            return True
        return False

    # -------------------------
    # Place zone rectangles (corner-based) and set result flags.
    # Use e1_long for North/South checks, e1_short for East/West checks.
    # The inward signs are chosen so rectangles extend into the inset correctly.
    # -------------------------

    # NORTH face (y = upper_y0) — long-face e1_long
    if e1_long > 0 and north_offset > 0:
        # North - East (near the eastern corner of the north face)
        if east_offset < 0.2 * e1_long:
            rect_w = e1_long / 5.0
            rect_h = e1_long / 3.0
            # NE corner, extend into inset in +x (southwards) and along-face towards west (-y)
            if add_corner_rect(NE[0], NE[1], inward_x_sign=+1, inward_y_sign=-1,
                               rect_w=rect_w, rect_h=rect_h, face="North", label="North-east"):
                results["North"]["east_zone_E"] = True

        # North - West
        if west_offset < 0.2 * e1_long:
            rect_w = e1_long / 5.0
            rect_h = e1_long / 3.0
            # NW corner, extend into inset in +x and along-face +y
            if add_corner_rect(NW[0], NW[1], inward_x_sign=+1, inward_y_sign=+1,
                               rect_w=rect_w, rect_h=rect_h, face="North", label="North-west"):
                results["North"]["west_zone_E"] = True

    # SOUTH face (y = upper_y1) — long-face e1_long
    if e1_long > 0 and south_offset > 0:
        # South - East (SE corner) extend -x (northwards) and along-face -y
        if east_offset < 0.2 * e1_long:
            rect_w = e1_long / 5.0
            rect_h = e1_long / 3.0
            if add_corner_rect(SE[0], SE[1], inward_x_sign=-1, inward_y_sign=-1,
                               rect_w=rect_w, rect_h=rect_h, face="South", label="South-east"):
                results["South"]["east_zone_E"] = True

        # South - West (SW corner) extend -x and along-face +y
        if west_offset < 0.2 * e1_long:
            rect_w = e1_long / 5.0
            rect_h = e1_long / 3.0
            if add_corner_rect(SW[0], SW[1], inward_x_sign=-1, inward_y_sign=+1,
                               rect_w=rect_w, rect_h=rect_h, face="South", label="South-west"):
                results["South"]["west_zone_E"] = True

    # EAST face (x = upper_x1) — short-face e1_short
    if e1_short > 0 and east_offset > 0:
        # East - North: place near the north end of the east face
        if north_offset < 0.2 * e1_short:
            rect_w = e1_short / 5.0
            rect_h = e1_short / 3.0
            # NE corner: extend depth -x (northwards) and along-face -y
            if add_corner_rect(NE[0], NE[1], inward_x_sign=-1, inward_y_sign=-1,
                               rect_w=rect_w, rect_h=rect_h, face="East", label="East-north"):
                results["East"]["north_zone_E"] = True

        # East - South
        if south_offset < 0.2 * e1_short:
            rect_w = e1_short / 5.0
            rect_h = e1_short / 3.0
            # SE corner: extend depth -x and along-face -y
            if add_corner_rect(SE[0], SE[1], inward_x_sign=-1, inward_y_sign=-1,
                               rect_w=rect_w, rect_h=rect_h, face="East", label="East-south"):
                results["East"]["south_zone_E"] = True

    # WEST face (x = upper_x0) — short-face e1_short
    if e1_short > 0 and west_offset > 0:
        # West - North
        if north_offset < 0.2 * e1_short:
            rect_w = e1_short / 5.0
            rect_h = e1_short / 3.0
            # NW corner: extend depth +x (southwards) and along-face +y
            if add_corner_rect(NW[0], NW[1], inward_x_sign=+1, inward_y_sign=+1,
                               rect_w=rect_w, rect_h=rect_h, face="West", label="West-north"):
                results["West"]["north_zone_E"] = True

        # West - South
        if south_offset < 0.2 * e1_short:
            rect_w = e1_short / 5.0
            rect_h = e1_short / 3.0
            # SW corner: extend depth +x and along-face +y
            if add_corner_rect(SW[0], SW[1], inward_x_sign=+1, inward_y_sign=+1,
                               rect_w=rect_w, rect_h=rect_h, face="West", label="West-south"):
                results["West"]["south_zone_E"] = True

    # ---- Build 3D visual ----
    fig = go.Figure()
    top_z = base_z

    # Draw top plane of base building (flat quad)
    # NOTE: x spans 0..NS_dimension, y spans 0..EW_dimension consistent with convention
    fig.add_trace(go.Mesh3d(
        x=[0.0, NS_dimension, NS_dimension, 0.0],
        y=[0.0, 0.0, EW_dimension, EW_dimension],
        z=[top_z, top_z, top_z, top_z],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=TT_TopPlane, opacity=1.0, hoverinfo="none", showlegend=False
    ))

    # Draw upper inset box (bottom, top, vertical faces)
    if upper_width_x > 0 and upper_width_y > 0 and H1 > 0:
        ux0, ux1, uy0, uy1 = upper_x0, upper_x1, upper_y0, upper_y1
        bz = top_z
        tz = top_z + H1
        pad = 1e-6

        # bottom
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[bz + pad, bz + pad, bz + pad, bz + pad],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # top
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[tz, tz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # vertical faces
        # face at x = ux0 (west face)
        fig.add_trace(go.Mesh3d(x=[ux0, ux0, ux0, ux0], y=[uy0, uy1, uy1, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # face at x = ux1 (east face)
        fig.add_trace(go.Mesh3d(x=[ux1, ux1, ux1, ux1], y=[uy0, uy1, uy1, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # face at y = uy0 (north face)
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy0, uy0, uy0, uy0], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))
        # face at y = uy1 (south face)
        fig.add_trace(go.Mesh3d(x=[ux0, ux1, ux1, ux0], y=[uy1, uy1, uy1, uy1], z=[bz, bz, tz, tz],
                                i=[0,0], j=[1,2], k=[2,3], color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False))

        # outlines (base/top) and vertical edges
        fig.add_trace(go.Scatter3d(
            x=[ux0, ux1, ux1, ux0, ux0],
            y=[uy0, uy0, uy1, uy1, uy0],
            z=[bz + pad]*5,
            mode='lines',
            line=dict(color='black', width=2),
            hoverinfo='none', showlegend=False
        ))
        fig.add_trace(go.Scatter3d(
            x=[ux0, ux1, ux1, ux0, ux0],
            y=[uy0, uy0, uy1, uy1, uy0],
            z=[tz]*5,
            mode='lines',
            line=dict(color='black', width=2),
            hoverinfo='none', showlegend=False
        ))
        for vx, vy in zip([ux0, ux1, ux1, ux0], [uy0, uy0, uy1, uy1]):
            fig.add_trace(go.Scatter3d(
                x=[vx, vx], y=[vy, vy], z=[bz + pad, tz],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))

        # roof (flush)
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[tz, tz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Roof, opacity=1.0, hoverinfo="none", showlegend=False
        ))
        fig.add_trace(go.Scatter3d(
            x=[ux0, ux1, ux1, ux0, ux0],
            y=[uy0, uy0, uy1, uy1, uy0],
            z=[tz]*5, mode='lines', line=dict(color='black', width=1), hoverinfo='none', showlegend=False
        ))

    # ---- Draw ZoneE rectangles using the explicit 'face' tag ----
    for rect in zoneE_rects:
        cx0, cx1, cy0, cy1, rect_h, label, face = (
            rect["x0"], rect["x1"], rect["y0"], rect["y1"], rect["h"], rect["label"], rect["face"]
        )
        bottom_z = top_z
        top_z_rect = top_z + rect_h

        if face == "North":
            y_plane = upper_y0
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx1, cx1, cx0],
                y=[y_plane, y_plane, y_plane, y_plane],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0,0], j=[1,2], k=[2,3], color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
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
                i=[0,0], j=[1,2], k=[2,3], color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
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
                i=[0,0], j=[1,2], k=[2,3], color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
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
                i=[0,0], j=[1,2], k=[2,3], color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[x_plane]*5,
                y=[cy0, cy1, cy1, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines', line=dict(color='black', width=2), hoverinfo='none', showlegend=False
            ))

    # Direction labels (North, East, South, West)
    label_margin = max(1.0, max(NS_dimension, EW_dimension) * 0.06)
    if upper_width_x > 0 and upper_width_y > 0:
        lx_center = (upper_x0 + upper_x1) / 2
        ly_center = (upper_y0 + upper_y1) / 2
        label_positions = {
            "North": {"pos": [lx_center, upper_y0 - label_margin, top_z], "text": "N"},
            "South": {"pos": [lx_center, upper_y1 + label_margin, top_z], "text": "S"},
            "East":  {"pos": [upper_x1 + label_margin, ly_center, top_z], "text": "E"},
            "West":  {"pos": [upper_x0 - label_margin, ly_center, top_z], "text": "W"},
        }
    else:
        center_x = NS_dimension / 2
        center_y = EW_dimension / 2
        label_positions = {
            "North": {"pos": [center_x, 0.0 - label_margin, top_z], "text": "N"},
            "South": {"pos": [center_x, EW_dimension + label_margin, top_z], "text": "S"},
            "East":  {"pos": [NS_dimension + label_margin, center_y, top_z], "text": "E"},
            "West":  {"pos": [0.0 - label_margin, center_y, top_z], "text": "W"},
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

    # Combined zone flags for easy downstream checks
    results["North"]["zone_E"] = bool(results["North"].get("east_zone_E", False) or results["North"].get("west_zone_E", False))
    results["South"]["zone_E"] = bool(results["South"].get("east_zone_E", False) or results["South"].get("west_zone_E", False))
    results["East"]["zone_E"]  = bool(results["East"].get("north_zone_E", False) or results["East"].get("south_zone_E", False))
    results["West"]["zone_E"]  = bool(results["West"].get("north_zone_E", False) or results["West"].get("south_zone_E", False))

    return results, fig

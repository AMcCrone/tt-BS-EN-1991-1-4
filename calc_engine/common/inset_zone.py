import plotly.graph_objects as go

def detect_zone_E_and_visualise(session_state,
                                inset_height,
                                north_offset,
                                south_offset,
                                east_offset,
                                west_offset):
    """
    Determine whether Zone E applies for each elevation edge and return a Plotly 3D
    visualisation. Fixes:
      - use clockwise vertex ordering for quads (no self-overlap)
      - show inset height in z (upper box has height = inset_height)
      - zone E rectangles are vertical: height = e1/3 from roof plane, width = e1/5
    Returns:
      - results: dict of per-direction metrics and booleans
      - fig: plotly.graph_objects.Figure
    """
    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"

    # Read base plan dims + base roof height from session_state
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))
    base_z = float(session_state.inputs.get("z", 10.0))  # roof plane z

    # Sanitize offsets and H1
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Upper-storey footprint in plan coordinates (x: 0 -> NS, y: 0 -> EW)
    upper_x0 = west_offset
    upper_x1 = max(west_offset, NS_dimension - east_offset)
    upper_y0 = north_offset
    upper_y1 = max(north_offset, EW_dimension - south_offset)

    upper_width_x = max(0.0, upper_x1 - upper_x0)
    upper_width_y = max(0.0, upper_y1 - upper_y0)

    # Results dict skeleton
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

    # Container for zone-E rectangles: each item holds (cx0,cx1,cy0,cy1,e_height, label)
    zoneE_rects = []

    # ---- compute B1 and e1 as specified ----
    # For North/South: B1 = EW - (east + west)
    B1_NS = max(0.0, EW_dimension - (east_offset + west_offset))
    e1_NS = min(B1_NS, 2.0 * H1)
    results["North"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})
    results["South"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})

    # East edge check on North elevation: east_offset < 0.2*e1 (east corner of north edge)
    if e1_NS > 0 and east_offset < 0.2 * e1_NS:
        results["North"]["east_zone_E"] = True
        rect_w = e1_NS / 5.0   # width along x (east-west)
        rect_h = e1_NS / 3.0   # vertical height
        # Anchor rectangle at east corner of upper footprint on north side:
        x1 = upper_x1
        x0 = x1 - rect_w
        y0 = upper_y0
        y1 = y0 + rect_w * (rect_h * 0 + 1)  # just use rect_h for z; keep plan depth = rect_h for clarity
        # For north/south edges we want depth into plan along +y (southwards) of rect_d = e1/3
        y1 = upper_y0 + min(upper_width_y, rect_h)  # depth into plan limited by footprint
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-east"))

    # West edge check on North elevation: west_offset < 0.2*e1
    if e1_NS > 0 and west_offset < 0.2 * e1_NS:
        results["North"]["west_zone_E"] = True
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        x0 = upper_x0
        x1 = x0 + rect_w
        y0 = upper_y0
        y1 = upper_y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-west"))

    # South elevation checks (anchor rectangles along south edge inward/upwards)
    if e1_NS > 0 and east_offset < 0.2 * e1_NS:
        results["South"]["east_zone_E"] = True
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        x1 = upper_x1
        x0 = x1 - rect_w
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-east"))

    if e1_NS > 0 and west_offset < 0.2 * e1_NS:
        results["South"]["west_zone_E"] = True
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        x0 = upper_x0
        x1 = x0 + rect_w
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-west"))

    # ---- East/West elevations: B1 = NS - (north + south) ----
    B1_EW = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_EW = min(B1_EW, 2.0 * H1)
    results["East"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})
    results["West"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})

    # East elevation north edge: north_offset < 0.2*e1
    if e1_EW > 0 and north_offset < 0.2 * e1_EW:
        results["East"]["north_zone_E"] = True
        rect_w = e1_EW / 5.0   # along x (NS)
        rect_h = e1_EW / 3.0   # vertical
        x1 = upper_x1
        x0 = x1 - min(upper_width_x, rect_w)
        y0 = upper_y0
        y1 = y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-north"))

    # East elevation south edge: south_offset < 0.2*e1
    if e1_EW > 0 and south_offset < 0.2 * e1_EW:
        results["East"]["south_zone_E"] = True
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x1 = upper_x1
        x0 = x1 - min(upper_width_x, rect_w)
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-south"))

    # West elevation north edge
    if e1_EW > 0 and north_offset < 0.2 * e1_EW:
        results["West"]["north_zone_E"] = True
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x0 = upper_x0
        x1 = x0 + min(upper_width_x, rect_w)
        y0 = upper_y0
        y1 = y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-north"))

    # West elevation south edge
    if e1_EW > 0 and south_offset < 0.2 * e1_EW:
        results["West"]["south_zone_E"] = True
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x0 = upper_x0
        x1 = x0 + min(upper_width_x, rect_w)
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-south"))

    # ---- Build 3D visual ----
    fig = go.Figure()

    # Draw top plane of base building (flat quad) with clockwise ordering:
    # vertices: (0,0), (NS,0), (NS,EW), (0,EW)
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

        # define 8 vertices in clockwise order for each face to avoid self-overlap:
        # bottom face (clockwise): (ux0,uy0),(ux1,uy0),(ux1,uy1),(ux0,uy1)
        # top face same order but z=tz
        # We'll draw 6 faces as quads (two triangles each) using separate Mesh3d traces
        # Bottom face (optional - sits on roof plane, draw slightly above to be visible)
        pad = 1e-6
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
        # Four vertical faces (west, east, north, south) - drawn with correct vertex order
        # West face (x = ux0) - vertices clockwise when viewed from outside
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux0, ux0, ux0],
            y=[uy0, uy1, uy1, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # East face (x = ux1)
        fig.add_trace(go.Mesh3d(
            x=[ux1, ux1, ux1, ux1],
            y=[uy0, uy1, uy1, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # North face (y = uy0)
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy0, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # South face (y = uy1)
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy1, uy1, uy1, uy1],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))

    # Draw each Zone E as a simple vertical rectangle (4 vertices)
    for (cx0, cx1, cy0, cy1, rect_h, label) in zoneE_rects:
        bottom_z = top_z
        top_z_rect = top_z + rect_h
        
        # Create a single vertical rectangle face
        # For a rectangular area in plan (cx0,cy0) to (cx1,cy1), we need to determine
        # which edge this Zone E is on and create the appropriate vertical face
        
        # Determine which edge this rectangle is on based on its position
        # and create the appropriate vertical face
        
        if "North" in label or "South" in label:
            # For North/South elevations, the rectangle should face outward
            if "North" in label:
                # North face - rectangle faces north (y = cy0, constant y)
                fig.add_trace(go.Mesh3d(
                    x=[cx0, cx1, cx1, cx0],
                    y=[cy0, cy0, cy0, cy0],  # constant y (north face)
                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                    i=[0, 0], j=[1, 2], k=[2, 3],
                    color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
                ))
            else:  # South
                # South face - rectangle faces south (y = cy1, constant y)
                fig.add_trace(go.Mesh3d(
                    x=[cx0, cx1, cx1, cx0],
                    y=[cy1, cy1, cy1, cy1],  # constant y (south face)
                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                    i=[0, 0], j=[1, 2], k=[2, 3],
                    color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
                ))
        
        else:  # East or West elevation
            if "East" in label:
                # East face - rectangle faces east (x = cx1, constant x)
                fig.add_trace(go.Mesh3d(
                    x=[cx1, cx1, cx1, cx1],  # constant x (east face)
                    y=[cy0, cy1, cy1, cy0],
                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                    i=[0, 0], j=[1, 2], k=[2, 3],
                    color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
                ))
            else:  # West
                # West face - rectangle faces west (x = cx0, constant x)
                fig.add_trace(go.Mesh3d(
                    x=[cx0, cx0, cx0, cx0],  # constant x (west face)
                    y=[cy0, cy1, cy1, cy0],
                    z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                    i=[0, 0], j=[1, 2], k=[2, 3],
                    color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
                ))

    # Summary annotation text
    summary_lines = []
    for direction in ["North", "South", "East", "West"]:
        info = results[direction]
        if direction in ["North", "South"]:
            msg = f"{direction}: B1={info['B1']:.3f} m, e1={info['e1']:.3f} m; EastE={info['east_zone_E']}, WestE={info['west_zone_E']}"
        else:
            msg = f"{direction}: B1={info['B1']:.3f} m, e1={info['e1']:.3f} m; NorthE={info.get('north_zone_E',False)}, SouthE={info.get('south_zone_E',False)}"
        summary_lines.append(msg)
    summary_text = "<br>".join(summary_lines)

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            zaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            aspectmode='data'
        ),
        margin=dict(l=2, r=2, t=90, b=2),
        showlegend=False,
        title=dict(text="Inset geometry check — Zone E vertical patches (orange) if present", x=0.5),
        annotations=[dict(
            x=0.5, y=0.98, xref="paper", yref="paper",
            text=summary_text, showarrow=False,
            bgcolor="rgba(255,255,255,0.9)", bordercolor="black", borderwidth=1,
            font=dict(size=10)
        )],
        scene_camera=dict(eye=dict(x=1.2, y=-1.2, z=0.9)),
        height=520
    )

    return results, fig


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

    Note: New rule — if the offset on a given side is zero, there cannot be a Zone E on that elevation.
    (e.g. north_offset == 0 disables any Zone E on the North elevation; east/west can still have Zone E
    if their offsets are > 0.)
    """
    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"
    TT_Roof = "lightgrey"

    # Read base plan dims + base roof height from session_state
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))
    base_z = float(session_state.inputs.get("z", 10.0))  # roof plane z

    # Sanitize offsets and H1 — NO forced defaults (treat None as 0.0)
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
    # New rule: only allow North elevation Zone E if north_offset > 0
    if e1_NS > 0 and east_offset < 0.2 * e1_NS and north_offset > 0:
        rect_w = e1_NS / 5.0   # width along x (east-west)
        rect_h = e1_NS / 3.0   # vertical height
        x1 = upper_x1
        x0 = x1 - rect_w
        y0 = upper_y0
        y1 = upper_y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["North"]["east_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-east"))

    # West edge check on North elevation (require north_offset > 0)
    if e1_NS > 0 and west_offset < 0.2 * e1_NS and north_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        x0 = upper_x0
        x1 = x0 + rect_w
        y0 = upper_y0
        y1 = upper_y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["North"]["west_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-west"))

    # South elevation checks (require south_offset > 0)
    if e1_NS > 0 and east_offset < 0.2 * e1_NS and south_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        x1 = upper_x1
        x0 = x1 - rect_w
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["South"]["east_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-east"))

    if e1_NS > 0 and west_offset < 0.2 * e1_NS and south_offset > 0:
        rect_w = e1_NS / 5.0
        rect_h = e1_NS / 3.0
        x0 = upper_x0
        x1 = x0 + rect_w
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["South"]["west_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "South-west"))

    # ---- East/West elevations: B1 = NS - (north + south) ----
    B1_EW = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_EW = min(B1_EW, 2.0 * H1)
    results["East"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})
    results["West"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})

    # East elevation north edge (require east_offset > 0 to allow east elevation Zone E)
    if e1_EW > 0 and north_offset < 0.2 * e1_EW and east_offset > 0:
        rect_w = e1_EW / 5.0   # along x (NS)
        rect_h = e1_EW / 3.0   # vertical
        x1 = upper_x1
        x0 = x1 - min(upper_width_x, rect_w)
        y0 = upper_y0
        y1 = y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["East"]["north_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-north"))

    # East elevation south edge (require east_offset > 0)
    if e1_EW > 0 and south_offset < 0.2 * e1_EW and east_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x1 = upper_x1
        x0 = x1 - min(upper_width_x, rect_w)
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["East"]["south_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-south"))

    # West elevation north edge (require west_offset > 0)
    if e1_EW > 0 and north_offset < 0.2 * e1_EW and west_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x0 = upper_x0
        x1 = x0 + min(upper_width_x, rect_w)
        y0 = upper_y0
        y1 = y0 + min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["West"]["north_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-north"))

    # West elevation south edge (require west_offset > 0)
    if e1_EW > 0 and south_offset < 0.2 * e1_EW and west_offset > 0:
        rect_w = e1_EW / 5.0
        rect_h = e1_EW / 3.0
        x0 = upper_x0
        x1 = x0 + min(upper_width_x, rect_w)
        y1 = upper_y1
        y0 = y1 - min(upper_width_y, rect_h)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            results["West"]["south_zone_E"] = True
            zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "West-south"))

    # ---- Build 3D visual (unchanged from previous layout) ----
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

    # Add perimeter line for base top plane
    fig.add_trace(go.Scatter3d(
        x=[0.0, NS_dimension, NS_dimension, 0.0, 0.0],
        y=[0.0, 0.0, EW_dimension, EW_dimension, 0.0],
        z=[top_z]*5,
        mode='lines',
        line=dict(color='black', width=2),
        hoverinfo='none',
        showlegend=False
    ))

    # Draw upper inset box and roof (if present) - same rendering as before but roof flush with top
    if upper_width_x > 0 and upper_width_y > 0 and H1 > 0:
        ux0, ux1, uy0, uy1 = upper_x0, upper_x1, upper_y0, upper_y1
        bz = top_z
        tz = top_z + H1
        pad = 1e-6

        # bottom, top and faces
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[bz + pad, bz + pad, bz + pad, bz + pad],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[tz, tz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux0, ux0, ux0],
            y=[uy0, uy1, uy1, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        fig.add_trace(go.Mesh3d(
            x=[ux1, ux1, ux1, ux1],
            y=[uy0, uy1, uy1, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy0, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy1, uy1, uy1, uy1],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))

        # perimeters (base & top & verticals)
        fig.add_trace(go.Scatter3d(
            x=[ux0, ux1, ux1, ux0, ux0],
            y=[uy0, uy0, uy1, uy1, uy0],
            z=[bz + pad]*5,
            mode='lines',
            line=dict(color='black', width=2),
            hoverinfo='none',
            showlegend=False
        ))
        fig.add_trace(go.Scatter3d(
            x=[ux0, ux1, ux1, ux0, ux0],
            y=[uy0, uy0, uy1, uy1, uy0],
            z=[tz]*5,
            mode='lines',
            line=dict(color='black', width=2),
            hoverinfo='none',
            showlegend=False
        ))
        vert_x = [ux0, ux1, ux1, ux0]
        vert_y = [uy0, uy0, uy1, uy1]
        for vx, vy in zip(vert_x, vert_y):
            fig.add_trace(go.Scatter3d(
                x=[vx, vx],
                y=[vy, vy],
                z=[bz + pad, tz],
                mode='lines',
                line=dict(color='black', width=2),
                hoverinfo='none',
                showlegend=False
            ))

        # flush roof
        roof_z = tz
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[roof_z, roof_z, roof_z, roof_z],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=TT_Roof, opacity=1.0, hoverinfo="none", showlegend=False
        ))
        fig.add_trace(go.Scatter3d(
            x=[ux0, ux1, ux1, ux0, ux0],
            y=[uy0, uy0, uy1, uy1, uy0],
            z=[roof_z]*5,
            mode='lines',
            line=dict(color='black', width=1),
            hoverinfo='none',
            showlegend=False
        ))

    # Draw each Zone E as a simple vertical rectangle (4 vertices)
    for (cx0, cx1, cy0, cy1, rect_h, label) in zoneE_rects:
        bottom_z = top_z
        top_z_rect = top_z + rect_h

        if "North" in label or "South" in label:
            if "North" in label:
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
                    mode='lines',
                    line=dict(color='black', width=2),
                    showlegend=False, hoverinfo='none'
                ))
            else:
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
                    mode='lines',
                    line=dict(color='black', width=2),
                    showlegend=False, hoverinfo='none'
                ))

        else:  # East or West elevation
            if "East" in label:
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
                    mode='lines',
                    line=dict(color='black', width=2),
                    showlegend=False, hoverinfo='none'
                ))
            else:
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
                    mode='lines',
                    line=dict(color='black', width=2),
                    showlegend=False, hoverinfo='none'
                ))

    # Add direction labels (N, E, S, W) in line with inset zone base.
    # label_margin kept as previously increased value
    label_margin = max(1.0, max(NS_dimension, EW_dimension) * 0.06)
    center_x = NS_dimension / 2
    center_y = EW_dimension / 2

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
        label_positions = {
            "North": {"pos": [center_x, 0.0 - label_margin, top_z], "text": "N"},
            "South": {"pos": [center_x, EW_dimension + label_margin, top_z], "text": "S"},
            "East":  {"pos": [0.0 - label_margin, center_y, top_z], "text": "E"},
            "West":  {"pos": [NS_dimension + label_margin, center_y, top_z], "text": "W"},
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

    # Layout: remove title and summary annotation; no legend
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

    return results, fig

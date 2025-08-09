import plotly.graph_objects as go

def detect_zone_E_and_visualise(session_state,
                                inset_height,
                                north_offset,
                                south_offset,
                                east_offset,
                                west_offset):
    """
    Determine whether Zone E applies and return Plotly 3D visualisation.

    Coordinate convention:
      x => Easting (0 .. EW_dimension)
      y => Northing (0 .. NS_dimension)
    This fixes east/west orientation so 'East' corresponds to larger x values
    and 'North' to smaller y values (y=0 is the north edge).
    """
    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"
    TT_Roof = "lightgrey"

    # Read base plan dims + base roof height
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))  # north-south length
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))  # east-west length
    base_z = float(session_state.inputs.get("z", 10.0))  # roof plane z

    # Sanitize offsets and H1 — treat None as 0.0 (no forced defaults)
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Upper-storey footprint in plan coordinates:
    # x: 0 -> EW_dimension (Easting), y: 0 -> NS_dimension (Northing)
    upper_x0 = west_offset
    upper_x1 = max(west_offset, EW_dimension - east_offset)
    upper_y0 = north_offset
    upper_y1 = max(north_offset, NS_dimension - south_offset)

    upper_width_x = max(0.0, upper_x1 - upper_x0)  # easting width
    upper_width_y = max(0.0, upper_y1 - upper_y0)  # northing depth

    # Results dict skeleton
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

    # ---- compute B1 and e1 ----
    # North/South elevations: B1 = EW - (east + west)
    B1_NS = max(0.0, EW_dimension - (east_offset + west_offset))
    e1_NS = min(B1_NS, 2.0 * H1)
    results["North"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})
    results["South"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})

    # East/West elevations: B1 = NS - (north + south)
    B1_EW = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_EW = min(B1_EW, 2.0 * H1)
    results["East"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})
    results["West"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})

    # ---- Zone E checks ----
    # North elevation (y = upper_y0). Require north_offset > 0 to allow North zone based on your rule.
    if e1_NS > 0 and north_offset > 0:
        # North-east (east corner) if east_offset small
        if east_offset < 0.2 * e1_NS:
            rect_w = e1_NS / 5.0   # plan width along easting (x)
            rect_h = e1_NS / 3.0
            x1 = upper_x1
            x0 = x1 - rect_w
            y0 = upper_y0
            y1 = upper_y0 + min(upper_width_y, rect_h)  # depth into plan (southwards)
            clamped = clamp_rect(x0, x1, y0, y1)
            if clamped:
                results["North"]["east_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "North-east"))

        # North-west (west corner)
        if west_offset < 0.2 * e1_NS:
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

    # South elevation (y = upper_y1). Require south_offset > 0
    if e1_NS > 0 and south_offset > 0:
        if east_offset < 0.2 * e1_NS:
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

        if west_offset < 0.2 * e1_NS:
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

    # East elevation (x = upper_x1). Require east_offset > 0
    if e1_EW > 0 and east_offset > 0:
        if north_offset < 0.2 * e1_EW:
            rect_w = e1_EW / 5.0
            rect_h = e1_EW / 3.0
            x1 = upper_x1
            x0 = x1 - min(upper_width_x, rect_w)
            y0 = upper_y0
            y1 = y0 + min(upper_width_y, rect_h)
            clamped = clamp_rect(x0, x1, y0, y1)
            if clamped:
                results["East"]["north_zone_E"] = True
                zoneE_rects.append((clamped[0], clamped[1], clamped[2], clamped[3], rect_h, "East-north"))

        if south_offset < 0.2 * e1_EW:
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

    # West elevation (x = upper_x0). Require west_offset > 0
    if e1_EW > 0 and west_offset > 0:
        if north_offset < 0.2 * e1_EW:
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

        if south_offset < 0.2 * e1_EW:
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

    # ---- Build 3D visual ----
    fig = go.Figure()
    top_z = base_z

    # Top plane: x across EW, y across NS (so east/west map to x)
    fig.add_trace(go.Mesh3d(
        x=[0.0, EW_dimension, EW_dimension, 0.0],
        y=[0.0, 0.0, NS_dimension, NS_dimension],
        z=[top_z, top_z, top_z, top_z],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=TT_TopPlane, opacity=1.0, hoverinfo="none", showlegend=False
    ))
    # Perimeter line for base top plane
    fig.add_trace(go.Scatter3d(
        x=[0.0, EW_dimension, EW_dimension, 0.0, 0.0],
        y=[0.0, 0.0, NS_dimension, NS_dimension, 0.0],
        z=[top_z]*5,
        mode='lines',
        line=dict(color='black', width=2),
        hoverinfo='none',
        showlegend=False
    ))

    # Draw inset box + perimeters + roof (if present)
    if upper_width_x > 0 and upper_width_y > 0 and H1 > 0:
        ux0, ux1, uy0, uy1 = upper_x0, upper_x1, upper_y0, upper_y1
        bz = top_z
        tz = top_z + H1
        pad = 1e-6

        # bottom face
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[bz + pad, bz + pad, bz + pad, bz + pad],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # top face
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[tz, tz, tz, tz],
            i=[0,0], j=[1,2], k=[2,3],
            color=TT_Upper, opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # vertical faces (4)
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

        # perimeters: bottom, top, vertical edges
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
        for vx, vy in zip([ux0, ux1, ux1, ux0], [uy0, uy0, uy1, uy1]):
            fig.add_trace(go.Scatter3d(
                x=[vx, vx],
                y=[vy, vy],
                z=[bz + pad, tz],
                mode='lines',
                line=dict(color='black', width=2),
                hoverinfo='none',
                showlegend=False
            ))

        # flush roof (no gap)
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

    # Draw Zone E rectangles and their perimeters
    for (cx0, cx1, cy0, cy1, rect_h, label) in zoneE_rects:
        bottom_z = top_z
        top_z_rect = top_z + rect_h

        if "North" in label or "South" in label:
            # north/south faces: y constant
            y_const = cy0 if "North" in label else cy1
            fig.add_trace(go.Mesh3d(
                x=[cx0, cx1, cx1, cx0],
                y=[y_const, y_const, y_const, y_const],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[cx0, cx1, cx1, cx0, cx0],
                y=[y_const, y_const, y_const, y_const, y_const],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines',
                line=dict(color='black', width=2),
                showlegend=False, hoverinfo='none'
            ))
        else:
            # east/west faces: x constant
            if "East" in label:
                x_const = cx1
            else:
                x_const = cx0
            fig.add_trace(go.Mesh3d(
                x=[x_const, x_const, x_const, x_const],
                y=[cy0, cy1, cy1, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[x_const, x_const, x_const, x_const, x_const],
                y=[cy0, cy1, cy1, cy0, cy0],
                z=[bottom_z, bottom_z, top_z_rect, top_z_rect, bottom_z],
                mode='lines',
                line=dict(color='black', width=2),
                showlegend=False, hoverinfo='none'
            ))

    # Direction labels aligned with inset base (or building midpoints)
    label_margin = max(1.0, max(NS_dimension, EW_dimension) * 0.06)
    center_x = EW_dimension / 2
    center_y = NS_dimension / 2

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
            "South": {"pos": [center_x, NS_dimension + label_margin, top_z], "text": "S"},
            "East":  {"pos": [EW_dimension + label_margin, center_y, top_z], "text": "E"},
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
            showlegend=False, hoverinfo='none'
        ))

    # Layout: no title, no annotation, no legend
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

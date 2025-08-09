import plotly.graph_objects as go

def detect_zone_E_and_visualise(session_state,
                                inset_height,
                                north_offset,
                                south_offset,
                                east_offset,
                                west_offset):
    """
    Determine whether Zone E applies for each elevation edge and return a Plotly 3D
    top-plane visualisation with orange rectangles marking Zone E areas.

    Inputs:
      - session_state: streamlit session (reads NS_dimension, EW_dimension, z)
      - inset_height: H1
      - north_offset, south_offset, east_offset, west_offset: offsets (m)

    Returns:
      - results: dict of per-direction metrics and booleans (e1, B1, zone_E per edge)
      - fig: plotly.graph_objects.Figure showing top-plane + upper footprint + zone E rectangles
    """
    # Colors
    TT_TopPlane = "rgb(223,224,225)"
    TT_Upper = "rgb(136,219,223)"
    TT_Orange = "rgb(211,69,29)"

    # Read base plan dims + base roof height from session_state
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))
    base_z = float(session_state.inputs.get("z", 10.0))  # top of lower storey (roof plane)

    # Ensure numeric and non-negative
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Compute upper-storey footprint in plan coordinates.
    # x runs from 0 to NS_dimension (west -> east)
    # y runs from 0 to EW_dimension (north -> south)
    upper_x0 = west_offset
    upper_x1 = max(west_offset, NS_dimension - east_offset)
    upper_y0 = north_offset
    upper_y1 = max(north_offset, EW_dimension - south_offset)

    upper_width_x = max(0.0, upper_x1 - upper_x0)  # footprint along x
    upper_width_y = max(0.0, upper_y1 - upper_y0)  # footprint along y

    # Prepare results structure
    results = {
        "North": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "South": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "East":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
        "West":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
    }

    # Helper: clamp a rectangle to the upper footprint
    def clamp_rect(x0, x1, y0, y1):
        cx0 = max(x0, upper_x0)
        cx1 = min(x1, upper_x1)
        cy0 = max(y0, upper_y0)
        cy1 = min(y1, upper_y1)
        if cx1 <= cx0 or cy1 <= cy0:
            return None  # degenerate or outside footprint
        return (cx0, cx1, cy0, cy1)

    # Collect rectangles to draw (list of dicts with coords & colour)
    zoneE_rects = []

    # ---- North & South elevations use B1 = EW - (east + west) (cross width) ----
    B1_NS = max(0.0, EW_dimension - (east_offset + west_offset))
    e1_NS = min(B1_NS, 2.0 * H1)
    results["North"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})
    results["South"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})

    # East edge check on North elevation: east_offset < 0.2*e1
    if e1_NS > 0 and east_offset < 0.2 * e1_NS:
        results["North"]["east_zone_E"] = True
        # rectangle on top-plane adjacent to north edge at the east corner:
        rect_w = e1_NS / 5.0
        rect_d = e1_NS / 3.0
        # place rectangle such that its east side aligns with upper_x1 and north side aligns with upper_y0
        x1 = upper_x1
        x0 = max(upper_x0, x1 - rect_w)
        y0 = upper_y0
        y1 = min(upper_y1, y0 + rect_d)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({"coords": clamped, "direction": "North-east"})

    # West edge check on North elevation: west_offset < 0.2*e1
    if e1_NS > 0 and west_offset < 0.2 * e1_NS:
        results["North"]["west_zone_E"] = True
        rect_w = e1_NS / 5.0
        rect_d = e1_NS / 3.0
        # west corner of upper footprint
        x0 = upper_x0
        x1 = min(upper_x1, x0 + rect_w)
        y0 = upper_y0
        y1 = min(upper_y1, y0 + rect_d)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({"coords": clamped, "direction": "North-west"})

    # South elevation: east and west edges measured from south side (upper_y1)
    if e1_NS > 0 and east_offset < 0.2 * e1_NS:
        # East edge on South elevation (same east_offset check)
        results["South"]["east_zone_E"] = True
        rect_w = e1_NS / 5.0
        rect_d = e1_NS / 3.0
        x1 = upper_x1
        x0 = max(upper_x0, x1 - rect_w)
        y1 = upper_y1
        y0 = max(upper_y0, y1 - rect_d)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({"coords": clamped, "direction": "South-east"})

    if e1_NS > 0 and west_offset < 0.2 * e1_NS:
        results["South"]["west_zone_E"] = True
        rect_w = e1_NS / 5.0
        rect_d = e1_NS / 3.0
        x0 = upper_x0
        x1 = min(upper_x1, x0 + rect_w)
        y1 = upper_y1
        y0 = max(upper_y0, y1 - rect_d)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({"coords": clamped, "direction": "South-west"})

    # ---- East & West elevations use B1 = NS - (north + south) ----
    B1_EW = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_EW = min(B1_EW, 2.0 * H1)
    results["East"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})
    results["West"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})

    # North edge on East elevation: north_offset < 0.2*e1
    if e1_EW > 0 and north_offset < 0.2 * e1_EW:
        results["East"]["north_zone_E"] = True
        rect_w = e1_EW / 5.0   # along x (NS)
        rect_d = e1_EW / 3.0   # along y (into plan)
        # For East elevation, the upwind north edge corresponds to y = upper_y0,
        # rectangle anchored at east side (x = upper_x1)
        x1 = upper_x1
        x0 = max(upper_x0, x1 - rect_w)
        y0 = upper_y0
        y1 = min(upper_y1, y0 + rect_d)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({"coords": clamped, "direction": "East-north"})

    # South edge on East elevation: south_offset < 0.2*e1
    if e1_EW > 0 and south_offset < 0.2 * e1_EW:
        results["East"]["south_zone_E"] = True
        rect_w = e1_EW / 5.0
        rect_d = e1_EW / 3.0
        x1 = upper_x1
        x0 = max(upper_x0, x1 - rect_w)
        y1 = upper_y1
        y0 = max(upper_y0, y1 - rect_d)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({"coords": clamped, "direction": "East-south"})

    # North edge on West elevation: north_offset < 0.2*e1
    if e1_EW > 0 and north_offset < 0.2 * e1_EW:
        results["West"]["north_zone_E"] = True
        rect_w = e1_EW / 5.0
        rect_d = e1_EW / 3.0
        x0 = upper_x0
        x1 = min(upper_x1, x0 + rect_w)
        y0 = upper_y0
        y1 = min(upper_y1, y0 + rect_d)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({"coords": clamped, "direction": "West-north"})

    # South edge on West elevation: south_offset < 0.2*e1
    if e1_EW > 0 and south_offset < 0.2 * e1_EW:
        results["West"]["south_zone_E"] = True
        rect_w = e1_EW / 5.0
        rect_d = e1_EW / 3.0
        x0 = upper_x0
        x1 = min(upper_x1, x0 + rect_w)
        y1 = upper_y1
        y0 = max(upper_y0, y1 - rect_d)
        clamped = clamp_rect(x0, x1, y0, y1)
        if clamped:
            zoneE_rects.append({"coords": clamped, "direction": "West-south"})

    # ---- Build top-plane visual (only top plane + upper footprint + any zoneE rectangles) ----
    fig = go.Figure()

    # Top plane of base building (single rectangle at z = base_z)
    # use Mesh3d with a tiny thickness (or draw as a single flat quad)
    top_z = base_z
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, EW_dimension, EW_dimension],
        z=[top_z, top_z, top_z, top_z],
        i=[0,0], j=[1,1], k=[2,3],
        color=TT_TopPlane, opacity=1.0, hoverinfo="none", showlegend=False
    ))

    # Draw upper footprint outline as a thin filled patch slightly above top plane for visibility
    if upper_width_x > 0 and upper_width_y > 0:
        pad_z = 0.0005 * max(NS_dimension, EW_dimension)  # tiny vertical offset
        ux0, ux1, uy0, uy1 = upper_x0, upper_x1, upper_y0, upper_y1

        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[top_z + pad_z]*4,
            i=[0,0], j=[1,1], k=[2,3],
            color=TT_Upper, opacity=0.9, hoverinfo="none", showlegend=False
        ))

    # Draw each zone E rectangle (slightly above footprint so it's visible)
    for rect in zoneE_rects:
        cx0, cx1, cy0, cy1 = rect["coords"]
        pad_z = 0.001 * max(NS_dimension, EW_dimension)
        fig.add_trace(go.Mesh3d(
            x=[cx0, cx1, cx1, cx0],
            y=[cy0, cy0, cy1, cy1],
            z=[top_z + pad_z]*4,
            i=[0,0], j=[1,1], k=[2,3],
            color=TT_Orange, opacity=0.95, hoverinfo="none", showlegend=False
        ))

    # Add a small legend-like annotation and per-direction summary
    summary_lines = []
    for direction in ["North", "South", "East", "West"]:
        info = results[direction]
        # build per-direction message depending on available keys
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
        margin=dict(l=2, r=2, t=80, b=2),
        showlegend=False,
        title=dict(text=f"Inset geometry check — Zone E rectangles (orange) if present", x=0.5),
        annotations=[dict(
            x=0.5, y=0.98, xref="paper", yref="paper",
            text=summary_text, showarrow=False,
            bgcolor="rgba(255,255,255,0.85)", bordercolor="black", borderwidth=1,
            font=dict(size=10)
        )],
        scene_camera=dict(eye=dict(x=1.2, y=-1.2, z=0.8)),
        height=480
    )

    return results, fig

import plotly.graph_objects as go

def detect_zone_E_and_visualise(session_state,
                                inset_height,
                                north_offset,
                                south_offset,
                                east_offset,
                                west_offset):
    """
    Determine whether Zone E applies for each wind direction and return a Plotly 3D
    visualisation of the base building + inset upper storey box.

    Inputs (passed directly or read from st.session_state.inputs):
      - inset_height: vertical height of the inset (H1)
      - north_offset, south_offset, east_offset, west_offset: inset offsets (distance
        from the corresponding base edge to the upper-storey edge)
    Reads from session_state.inputs:
      - NS_dimension, EW_dimension : base plan dimensions (x and y extents)
      - z : base building height (height of the lower storey) — upper box sits on top
    Returns:
      - results: dict keyed by direction with numeric values and boolean 'zone_E'
      - fig: plotly.graph_objects.Figure 3D visualisation (upper box coloured TT_Orange
             if any zone_E True)
    """
    # Colours
    TT_LightBlue = "rgb(136,219,223)"
    TT_MidBlue = "rgb(0,163,173)"
    TT_DarkBlue = "rgb(0,48,60)"
    TT_LightGrey = "rgb(223,224,225)"
    TT_Orange = "rgb(211,69,29)"

    # Read plan dims and base height
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))
    base_z = float(session_state.inputs.get("z", 10.0))  # top of lower storey

    # Ensure offsets are non-negative numbers
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # Compute upper-storey footprint coordinates (x along NS, y along EW)
    # coordinate convention:
    #   x: 0 -> NS_dimension (west -> east)
    #   y: 0 -> EW_dimension (north -> south)
    upper_x0 = west_offset
    upper_x1 = max(west_offset, NS_dimension - east_offset)  # clamp to valid range
    upper_y0 = north_offset
    upper_y1 = max(north_offset, EW_dimension - south_offset)  # clamp

    # Avoid degenerate upper box
    upper_width_x = max(0.0, upper_x1 - upper_x0)
    upper_width_y = max(0.0, upper_y1 - upper_y0)

    # Helper to compute per-direction metrics
    results = {}
    # Directions and how to pick B1 and inset distance
    # For wind from North: upwind edge is y=0 => inset_distance = upper_y0, B1 = extent in y
    # For wind from South: upwind edge is y=EW_dimension => inset_distance = EW - upper_y1, B1 = extent in y
    # For wind from West: upwind edge is x=0 => inset_distance = upper_x0, B1 = extent in x
    # For wind from East: upwind edge is x=NS_dimension => inset_distance = NS - upper_x1, B1 = extent in x

    directions = {
        "North": {
            "B1": upper_width_y,
            "inset_distance": upper_y0
        },
        "South": {
            "B1": upper_width_y,
            "inset_distance": max(0.0, EW_dimension - upper_y1)
        },
        "West": {
            "B1": upper_width_x,
            "inset_distance": upper_x0
        },
        "East": {
            "B1": upper_width_x,
            "inset_distance": max(0.0, NS_dimension - upper_x1)
        }
    }

    for direction, vals in directions.items():
        B1 = float(vals["B1"])
        inset_distance = float(vals["inset_distance"])
        # e1 per Eurocode: e1 = min(B1, 2*H1)
        e1 = min(B1, 2.0 * H1)

        # Decision: Zone E present if the upwind edge of the upper storey is flush
        # or inset less than 0.2 * e1. That is inset_distance < 0.2*e1.
        # We treat the "flush" case as inset_distance == 0 (covered by < check).
        # If B1 == 0 or H1 == 0, e1 will be 0 and we avoid division by zero: then
        # no meaningful zone E (set False) unless inset_distance == 0 and e1 == 0
        zone_E = False
        reason = ""
        threshold = 0.2 * e1
        if e1 <= 0.0:
            # degenerate: if there's no upper footprint (B1==0) or no inset height, zone E cannot be computed.
            zone_E = False
            reason = "No meaningful upper-storey geometry (B1=0 or H1=0)"
        else:
            if inset_distance < threshold:
                zone_E = True
                reason = f"inset_distance ({inset_distance:.3f} m) < 0.2*e1 ({threshold:.3f} m)"
            else:
                zone_E = False
                reason = f"inset_distance ({inset_distance:.3f} m) ≥ 0.2*e1 ({threshold:.3f} m)"

        results[direction] = {
            "B1": round(B1, 4),
            "H1": round(H1, 4),
            "e1": round(e1, 4),
            "inset_distance": round(inset_distance, 4),
            "threshold_0.2e1": round(threshold, 4),
            "zone_E": bool(zone_E),
            "reason": reason
        }

    # Determine whether any direction requires Zone E
    any_zone_E = any(info["zone_E"] for info in results.values())

    # Build 3D visualisation: base + upper inset box (upper box coloured TT_Orange if any_zone_E)
    fig = go.Figure()

    # Ground plane (slightly extended)
    ground_extension = max(NS_dimension, EW_dimension) * 0.25
    gx = [-ground_extension, NS_dimension + ground_extension, NS_dimension + ground_extension, -ground_extension]
    gy = [-ground_extension, -ground_extension, EW_dimension + ground_extension, EW_dimension + ground_extension]
    gz = [0, 0, 0, 0]
    fig.add_trace(go.Mesh3d(
        x=gx, y=gy, z=gz,
        i=[0,0], j=[1,1], k=[2,3],
        color=TT_LightGrey, opacity=0.6, hoverinfo="none", showlegend=False
    ))

    z0 = 0.0
    z1 = base_z  # base building top

    # Base building faces (use simple mesh quads like in your example)
    # Front (north, y=0)
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, 0, 0],
        z=[z0, z0, z1, z1],
        i=[0,0], j=[1,2], k=[2,3],
        color=TT_MidBlue, opacity=1.0, hoverinfo="none", showlegend=False
    ))
    # Back (south, y=EW_dimension)
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[EW_dimension, EW_dimension, EW_dimension, EW_dimension],
        z=[z0, z0, z1, z1],
        i=[0,0], j=[1,2], k=[2,3],
        color=TT_MidBlue, opacity=1.0, hoverinfo="none", showlegend=False
    ))
    # Left (west, x=0)
    fig.add_trace(go.Mesh3d(
        x=[0, 0, 0, 0],
        y=[0, EW_dimension, EW_dimension, 0],
        z=[z0, z0, z1, z1],
        i=[0,0], j=[1,2], k=[2,3],
        color=TT_LightBlue, opacity=1.0, hoverinfo="none", showlegend=False
    ))
    # Right (east, x=NS_dimension)
    fig.add_trace(go.Mesh3d(
        x=[NS_dimension, NS_dimension, NS_dimension, NS_dimension],
        y=[0, EW_dimension, EW_dimension, 0],
        z=[z0, z0, z1, z1],
        i=[0,0], j=[1,2], k=[2,3],
        color=TT_LightBlue, opacity=1.0, hoverinfo="none", showlegend=False
    ))
    # Top of base
    fig.add_trace(go.Mesh3d(
        x=[0, NS_dimension, NS_dimension, 0],
        y=[0, 0, EW_dimension, EW_dimension],
        z=[z1, z1, z1, z1],
        i=[0,0], j=[1,2], k=[2,3],
        color=TT_LightBlue, opacity=1.0, hoverinfo="none", showlegend=False
    ))

    # Draw the inset upper box only if it has positive footprint area
    if upper_width_x > 0 and upper_width_y > 0 and H1 > 0:
        ux0, ux1 = upper_x0, upper_x1
        uy0, uy1 = upper_y0, upper_y1
        uz0, uz1 = z1, z1 + H1

        upper_color = TT_Orange if any_zone_E else TT_DarkBlue

        # Six faces of box as Mesh3d quads:
        # North face (y = uy0)
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy0, uy0],
            z=[uz0, uz0, uz1, uz1],
            i=[0,0], j=[1,2], k=[2,3],
            color=upper_color, opacity=1.0, hoverinfo="none", showlegend=False
        ))
        # South face (y = uy1)
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy1, uy1, uy1, uy1],
            z=[uz0, uz0, uz1, uz1],
            i=[0,0], j=[1,2], k=[2,3],
            color=upper_color, opacity=1.0, hoverinfo="none", showlegend=False
        ))
        # West face (x = ux0)
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux0, ux0, ux0],
            y=[uy0, uy1, uy1, uy0],
            z=[uz0, uz0, uz1, uz1],
            i=[0,0], j=[1,2], k=[2,3],
            color=upper_color, opacity=1.0, hoverinfo="none", showlegend=False
        ))
        # East face (x = ux1)
        fig.add_trace(go.Mesh3d(
            x=[ux1, ux1, ux1, ux1],
            y=[uy0, uy1, uy1, uy0],
            z=[uz0, uz0, uz1, uz1],
            i=[0,0], j=[1,2], k=[2,3],
            color=upper_color, opacity=1.0, hoverinfo="none", showlegend=False
        ))
        # Top face
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[uz1, uz1, uz1, uz1],
            i=[0,0], j=[1,2], k=[2,3],
            color=upper_color, opacity=1.0, hoverinfo="none", showlegend=False
        ))
        # Bottom face (sits on base roof)
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[uz0, uz0, uz0, uz0],
            i=[0,0], j=[1,2], k=[2,3],
            color=upper_color, opacity=1.0, hoverinfo="none", showlegend=False
        ))
    else:
        # Optionally add a thin outline if there's no upper box
        pass

    # Add textual annotations (small) describing zone E check per direction
    ann_y = 1.02  # will be placed in paper coordinates
    ann_text_lines = []
    for direction in ["North", "South", "West", "East"]:
        info = results[direction]
        status = "YES" if info["zone_E"] else "no"
        ann_text_lines.append(f"{direction}: Zone E? {status}  (e1={info['e1']:.3f} m, inset={info['inset_distance']:.3f} m)")

    ann_text = "<br>".join(ann_text_lines)

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            zaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            aspectmode='data'
        ),
        margin=dict(l=2, r=2, t=60, b=2),
        showlegend=False,
        title=dict(text=f"Inset geometry check — any Zone E required? {'YES' if any_zone_E else 'No'}",
                   x=0.5),
        annotations=[dict(
            x=0.5, y=0.98, xref="paper", yref="paper",
            text=ann_text, showarrow=False,
            bgcolor="rgba(255,255,255,0.8)", bordercolor="black", borderwidth=1,
            font=dict(size=11)
        )],
        scene_camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2)),
        height=480
    )

    return results, fig

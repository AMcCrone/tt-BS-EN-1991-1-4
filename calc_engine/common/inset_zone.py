import plotly.graph_objects as go

def get_zone_boundaries(width, H1, crosswind_dim):
    """
    Return zone_boundaries and zone_names using the same logic as your
    2D elevation routine, but using e1 = min(B1, 2*H1) where crosswind_dim = B1.
    width: horizontal span of the elevation (e.g. NS_dimension for N face)
    H1: inset_height
    crosswind_dim: B1 (the cross width used to compute e1)
    """
    e = min(crosswind_dim, 2.0 * H1)  # this is e1
    zone_boundaries = []
    zone_names = []

    if e < width:
        if width < 2*e:
            if width <= 2*(e/5):
                zone_boundaries = [(0.0, width)]
                zone_names = ['A']
            else:
                zone_boundaries = [
                    (0.0, e/5.0),
                    (e/5.0, width - e/5.0),
                    (width - e/5.0, width)
                ]
                zone_names = ['A', 'B', 'A']
        else:
            if width - 2*e <= 0:
                zone_boundaries = [
                    (0.0, e/5.0),
                    (e/5.0, width - e/5.0),
                    (width - e/5.0, width)
                ]
                zone_names = ['A', 'B', 'A']
            else:
                zone_boundaries = [
                    (0.0, e/5.0),
                    (e/5.0, e),
                    (e, width - e),
                    (width - e, width - e/5.0),
                    (width - e/5.0, width)
                ]
                zone_names = ['A', 'B', 'C', 'B', 'A']
    elif e >= width and e < 5*width:
        if width <= 2*(e/5.0):
            zone_boundaries = [(0.0, width)]
            zone_names = ['A']
        else:
            zone_boundaries = [
                (0.0, e/5.0),
                (e/5.0, width - e/5.0),
                (width - e/5.0, width)
            ]
            zone_names = ['A', 'B', 'A']
    else:
        zone_boundaries = [(0.0, width)]
        zone_names = ['A']

    return zone_boundaries, zone_names, e


def add_elevation_face(fig, face,
                       ux0, ux1, uy0, uy1, bz, H1,
                       face_width, B1, zone_colors,
                       zoneE_flags):
    """
    Draw the vertical face of the upper inset box corresponding to 'face'
    onto the 3D fig. 'face' is one of 'North','South','East','West'.
    - ux0..ux1, uy0..uy1 define the upper-storey footprint in plan coords.
    - bz is roof plane z, top of lower storey; H1 is inset_height (height of upper box).
    - face_width is the horizontal width of the elevation (NS_dimension for N/S,
      EW_dimension for E/W). B1 is the cross width used to compute e1.
    - zone_colors dict maps 'A','B','C' to colours.
    - zoneE_flags is a dict containing booleans e.g. {'east_zone_E': True}
    The face is drawn with zones A/B/C (vertical panels spanning bz -> bz+H1),
    and any Zone E panels (vertical, height e1/3) are drawn on the face plane,
    above Zone A (i.e., nearer the corner).
    """
    # Determine local coordinates for face plane (vertical plane of the upper box)
    # For each face we will parameterise a local horizontal axis 's' that maps into plan x/y:
    # - North/South faces: 's' runs along x from 0..face_width (west->east)
    # - East/West faces: 's' runs along y from 0..face_width (north->south)
    # We will compute zone boundaries in s-space, then convert to (x,y) positions,
    # and finally draw vertical quads from z=bz to z=bz+H1.

    zone_boundaries, zone_names, e1 = get_zone_boundaries(face_width, H1, B1)

    # helper to convert s interval to (x0,x1,y0,y1) within the upper footprint and clamp
    def s_interval_to_plan_rect(s0, s1):
        # s corresponds to full building coordinate (0..face_width) where 0 is west or north
        # We map it to plan coordinates and then clamp to upper footprint (ux0..ux1, uy0..uy1)
        if face in ("North", "South"):
            # s => x coordinate (0..NS_dimension)
            x0 = s0
            x1 = s1
            y0 = uy0  # face plane at y=uy0 (North) or y=uy1 (South) later handled by anchor
            y1 = uy1
        else:
            # face East/West: s => y coordinate (0..EW_dimension)
            x0 = ux0
            x1 = ux1
            y0 = s0
            y1 = s1

        # clamp to upper footprint
        cx0 = max(ux0, x0)
        cx1 = min(ux1, x1)
        cy0 = max(uy0, y0)
        cy1 = min(uy1, y1)
        if cx1 <= cx0 or cy1 <= cy0:
            return None
        return (cx0, cx1, cy0, cy1)

    # Draw each A/B/C strip as vertical quad (bz->bz+H1). Use clockwise ordering for each face quad.
    for (s0, s1), zname in zip(zone_boundaries, zone_names):
        rect = s_interval_to_plan_rect(s0, s1)
        if rect is None:
            continue
        cx0, cx1, cy0, cy1 = rect
        top_z = bz + H1
        # Draw quad: choose vertex order clockwise looking from outside (consistent ordering)
        # We'll use the four corners: (cx0,cy0),(cx1,cy0),(cx1,cy1),(cx0,cy1)
        fig.add_trace(go.Mesh3d(
            x=[cx0, cx1, cx1, cx0],
            y=[cy0, cy0, cy1, cy1],
            z=[bz, bz, top_z, top_z],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=zone_colors[zname],
            opacity=0.9,
            hoverinfo="none",
            showlegend=False
        ))

    # If Zone E flags indicate a Zone E on this face, draw the vertical Zone E patch
    # Each Zone E is anchored at the corner of the upper footprint corresponding to the edge.
    # Compute e1 again (get_zone_boundaries returned e1)
    # Width along face in plan = e1/5, vertical height = e1/3
    rect_h = e1 / 3.0
    rect_w = e1 / 5.0

    # Helper to add zone E patch anchored at a corner (corner args: 'east'/'west' for N/S and 'north'/'south' for E/W)
    def add_zoneE_patch(anchor):
        # anchor chooses which corner on the face:
        # for North: 'east'->east corner (ux1, uy0), 'west'->(ux0,uy0)
        # for South: 'east'->(ux1, uy1), 'west'->(ux0,uy1)
        # for East: 'north'->(ux1,uy0), 'south'->(ux1,uy1)
        # for West: 'north'->(ux0,uy0), 'south'->(ux0,uy1)
        if face == "North":
            z0 = bz
            z1 = bz + rect_h
            if anchor == "east":
                x1 = ux1
                x0 = ux1 - rect_w
                y0 = uy0
                y1 = uy0 + min(rect_w * 10.0, rect_h)  # depth into plan limited by footprint; but we'll use rect_h as depth
                # Depth should be rect_h along +y, but clamp
                y1 = min(uy1, uy0 + rect_h)
            else:  # west
                x0 = ux0
                x1 = ux0 + rect_w
                y0 = uy0
                y1 = min(uy1, uy0 + rect_h)
        elif face == "South":
            z0 = bz
            z1 = bz + rect_h
            if anchor == "east":
                x1 = ux1
                x0 = ux1 - rect_w
                y1 = uy1
                y0 = max(uy0, uy1 - rect_h)
            else:  # west
                x0 = ux0
                x1 = ux0 + rect_w
                y1 = uy1
                y0 = max(uy0, uy1 - rect_h)
        elif face == "East":
            z0 = bz
            z1 = bz + rect_h
            if anchor == "north":
                y0 = uy0
                y1 = uy0 + rect_w
                x1 = ux1
                x0 = max(ux0, ux1 - rect_h)
                # clamp x0
                x0 = max(ux0, ux1 - rect_h)
            else:  # south
                y1 = uy1
                y0 = max(uy0, uy1 - rect_w)
                x1 = ux1
                x0 = max(ux0, ux1 - rect_h)
        elif face == "West":
            z0 = bz
            z1 = bz + rect_h
            if anchor == "north":
                y0 = uy0
                y1 = uy0 + rect_w
                x0 = ux0
                x1 = min(ux1, ux0 + rect_h)
            else:  # south
                y1 = uy1
                y0 = max(uy0, uy1 - rect_w)
                x0 = ux0
                x1 = min(ux1, ux0 + rect_h)
        else:
            return

        # clamp to upper footprint
        if x1 <= x0 or y1 <= y0:
            return
        # draw vertical quad in face plane between z0..z1
        fig.add_trace(go.Mesh3d(
            x=[x0, x1, x1, x0],
            y=[y0, y0, y1, y1],
            z=[z0, z0, z1, z1],
            i=[0,0], j=[1,2], k=[2,3],
            color="rgb(211,69,29)",  # TT_Orange
            opacity=0.95,
            hoverinfo="none",
            showlegend=False
        ))

    # Decide which anchors to draw using zoneE_flags
    if face == "North":
        if zoneE_flags.get("east_zone_E", False):
            add_zoneE_patch("east")
        if zoneE_flags.get("west_zone_E", False):
            add_zoneE_patch("west")
    elif face == "South":
        if zoneE_flags.get("east_zone_E", False):
            add_zoneE_patch("east")
        if zoneE_flags.get("west_zone_E", False):
            add_zoneE_patch("west")
    elif face == "East":
        if zoneE_flags.get("north_zone_E", False):
            add_zoneE_patch("north")
        if zoneE_flags.get("south_zone_E", False):
            add_zoneE_patch("south")
    elif face == "West":
        if zoneE_flags.get("north_zone_E", False):
            add_zoneE_patch("north")
        if zoneE_flags.get("south_zone_E", False):
            add_zoneE_patch("south")

    # Optionally return e1 (for debug) if needed
    return e1


def detect_zone_E_and_visualise(session_state,
                                inset_height,
                                north_offset,
                                south_offset,
                                east_offset,
                                west_offset):
    """
    Top-level function.
    - computes B1 and e1 per axis using the rules you specified
    - determines zone E presence for each relevant edge
    - draws the top plane, the upper inset box (with height inset_height),
      the elevation faces with A/B/C zones using e1 & B1, and vertical Zone E patches
      on the same plane as the elevation faces (height e1/3, width e1/5).
    Returns: results dict and Plotly Figure.
    """
    # Colours
    TT_TopPlane = "rgb(223,224,225)"
    zone_colors = {'A': 'rgb(0,48,60)', 'B': 'rgb(0,163,173)', 'C': 'rgb(136,219,223)'}
    TT_Orange = "rgb(211,69,29)"

    # Read base plan dims + base roof height from session_state
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))
    base_z = float(session_state.inputs.get("z", 10.0))  # top of lower storey (roof plane)

    # sanitize inputs
    north_offset = max(0.0, float(north_offset or 0.0))
    south_offset = max(0.0, float(south_offset or 0.0))
    east_offset  = max(0.0, float(east_offset  or 0.0))
    west_offset  = max(0.0, float(west_offset  or 0.0))
    H1 = max(0.0, float(inset_height or 0.0))

    # compute upper footprint (plan coords)
    ux0 = west_offset
    ux1 = max(west_offset, NS_dimension - east_offset)
    uy0 = north_offset
    uy1 = max(north_offset, EW_dimension - south_offset)

    ux_width = max(0.0, ux1 - ux0)
    uy_width = max(0.0, uy1 - uy0)

    # Prepare results
    results = {
        "North": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "South": {"B1": None, "H1": H1, "e1": None, "east_zone_E": False, "west_zone_E": False},
        "East":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
        "West":  {"B1": None, "H1": H1, "e1": None, "north_zone_E": False, "south_zone_E": False},
    }

    # B1 and e1 for North/South (cross width = EW - (east+west))
    B1_NS = max(0.0, EW_dimension - (east_offset + west_offset))
    e1_NS = min(B1_NS, 2.0 * H1)
    results["North"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})
    results["South"].update({"B1": round(B1_NS, 4), "e1": round(e1_NS, 4)})

    # For North: east edge check (east_offset < 0.2*e1), west edge similarly
    if e1_NS > 0:
        if east_offset < 0.2 * e1_NS and ux_width > 0:
            results["North"]["east_zone_E"] = True
            results["South"]["east_zone_E"] = True
        if west_offset < 0.2 * e1_NS and ux_width > 0:
            results["North"]["west_zone_E"] = True
            results["South"]["west_zone_E"] = True

    # B1 and e1 for East/West (cross width = NS - (north+south))
    B1_EW = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_EW = min(B1_EW, 2.0 * H1)
    results["East"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})
    results["West"].update({"B1": round(B1_EW, 4), "e1": round(e1_EW, 4)})

    if e1_EW > 0:
        if north_offset < 0.2 * e1_EW and uy_width > 0:
            results["East"]["north_zone_E"] = True
            results["West"]["north_zone_E"] = True
        if south_offset < 0.2 * e1_EW and uy_width > 0:
            results["East"]["south_zone_E"] = True
            results["West"]["south_zone_E"] = True

    # Build 3D figure
    fig = go.Figure()

    # Draw top plane of base building (clockwise order so it doesn't overlap)
    top_z = base_z
    fig.add_trace(go.Mesh3d(
        x=[0.0, NS_dimension, NS_dimension, 0.0],
        y=[0.0, 0.0, EW_dimension, EW_dimension],
        z=[top_z, top_z, top_z, top_z],
        i=[0,0], j=[1,1], k=[2,3],
        color=TT_TopPlane, opacity=1.0, hoverinfo="none", showlegend=False
    ))

    # Draw upper inset box (proper 3D) if footprint and H1 positive
    if ux_width > 0 and uy_width > 0 and H1 > 0:
        bz = top_z
        tz = top_z + H1
        # bottom face (slightly above top plane to avoid z-fight)
        pad = 1e-6
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[bz+pad, bz+pad, bz+pad, bz+pad],
            i=[0,0], j=[1,1], k=[2,3],
            color="rgb(200,200,200)", opacity=0.02, hoverinfo="none", showlegend=False
        ))
        # top face
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy1, uy1],
            z=[tz, tz, tz, tz],
            i=[0,0], j=[1,1], k=[2,3],
            color="rgb(220,240,240)", opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # four vertical faces for visual context (clockwise)
        # West face x=ux0
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux0, ux0, ux0],
            y=[uy0, uy1, uy1, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,1], k=[2,3],
            color="rgb(220,240,240)", opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # East face x=ux1
        fig.add_trace(go.Mesh3d(
            x=[ux1, ux1, ux1, ux1],
            y=[uy0, uy1, uy1, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,1], k=[2,3],
            color="rgb(220,240,240)", opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # North face y=uy0
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy0, uy0, uy0, uy0],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,1], k=[2,3],
            color="rgb(220,240,240)", opacity=0.95, hoverinfo="none", showlegend=False
        ))
        # South face y=uy1
        fig.add_trace(go.Mesh3d(
            x=[ux0, ux1, ux1, ux0],
            y=[uy1, uy1, uy1, uy1],
            z=[bz, bz, tz, tz],
            i=[0,0], j=[1,1], k=[2,3],
            color="rgb(220,240,240)", opacity=0.95, hoverinfo="none", showlegend=False
        ))

        # Now add elevation faces with zones using e1 as described
        # NORTH face: face_width = NS_dimension, B1 = B1_NS
        add_elevation_face(fig, "North",
                           ux0, ux1, uy0, uy1, bz, H1,
                           face_width=NS_dimension, B1=B1_NS,
                           zone_colors=zone_colors,
                           zoneE_flags=results["North"])

        # SOUTH face
        add_elevation_face(fig, "South",
                           ux0, ux1, uy0, uy1, bz, H1,
                           face_width=NS_dimension, B1=B1_NS,
                           zone_colors=zone_colors,
                           zoneE_flags=results["South"])

        # EAST face (face_width = EW_dimension)
        add_elevation_face(fig, "East",
                           ux0, ux1, uy0, uy1, bz, H1,
                           face_width=EW_dimension, B1=B1_EW,
                           zone_colors=zone_colors,
                           zoneE_flags=results["East"])

        # WEST face
        add_elevation_face(fig, "West",
                           ux0, ux1, uy0, uy1, bz, H1,
                           face_width=EW_dimension, B1=B1_EW,
                           zone_colors=zone_colors,
                           zoneE_flags=results["West"])

    # Add cardinal labels and simple dimension arrows (2D paper annotations)
    cardinals = ["N", "E", "S", "W"]
    # Place them in paper coordinates around the plot for clarity
    cardinal_annotations = [
        dict(x=0.5, y=1.02, xref="paper", yref="paper", text="N", showarrow=False, font=dict(size=12)),
        dict(x=1.02, y=0.5, xref="paper", yref="paper", text="E", showarrow=False, font=dict(size=12)),
        dict(x=0.5, y=-0.02, xref="paper", yref="paper", text="S", showarrow=False, font=dict(size=12)),
        dict(x=-0.02, y=0.5, xref="paper", yref="paper", text="W", showarrow=False, font=dict(size=12))
    ]

    # dimension text for plan dims
    dim_text = f"NS = {NS_dimension:.2f} m    EW = {EW_dimension:.2f} m    H1 = {H1:.2f} m"
    # top annotation summarising results
    summary_lines = []
    for d in ["North", "South", "East", "West"]:
        info = results[d]
        if d in ("North","South"):
            summary_lines.append(f"{d}: e1={info['e1']:.3f} m (B1={info['B1']:.3f} m) E?{info['east_zone_E']} W?{info['west_zone_E']}")
        else:
            summary_lines.append(f"{d}: e1={info['e1']:.3f} m (B1={info['B1']:.3f} m) N?{info.get('north_zone_E',False)} S?{info.get('south_zone_E',False)}")
    summary_text = "<br>".join(summary_lines)

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            zaxis=dict(visible=False, showgrid=False, showticklabels=False, zeroline=False),
            aspectmode='data'
        ),
        margin=dict(l=2, r=2, t=120, b=2),
        showlegend=False,
        title=dict(text="Inset geometry check — elevation zones (A/B/C) and Zone E patches", x=0.5),
        annotations=[dict(x=0.5, y=1.03, xref="paper", yref="paper",
                          text=dim_text + "<br>" + summary_text,
                          showarrow=False, bgcolor="rgba(255,255,255,0.9)",
                          bordercolor="black", borderwidth=1, font=dict(size=11))] + cardinal_annotations,
        scene_camera=dict(eye=dict(x=1.2, y=-1.2, z=1.0)),
        height=620
    )

    return results, fig

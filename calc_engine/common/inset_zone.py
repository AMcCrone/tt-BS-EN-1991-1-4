import plotly.graph_objects as go

import plotly.graph_objects as go

def _compute_zone_boundaries_using_e1(width, e1):
    """
    Return zone_boundaries (list of (s0,s1)) and zone_names like your 2D elevation logic,
    but using e1 (instead of e) and width (d).
    """
    zone_boundaries = []
    zone_names = []

    if e1 < width:
        if width < 2*e1:
            if width <= 2*(e1/5.0):
                zone_boundaries = [(0.0, width)]
                zone_names = ['A']
            else:
                zone_boundaries = [
                    (0.0, e1/5.0),
                    (e1/5.0, width - e1/5.0),
                    (width - e1/5.0, width)
                ]
                zone_names = ['A', 'B', 'A']
        else:
            if width - 2*e1 <= 0:
                zone_boundaries = [
                    (0.0, e1/5.0),
                    (e1/5.0, width - e1/5.0),
                    (width - e1/5.0, width)
                ]
                zone_names = ['A', 'B', 'A']
            else:
                zone_boundaries = [
                    (0.0, e1/5.0),
                    (e1/5.0, e1),
                    (e1, width - e1),
                    (width - e1, width - e1/5.0),
                    (width - e1/5.0, width)
                ]
                zone_names = ['A', 'B', 'C', 'B', 'A']
    elif e1 >= width and e1 < 5*width:
        if width <= 2*(e1/5.0):
            zone_boundaries = [(0.0, width)]
            zone_names = ['A']
        else:
            zone_boundaries = [
                (0.0, e1/5.0),
                (e1/5.0, width - e1/5.0),
                (width - e1/5.0, width)
            ]
            zone_names = ['A', 'B', 'A']
    else:
        zone_boundaries = [(0.0, width)]
        zone_names = ['A']

    return zone_boundaries, zone_names


def _add_quad_mesh(fig, xs, ys, zs, color, hovertext=None, border=True):
    """
    Add a quad face (as two triangles) with consistent vertex ordering (clockwise),
    then add an outline (Scatter3d) around it for a crisp border.
    xs,ys,zs are lists of 4 coords in clockwise order.
    """
    # Ensure lists are floats
    xs = [float(v) for v in xs]
    ys = [float(v) for v in ys]
    zs = [float(v) for v in zs]

    fig.add_trace(go.Mesh3d(
        x=xs, y=ys, z=zs,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=color, opacity=1.0, showlegend=False,
        hovertext=hovertext, hoverinfo='text'
    ))
    if border:
        fig.add_trace(go.Scatter3d(
            x=[xs[0], xs[1], xs[2], xs[3], xs[0]],
            y=[ys[0], ys[1], ys[2], ys[3], ys[0]],
            z=[zs[0], zs[1], zs[2], zs[3], zs[0]],
            mode='lines',
            line=dict(color='black', width=2),
            showlegend=False,
            hoverinfo='none'
        ))


def create_3d_inset_visualization(session_state, results_by_direction=None):
    """
    Create a 3D visualization of the inset/upper-storey and elevation zones (A/B/C),
    plus Zone E patches when the geometric condition is met.

    - Reads NS_dimension, EW_dimension, z, inset_height and inset offsets from session_state.inputs.
    - Uses e1 = min(B1, 2*H1) and B1 as per your rules:
        * North/South faces: B1 = EW - (east + west)
        * East/West faces:  B1 = NS - (north + south)
    - A/B/C are drawn on the vertical face of the upper box (height = H1).
    - Zone E patches are vertical patches on the same plane as the face:
        height = e1/3 (from roof plane up), width along face = e1/5, orange.
    - Returns plotly Figure.
    """
    # Colours (same as in your elevation plots)
    zone_colors = {'A': 'rgb(0,48,60)', 'B': 'rgb(0,163,173)', 'C': 'rgb(136,219,223)'}
    TT_Orange = 'rgb(211,69,29)'
    TOPPLANE = 'rgb(240,240,240)'

    # Read inputs
    NS_dimension = float(session_state.inputs.get("NS_dimension", 20.0))
    EW_dimension = float(session_state.inputs.get("EW_dimension", 40.0))
    z = float(session_state.inputs.get("z", 10.0))  # roof plane height

    H1 = max(0.0, float(session_state.inputs.get("inset_height", 0.0)))
    north_offset = max(0.0, float(session_state.inputs.get("north_offset", 0.0)))
    south_offset = max(0.0, float(session_state.inputs.get("south_offset", 0.0)))
    east_offset  = max(0.0, float(session_state.inputs.get("east_offset", 0.0)))
    west_offset  = max(0.0, float(session_state.inputs.get("west_offset", 0.0)))

    # Upper-storey footprint (plan coords)
    ux0 = west_offset
    ux1 = max(west_offset, NS_dimension - east_offset)
    uy0 = north_offset
    uy1 = max(north_offset, EW_dimension - south_offset)

    ux_width = max(0.0, ux1 - ux0)
    uy_width = max(0.0, uy1 - uy0)

    # Compute B1 and e1 for both axis
    B1_NS = max(0.0, EW_dimension - (east_offset + west_offset))
    e1_NS = min(B1_NS, 2.0 * H1)

    B1_EW = max(0.0, NS_dimension - (north_offset + south_offset))
    e1_EW = min(B1_EW, 2.0 * H1)

    # Prepare figure
    fig = go.Figure()

    # Roof top plane (single quad, clockwise vertices)
    top_z = z
    _add_quad_mesh(
        fig,
        xs=[0.0, NS_dimension, NS_dimension, 0.0],
        ys=[0.0, 0.0, EW_dimension, EW_dimension],
        zs=[top_z, top_z, top_z, top_z],
        color=TOPPLANE,
        hovertext="Roof plane",
        border=True
    )

    # Draw the upper inset box (if it exists)
    if ux_width > 0 and uy_width > 0 and H1 > 0:
        bz = top_z
        tz = top_z + H1

        # Top face (clockwise)
        _add_quad_mesh(
            fig,
            xs=[ux0, ux1, ux1, ux0],
            ys=[uy0, uy0, uy1, uy1],
            zs=[tz, tz, tz, tz],
            color='rgb(220,240,240)',
            hovertext=f"Upper storey (H1={H1:.2f} m)",
            border=True
        )

        # Four vertical faces for the upper box (draw lightly to give volume)
        # West face (x = ux0) - clockwise when viewed from outside
        _add_quad_mesh(
            fig,
            xs=[ux0, ux0, ux0, ux0],
            ys=[uy0, uy1, uy1, uy0],
            zs=[bz, bz, tz, tz],
            color='rgb(220,240,240)',
            hovertext="Inset face (west)",
            border=True
        )
        # East face (x = ux1)
        _add_quad_mesh(
            fig,
            xs=[ux1, ux1, ux1, ux1],
            ys=[uy0, uy1, uy1, uy0],
            zs=[bz, bz, tz, tz],
            color='rgb(220,240,240)',
            hovertext="Inset face (east)",
            border=True
        )
        # North face (y = uy0)
        _add_quad_mesh(
            fig,
            xs=[ux0, ux1, ux1, ux0],
            ys=[uy0, uy0, uy0, uy0],
            zs=[bz, bz, tz, tz],
            color='rgb(220,240,240)',
            hovertext="Inset face (north)",
            border=True
        )
        # South face (y = uy1)
        _add_quad_mesh(
            fig,
            xs=[ux0, ux1, ux1, ux0],
            ys=[uy1, uy1, uy1, uy1],
            zs=[bz, bz, tz, tz],
            color='rgb(220,240,240)',
            hovertext="Inset face (south)",
            border=True
        )

        # Helper: map s-interval (0..face_width) to plan rectangle on the upper footprint for a face
        def s_interval_to_plan_rect(face, s0, s1):
            """
            face: 'North','South','East','West'
            s0,s1: interval in [0, face_width] where face_width is NS_dimension (for N/S) or EW_dimension (for E/W)
            returns (cx0,cx1,cy0,cy1) clipped to upper footprint, or None if no overlap
            """
            if face in ("North", "South"):
                # s => x in [0..NS_dimension]
                x0 = s0
                x1 = s1
                y0 = uy0 if face == "North" else uy1
                y1 = y0  # face plane; but for a quad we need a depth - will use yz interval = small depth = intersection with footprint
                # For vertical face panels we want full vertical strip clipped to footprint in x
                cx0 = max(ux0, x0)
                cx1 = min(ux1, x1)
                # depth into plan along y should be at least a tiny thickness inside the upper footprint.
                # We'll make cy0..cy1 such that the quad has finite area: for north use y0 -> y0 + small_depth_clamped
                if face == "North":
                    cy0 = uy0
                    cy1 = min(uy1, uy0 + max(0.0001, min(H1, (ux1-ux0))))  # small depth (preferably rect_h later)
                else:  # South
                    cy1 = uy1
                    cy0 = max(uy0, uy1 - max(0.0001, min(H1, (ux1-ux0))))
            else:
                # face East/West: s maps to y in [0..EW_dimension]
                y0 = s0
                y1 = s1
                x0 = ux0 if face == "West" else ux1  # for East/West faces mapping we'll clamp differently below
                # For East/West we want full vertical strip clipped to footprint in y
                cy0 = max(uy0, y0)
                cy1 = min(uy1, y1)
                if face == "East":
                    cx1 = ux1
                    cx0 = max(ux0, ux1 - max(0.0001, min(H1, (uy1-uy0))))
                else:  # West
                    cx0 = ux0
                    cx1 = min(ux1, ux0 + max(0.0001, min(H1, (uy1-uy0))))

            # Final clamp for x
            # If we didn't compute cx0/cx1 yet in East/West branch, ensure values exist
            try:
                cx0, cx1, cy0, cy1
            except NameError:
                # compute safely
                cx0 = max(ux0, x0)
                cx1 = min(ux1, x1)
                cy0 = max(uy0, y0)
                cy1 = min(uy1, y1)

            if cx1 <= cx0 or cy1 <= cy0:
                return None
            return (cx0, cx1, cy0, cy1)

        # Helper to draw zone strips for a face
        def draw_face_zones(face, face_width, B1, e1):
            # get zone boundaries using e1
            zones, znames = _compute_zone_boundaries_using_e1(face_width, e1)
            for (s0, s1), zname in zip(zones, znames):
                # map to plan rect within upper footprint
                rect = s_interval_to_plan_rect(face, s0, s1)
                if rect is None:
                    continue
                cx0, cx1, cy0, cy1 = rect
                # Create clockwise vertex ordering for the face plane quad (vertical from bz->tz)
                xs = [cx0, cx1, cx1, cx0]
                ys = [cy0, cy0, cy1, cy1]
                zs = [bz, bz, tz, tz]
                # hover text with dimensions & zone label
                width_s = s1 - s0
                hover = f"Zone {zname}<br>zone_width={width_s:.2f} m<br>H1={H1:.2f} m<br>B1={B1:.2f} m<br>e1={e1:.2f} m"
                _add_quad_mesh(fig, xs, ys, zs, color=zone_colors[zname], hovertext=hover)

        # Draw N/S face zones (face_width = NS_dimension, but use B1_NS/e1_NS)
        draw_face_zones("North", NS_dimension, B1_NS, e1_NS)
        draw_face_zones("South", NS_dimension, B1_NS, e1_NS)

        # Draw E/W face zones (face_width = EW_dimension, use B1_EW/e1_EW)
        draw_face_zones("East", EW_dimension, B1_EW, e1_EW)
        draw_face_zones("West", EW_dimension, B1_EW, e1_EW)

        # Now draw Zone E patches (vertical patches in the face plane) where they apply
        # Anchoring logic (per your spec):
        # North/South: test east_offset and west_offset against 0.2*e1_NS
        # East/West:  test north_offset and south_offset against 0.2*e1_EW

        def add_zoneE_for(face, anchor):
            """
            anchor:
              - for North/South: 'east' or 'west'
              - for East/West: 'north' or 'south'
            Draw a vertical patch anchored at the appropriate corner.
            """
            if face in ("North", "South"):
                e1 = e1_NS
                B1 = B1_NS
            else:
                e1 = e1_EW
                B1 = B1_EW

            if e1 <= 0:
                return

            rect_h = e1 / 3.0   # vertical height
            rect_w = e1 / 5.0   # width along face horizontal axis

            bz_local = bz
            tz_local = bz + rect_h

            if face == "North":
                if anchor == "east":
                    x1 = ux1
                    x0 = max(ux0, ux1 - rect_w)
                    y0 = uy0
                    y1 = min(uy1, uy0 + rect_w * 10.0)  # ensure some depth; we'll clamp to footprint
                    # depth should be rect_h into plan
                    y1 = min(uy1, uy0 + rect_h)
                else:  # west
                    x0 = ux0
                    x1 = min(ux1, ux0 + rect_w)
                    y0 = uy0
                    y1 = min(uy1, uy0 + rect_h)
            elif face == "South":
                if anchor == "east":
                    x1 = ux1
                    x0 = max(ux0, ux1 - rect_w)
                    y1 = uy1
                    y0 = max(uy0, uy1 - rect_h)
                else:
                    x0 = ux0
                    x1 = min(ux1, ux0 + rect_w)
                    y1 = uy1
                    y0 = max(uy0, uy1 - rect_h)
            elif face == "East":
                if anchor == "north":
                    y0 = uy0
                    y1 = min(uy1, uy0 + rect_w)
                    x1 = ux1
                    x0 = max(ux0, ux1 - rect_h)
                else:  # south
                    y1 = uy1
                    y0 = max(uy0, uy1 - rect_w)
                    x1 = ux1
                    x0 = max(ux0, ux1 - rect_h)
            elif face == "West":
                if anchor == "north":
                    y0 = uy0
                    y1 = min(uy1, uy0 + rect_w)
                    x0 = ux0
                    x1 = min(ux1, ux0 + rect_h)
                else:  # south
                    y1 = uy1
                    y0 = max(uy0, uy1 - rect_w)
                    x0 = ux0
                    x1 = min(ux1, ux0 + rect_h)
            else:
                return

            # clamp
            if x1 <= x0 or y1 <= y0:
                return

            # Draw vertical quad in face plane from bz_local -> tz_local
            xs = [x0, x1, x1, x0]
            ys = [y0, y0, y1, y1]
            zs = [bz_local, bz_local, tz_local, tz_local]
            hover = f"Zone E<br>width={x1-x0:.2f} m / {y1-y0:.2f} m<br>height={rect_h:.2f} m<br>e1={e1:.2f} m"
            _add_quad_mesh(fig, xs, ys, zs, color=TT_Orange, hovertext=hover)

        # Check conditions and add patches
        # North/South checks (east_offset, west_offset vs 0.2*e1_NS)
        if e1_NS > 0 and ux_width > 0:
            if east_offset < 0.2 * e1_NS:
                add_zoneE_for("North", "east")
                add_zoneE_for("South", "east")
            if west_offset < 0.2 * e1_NS:
                add_zoneE_for("North", "west")
                add_zoneE_for("South", "west")

        # East/West checks (north_offset, south_offset vs 0.2*e1_EW)
        if e1_EW > 0 and uy_width > 0:
            if north_offset < 0.2 * e1_EW:
                add_zoneE_for("East", "north")
                add_zoneE_for("West", "north")
            if south_offset < 0.2 * e1_EW:
                add_zoneE_for("East", "south")
                add_zoneE_for("West", "south")

    # Add cardinal labels in paper coords (2D annotations)
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False),
            zaxis=dict(visible=False, showgrid=False, zeroline=False),
            aspectmode='data'
        ),
        margin=dict(l=2, r=2, t=80, b=2),
        showlegend=False,
        title=f"Inset geometry — upper storey & elevation zones (Zone E orange)",
        scene_camera=dict(eye=dict(x=1.2, y=-1.2, z=1.0)),
        height=600
    )

    # Add textual overlay summarising dims (paper coords)
    dim_text = f"NS={NS_dimension:.2f} m · EW={EW_dimension:.2f} m · H1={H1:.2f} m · B1_NS={B1_NS:.2f} m · e1_NS={e1_NS:.2f} m · B1_EW={B1_EW:.2f} m · e1_EW={e1_EW:.2f} m"
    fig.update_layout(annotations=[dict(
        x=0.5, y=0.98, xref='paper', yref='paper',
        text=dim_text, showarrow=False,
        bgcolor="rgba(255,255,255,0.9)", bordercolor="black", borderwidth=1, font=dict(size=10)
    )])

    return fig

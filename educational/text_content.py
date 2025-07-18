region_help = """

By selecting **United Kindom**, this app follows the methodology set out in BS EN 1991-1-4 and the UK National Annex.

Otherwise, by selecting **Other European Country**, this app follow the methodology set out in only BS EN 1991-1-4.

"""

terrain_help = """

**Terrain Categories (UK)**

The classification of roughness categories has been simplified into three terrain categories:

- **Terrain Category 0**: Referred to as **Sea** — open sea, lakes, and coastal areas exposed to open sea.
- **Terrain Categories I and II**: Grouped together as **Country terrain** — flat, open country with minimal obstacles.
- **Terrain Categories III and IV**: Grouped together as **Town terrain** — towns or cities with closely spaced obstacles.

**Note:** All inland lakes extending more than 1 km in the direction of wind and closer than 1 km upwind of the site should also be treated as **Sea**.

---

**Terrain Categories (EU)**

When calculating wind pressure parameters (qₚ and cₛc_d), transitions between terrain roughness categories must be considered. Two recommended procedures are:

**Procedure 1**
Use the **smoother terrain category in the upwind direction** if the structure is located:

- Less than 2 km from the smoother **Category 0**, or  
- Less than 1 km from smoother **Categories I to III**.

> Small areas (less than 10% of the area under consideration) with different roughness may be ignored.

**Procedure 2**
1. Determine the roughness categories for the upstream terrain in angular sectors.
2. For each sector, find the distance *x* from the building to where the terrain roughness changes.
3. If *x* is **smaller** than values from Table A.1 (based on height), use the **lower** roughness value.  
   If *x* is **larger**, use the **higher** roughness value.

> Again, small areas (<10%) with deviating roughness may be ignored.

If no distance *x* is specified (or height exceeds 50 m), default to using the **smaller** roughness length.

Linear interpolation may be used for intermediate heights.

> A building can be calculated in a lower terrain category if it lies within the limits defined in Table A.1.
"""

basic_wind_help = """

Values for $V_{b,map}$ can be obtained from the National Annex.

For projects in the UK, $V_{b,map}$ may be read from **Figure NA.1** (shown right). Typically, for projects in London, $V_{b,map}$ = 21.5 m/s
"""

velocity_profile_help = """

The reference heights, $ z_e $, for windward walls of rectangular plan buildings (zone D, see Figure 7.5) depend on the aspect ratio $ h/b $ and are always the upper heights of the different parts of the walls. They are given in Figure 7.4 for the following three cases:

- A building, whose height $ h $ is less than $ b $ should be considered to be one part.

- A building, whose height $ h $ is greater than $ b $, but less than $ 2b $, may be considered to be two parts, comprising: a lower part extending upwards from the ground by a height equal to $ b $ and an upper part consisting of the remainder.

- A building, whose height $ h $ is greater than $ 2b $ may be considered to be in multiple parts, comprising: a lower part extending upwards from the ground by a height equal to $ b $; an upper part extending downwards from the top by a height equal to $ b $ and a middle region, between the upper and lower parts, which may be divided into horizontal strips with a height $ h_{strip} $ as shown in Figure 7.4.

NOTE The rules for the velocity pressure distribution for leeward wall and sidewalls (zones A, B, C and E, see Figure 7.5) may be given in the National Annex or be defined for the individual project. The recommended procedure is to take the reference height as the height of the building.

"""

h_dis_help = """

For buildings in terrain category IV, closely spaced buildings and other obstructions cause the wind to behave as if the ground level was raised to a displacement height, $h_{dis}$.

The displacement height $h_{dis}$ may be determined by Expression (A.15) (see Figure A.5). The profile of peak velocity pressure over height (see Figure 4.2) may be lifted by $h_{dis}$.

• If $x \le 2\,h_{ave}$, then $h_{dis}$ is the lesser of
  $0.8\,h_{ave}$ or $0.6\,h$.

• If $2\,h_{ave} < x < 6\,h_{ave}$, then $h_{dis}$ is the lesser of
  $1.2\,h_{ave} - 0.2\,x$ or $0.6\,h$.

• If $x \ge 6\,h_{ave}$, then
  $h_{dis} = 0$.

In the absence of more accurate information, the obstruction height may be taken as $h_{ave} = 15m$ for terrain category IV. These rules are direction-dependent: the values of $h_{ave}$ and $x$ should be established for each 30° sector as described in 4.3.2.
"""

orography_help = """

Numerical calculation of orography coefficients

At isolated hills and ridges or cliffs and escarpments, different wind velocities occur depending on the upstream slope
$\Phi = H / L_u$
in the wind direction, where the height $H$ and the length $L_u$ are defined in Figure A.1.

The largest increase of the wind velocities occurs near the top of the slope and is determined by the orography factor $c_{oe}(z)$; see Figure A.1.
The slope has no significant effect on the standard deviation of the turbulence defined in 4.4 (1).

NOTE The turbulence intensity will decrease with increasing wind velocity at equal standard deviation.

The orography factor
$c_{oe}(z) = v_m / v_{eff}$
accounts for the increase in mean wind speed over isolated hills and escarpments (not undulating and mountainous regions).
It is related to the wind velocity at the base of the hill or escarpment.
The effects of orography should be taken into account in the following situations:

- For upwind slopes of hills and ridges: $0.05 < \Phi < 0.3$ and $|x| \le L_u / 2$
- For downwind slopes of hills and ridges:
- $\Phi < 0.3$ and $x < L_d / 2$
- $\Phi > 0.3$ and $x < 1.6 \cdot H$
- For upwind slopes of cliffs and escarpments: $0.05 < \Phi < 0.3$ and $|x| \le L_u / 2$
- For downwind slopes of cliffs and escarpments:
- $\Phi < 0.3$ and $x < 1.6 \cdot H$
- $\Phi > 0.3$ and $x < 5 \cdot H$

The factor $c_{oe}$ is defined as follows:
- If $\Phi < 0.05$, then $c_{oe} = 1$.
- If $0.05 \le \Phi \le 0.3$, then $c_{oe} = 1 + 2 \cdot s \cdot \Phi$.
- If $\Phi > 0.3$, then $c_{oe} = 1 + 0.6 \cdot s$.

where:
- $s$ is the orographic location factor (from Figures A.2/A.3), scaled to $L_{oe}$
- $\Phi = H / L_u$
- $L_{oe}$ is the effective upwind length (Table A.2)
- $L_u$ and $L_d$ are the upwind/downwind slope lengths
- $H$ is the feature height
- $x$ is the distance from crest
- $z$ is the site elevation above ground

Table A.2 — Effective length $L_{oe}$:

Type of slope ($\Phi = H / L_u$) | $L_{oe}$
----------------------------------|---------
Shallow ($0.05 < \Phi < 0.3$)    | $L_u$
Steep ($\Phi > 0.3$)              | $H / 0.3$

NOTE Use $c_{oe}(z) = 1.0$ in valleys unless funneling effects apply.

"""
net_pressure_help = """
Wind pressure on surfaces

The wind pressure acting on the external surfaces, $w_e$, should be obtained from:

$$
w_e = q_p(z_e)\cdot c_{pe}
$$

where:
- $q_p(z_e)$ is the peak velocity pressure
- $z_e$ is the reference height for the external pressure
- $c_{pe}$ is the pressure coefficient for the external pressure

The wind pressure acting on the internal surfaces of a structure, $w_i$, should be obtained from:

$$
w_i = q_p(z_i)\cdot c_{pi}
$$

where:
- $q_p(z_i)$ is the peak velocity pressure
- $z_i$ is the reference height for the internal pressure
- $c_{pi}$ is the pressure coefficient for the internal pressure

**Selection of $c_{pi}$ for maximum envelope pressure difference:**
- **Zone D (positive pressure):**  
  Maximum pressure difference when $c_{pi} = -0.3$.
- **Zones A, B, C (suction/negative pressure):**  
  Maximum pressure difference when $c_{pi} = 0.2$.

**Net Pressure Equation:**

$$
W_{net} = W_e - W_i
$$

- For **Zone D**:
  $$
  W_{net} = W_e - W_i(c_{pi} = -0.3)
  $$
- For **Zones A, B, C**:
  $$
  W_{net} = W_e - W_i(c_{pi} = 0.2)
  $$
"""

funnelling_help = """

**What Is Funnelling?**

Funnelling occurs when wind is channeled through a narrow passage—such as the space between two buildings—causing it to accelerate and increase in pressure.

---

**Impact of Funnelling**

- The accelerated airflow leads to higher wind pressures on the walls and roofs of the affected structures.  
- These increased pressures may necessitate enhanced design considerations to ensure structural safety and serviceability.

---

**BS EN 1991-1-4 and the UK National Annex**

The Eurocode standard BS EN 1991-1-4 establishes general rules for wind actions on structures.  
The UK National Annex (NA) supplements this by providing:

- More specific guidance on wind loading in the British context.  
- A method for adjusting (enhancing) the pressure coefficients to account for the funnelling effect in narrow passages.

"""

map_help = """

1. Click on the map to place markers (up to 2 points)
2. First click (red marker) = the project location, Second click (blue marker) = the closest sea location
3. Click 'Calculate Data' to get elevations and distance to sea
4. Third click resets to a new Point 1 or click 'Clear Points'

"""

wind_zone_help = """

Figure 7.5 from BS EN 1991-1-4.

"""

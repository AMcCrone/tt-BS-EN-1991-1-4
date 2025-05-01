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

(1) The reference heights, \( z_e \), for windward walls of rectangular plan buildings (zone D, see Figure 7.5) depend on the aspect ratio \( h/b \) and are always the upper heights of the different parts of the walls. They are given in Figure 7.4 for the following three cases:

- A building, whose height \( h \) is less than \( b \) should be considered to be one part.

- A building, whose height \( h \) is greater than \( b \), but less than \( 2b \), may be considered to be two parts, comprising: a lower part extending upwards from the ground by a height equal to \( b \) and an upper part consisting of the remainder.

- A building, whose height \( h \) is greater than \( 2b \) may be considered to be in multiple parts, comprising: a lower part extending upwards from the ground by a height equal to \( b \); an upper part extending downwards from the top by a height equal to \( b \) and a middle region, between the upper and lower parts, which may be divided into horizontal strips with a height \( h_{strip} \) as shown in Figure 7.4.

NOTE The rules for the velocity pressure distribution for leeward wall and sidewalls (zones A, B, C and E, see Figure 7.5) may be given in the National Annex or be defined for the individual project. The recommended procedure is to take the reference height as the height of the building.

"""

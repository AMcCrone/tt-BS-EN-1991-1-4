terrain_help = """
### Terrain Categories (UK)

The classification of roughness categories has been simplified into three terrain categories:

- **Terrain Category 0**: Referred to as **Sea** — open sea, lakes, and coastal areas exposed to open sea.
- **Terrain Categories I and II**: Grouped together as **Country terrain** — flat, open country with minimal obstacles.
- **Terrain Categories III and IV**: Grouped together as **Town terrain** — towns or cities with closely spaced obstacles.

**Note:** All inland lakes extending more than 1 km in the direction of wind and closer than 1 km upwind of the site should also be treated as **Sea**.

---

### Transition Between Roughness Categories (0, I, II, III, IV)

When calculating wind pressure parameters (qₚ and cₛc_d), transitions between terrain roughness categories must be considered. Two recommended procedures are:

#### Procedure 1
Use the **smoother terrain category in the upwind direction** if the structure is located:

- Less than 2 km from the smoother **Category 0**, or  
- Less than 1 km from smoother **Categories I to III**.

> Small areas (less than 10% of the area under consideration) with different roughness may be ignored.

#### Procedure 2
1. Determine the roughness categories for the upstream terrain in angular sectors.
2. For each sector, find the distance *x* from the building to where the terrain roughness changes.
3. If *x* is **smaller** than values from Table A.1 (based on height), use the **lower** roughness value.  
   If *x* is **larger**, use the **higher** roughness value.

> Again, small areas (<10%) with deviating roughness may be ignored.

If no distance *x* is specified (or height exceeds 50 m), default to using the **smaller** roughness length.

Linear interpolation may be used for intermediate heights.

> A building can be calculated in a lower terrain category if it lies within the limits defined in Table A.1.
"""


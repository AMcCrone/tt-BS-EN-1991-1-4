import pandas as pd
import streamlit as st
from typing import List, Tuple
from pressure_summary import calculate_pressure_data

def generate_pressure_summary_paragraphs(session_state, results_by_direction) -> List[str]:
    """
    Returns a list of 4 paragraphs (strings) summarising:
      1) maximum wind pressure and elevation(s)
      2) maximum suction and elevation(s)
      3) whether funnelling was considered
      4) whether an inset zone was considered, presence of Zone E and where
      5) final design value (largest absolute) with zone and elevations

    Relies on calculate_pressure_data(session_state, results_by_direction).
    """
    # 1) get calculated data
    summary_data, _, zone_pressures_by_direction = calculate_pressure_data(session_state, results_by_direction)
    summary_df = pd.DataFrame(summary_data)

    # Prepare paragraph outputs
    paragraphs: List[str] = []

    # ---------- Handle empty data ----------
    if summary_df.empty:
        paragraphs.append("No pressure/suction results available to summarise.")
        # still check funnelling / inset flags for informative paragraphs
        # funnelling paragraph:
        consider_funnelling = session_state.inputs.get("consider_funnelling", False) \
                             if hasattr(session_state, "inputs") else session_state.get("consider_funnelling", False)
        paragraphs.append(
            f"Funnelling considered: {'Yes' if consider_funnelling else 'No'}."
        )
        inset_enabled = session_state.inputs.get("inset_enabled", False) \
                        if hasattr(session_state, "inputs") else session_state.get("inset_enabled", False)
        paragraphs.append(
            f"Inset zone enabled: {'Yes' if inset_enabled else 'No'}. No zone E data available."
        )
        paragraphs.append("No design value can be selected because no results are present.")
        return paragraphs

    # ---------- Max positive pressure ----------
    pos_df = summary_df[summary_df["Net (kPa)"] > 0]
    if not pos_df.empty:
        max_pos_val = pos_df["Net (kPa)"].max()
        max_pos_rows = pos_df[pos_df["Net (kPa)"] == max_pos_val]
        # collect unique (Direction, Zone)
        locations = sorted(set(tuple(x) for x in max_pos_rows[["Direction", "Zone"]].values.tolist()))
        loc_text = ", ".join([f"{zone} on {direction}" for direction, zone in [(d,z) for d,z in locations]])
        paragraphs.append(
            f"Maximum positive wind pressure: {max_pos_val:.2f} kPa — present at {loc_text}."
        )
    else:
        paragraphs.append("No positive wind pressure (net pressure > 0) was found in the results.")

    # ---------- Max suction (most negative) ----------
    neg_df = summary_df[summary_df["Net (kPa)"] < 0]
    if not neg_df.empty:
        min_neg_val = neg_df["Net (kPa)"].min()  # most negative
        min_neg_rows = neg_df[neg_df["Net (kPa)"] == min_neg_val]
        locations_neg = sorted(set(tuple(x) for x in min_neg_rows[["Direction", "Zone"]].values.tolist()))
        loc_text_neg = ", ".join([f"{zone} on {direction}" for direction, zone in [(d,z) for d,z in locations_neg]])
        paragraphs.append(
            f"Maximum suction (most negative net): {min_neg_val:.2f} kPa — present at {loc_text_neg}."
        )
    else:
        paragraphs.append("No suction (net negative pressures) was found in the results.")

    # ---------- Funnelling paragraph ----------
    # check session state flags robustly
    consider_funnelling = None
    if hasattr(session_state, "inputs"):
        consider_funnelling = session_state.inputs.get("consider_funnelling", None)
    if consider_funnelling is None:
        consider_funnelling = session_state.get("consider_funnelling", False)
    paragraphs.append(
        f"Funnelling considered: {'Yes' if bool(consider_funnelling) else 'No'}. "
        "This reflects whether funnelling effects between buildings were enabled in the model."
    )

    # ---------- Inset / Zone E paragraph ----------
    inset_enabled = None
    if hasattr(session_state, "inputs"):
        inset_enabled = bool(session_state.inputs.get("inset_enabled", False))
    else:
        inset_enabled = bool(session_state.get("inset_enabled", False))

    # Find Zone E occurrences in zone_pressures_by_direction
    zone_e_entries = []
    for direction, zd in zone_pressures_by_direction.items():
        e = zd.get("E")
        if e is not None:
            # net_pressure_kpa stored rounded
            zone_e_entries.append({
                "Direction": direction,
                "Net (kPa)": e.get("net_pressure_kpa"),
                "cp,e": e.get("cp_e")
            })

    if zone_e_entries:
        # build listing (direction -> value (kPa) and cp,e)
        entries_txt = "; ".join([f"{ent['Direction']} = {ent['Net (kPa)']:.2f} kPa (cp,e={ent['cp,e']})"
                                 for ent in zone_e_entries])
        paragraphs.append(
            f"Inset zone enabled: {'Yes' if inset_enabled else 'No'}. "
            f"Zone E is present on the following elevation(s): {entries_txt}."
        )
    else:
        paragraphs.append(
            f"Inset zone enabled: {'Yes' if inset_enabled else 'No'}. Zone E was not present on any elevation."
        )

    # ---------- Final design value paragraph ----------
    # design value = maximum absolute net pressure across all rows
    summary_df["abs_Net"] = summary_df["Net (kPa)"].abs()
    max_abs_val = summary_df["abs_Net"].max()
    max_abs_rows = summary_df[summary_df["abs_Net"] == max_abs_val]

    # Collect unique zone/direction combos (may be multiple ties)
    combos = sorted(set(tuple(x) for x in max_abs_rows[["Direction", "Zone", "Net (kPa)"]].values.tolist()))
    combo_texts = []
    for direction, zone, net in combos:
        kind = "pressure" if net > 0 else "suction" if net < 0 else "zero"
        combo_texts.append(f"{zone} on {direction} ({net:.2f} kPa, {kind})")
    combo_text = "; ".join(combo_texts)

    paragraphs.append(
        f"Design value (largest absolute net) to be used: {max_abs_val:.2f} kPa — coming from {combo_text}."
    )

    return paragraphs

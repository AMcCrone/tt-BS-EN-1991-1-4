def get_terrain_categories():
    """
    Returns terrain categories according to UK National Annex.
    Keys are the simplified codes and values are the detailed descriptions.
    """
    return {
        "Sea": "Open sea, lakes and coastal areas exposed to open sea",
        "Country": "Flat open country without obstacles",
        "Town": "Town or city terrain with closely spaced obstacles"
    }


def get_terrain_categories():
    """
    Returns terrain categories according to Eurocode EN 1991-1-4
    """
    return [
        "0 - Sea or coastal area exposed to the open sea",
        "I - Lakes or flat and horizontal area with negligible vegetation",
        "II - Area with low vegetation and isolated obstacles",
        "III - Area with regular cover of vegetation or buildings",
        "IV - Area where at least 15% of surface is covered with buildings"
    ]

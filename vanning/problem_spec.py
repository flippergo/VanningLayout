"""Problem constants for the vanning design task."""

from vanning.geometry import BoxPlacement, Container, oriented_size


# 20ft container inner dimensions [mm]
CONTAINER_20FT = Container(l=5898, w=2352, h=2393)

# Box outer dimensions [mm] by type (length, width, height)
BOX_DIMS = {
    "A": (1400, 1000, 800),
    "B": (1200, 900, 700),
    "C": (800, 600, 600),
}


def box_size(box_type: str, yaw_deg: int) -> tuple[float, float, float]:
    """Get oriented size for a box type under 0/90 degree yaw."""
    key = box_type.upper()
    if key not in BOX_DIMS:
        raise ValueError(f"unknown box_type: {box_type}")
    length, width, height = BOX_DIMS[key]
    return oriented_size(length, width, height, yaw_deg)


def place_box(box_type: str, x: float, y: float, z: float, yaw_deg: int) -> BoxPlacement:
    """Create BoxPlacement from a box type and position."""
    l, w, h = box_size(box_type, yaw_deg)
    return BoxPlacement(x=x, y=y, z=z, l=l, w=w, h=h)


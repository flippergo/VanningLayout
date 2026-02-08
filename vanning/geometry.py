from dataclasses import dataclass


@dataclass(frozen=True)
class BoxPlacement:
    """Axis-aligned box placement by its left-front-bottom corner and size."""

    x: float
    y: float
    z: float
    l: float
    w: float
    h: float

    @property
    def x_max(self) -> float:
        return self.x + self.l

    @property
    def y_max(self) -> float:
        return self.y + self.w

    @property
    def z_max(self) -> float:
        return self.z + self.h


@dataclass(frozen=True)
class Container:
    """Container inner dimensions."""

    l: float
    w: float
    h: float


def oriented_size(length: float, width: float, height: float, yaw_deg: int) -> tuple[float, float, float]:
    """Return (l, w, h) after allowed horizontal rotation."""
    if yaw_deg == 0:
        return (length, width, height)
    if yaw_deg == 90:
        return (width, length, height)
    raise ValueError("yaw_deg must be either 0 or 90")


def _strict_interval_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> bool:
    """Internal overlap only. Boundary touch is not overlap."""
    return max(a_min, b_min) < min(a_max, b_max)


def boxes_collide(a: BoxPlacement, b: BoxPlacement) -> bool:
    """Return True only when two AABBs overlap in volume."""
    return (
        _strict_interval_overlap(a.x, a.x_max, b.x, b.x_max)
        and _strict_interval_overlap(a.y, a.y_max, b.y, b.y_max)
        and _strict_interval_overlap(a.z, a.z_max, b.z, b.z_max)
    )


def is_inside_container(box: BoxPlacement, container: Container) -> bool:
    """Inclusive boundary check for container limits."""
    return (
        box.x >= 0
        and box.y >= 0
        and box.z >= 0
        and box.x_max <= container.l
        and box.y_max <= container.w
        and box.z_max <= container.h
    )


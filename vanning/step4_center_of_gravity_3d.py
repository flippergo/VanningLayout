"""Step4: center-of-gravity constrained 3D packing built on top of Step3."""

from dataclasses import dataclass, field
from math import hypot

from vanning.geometry import Container
from vanning.step3_weighted_3d import (
    WeightedItem3D,
    WeightedPackedBin3D,
    WeightedPlacedItem3D,
    pack_weighted_3d_by_destination_ffd,
    validate_stable_placements,
)


@dataclass
class CenterBalancedBin3D:
    """A Step3 bin translated to improve horizontal center of gravity."""

    container: Container
    dest: str
    max_weight_kg: float
    max_center_offset_mm: float
    placements: list[WeightedPlacedItem3D] = field(default_factory=list)

    @property
    def total_weight_kg(self) -> float:
        return sum(placement.item.weight_kg for placement in self.placements)

    @property
    def remaining_weight_kg(self) -> float:
        return self.max_weight_kg - self.total_weight_kg

    @property
    def center_of_gravity_x(self) -> float:
        return horizontal_center_of_gravity(self.placements)[0]

    @property
    def center_of_gravity_y(self) -> float:
        return horizontal_center_of_gravity(self.placements)[1]

    @property
    def center_offset_mm(self) -> float:
        return center_offset_distance_mm(self.placements, self.container)

    @property
    def satisfies_center_constraint(self) -> bool:
        return self.center_offset_mm <= self.max_center_offset_mm


@dataclass(frozen=True)
class CenterBalancedPackingSummary3D:
    """Summary of the Step4 center-constrained 3D packing result."""

    bins: list[CenterBalancedBin3D]
    max_center_offset_mm: float

    @property
    def bin_count(self) -> int:
        return len(self.bins)

    @property
    def total_weight_kg(self) -> float:
        return sum(bin_.total_weight_kg for bin_ in self.bins)

    @property
    def max_observed_center_offset_mm(self) -> float:
        return max((bin_.center_offset_mm for bin_ in self.bins), default=0.0)

    @property
    def all_bins_within_center_constraint(self) -> bool:
        return all(bin_.satisfies_center_constraint for bin_ in self.bins)


def horizontal_center_of_gravity(placements: list[WeightedPlacedItem3D]) -> tuple[float, float]:
    """Return the horizontal center of gravity of one packed bin."""
    if not placements:
        raise ValueError("placements must be non-empty")

    total_weight = sum(placement.item.weight_kg for placement in placements)
    if total_weight <= 0:
        raise ValueError("total placement weight must be positive")

    weighted_x = sum((placement.x + placement.length / 2) * placement.item.weight_kg for placement in placements)
    weighted_y = sum((placement.y + placement.width / 2) * placement.item.weight_kg for placement in placements)
    return (weighted_x / total_weight, weighted_y / total_weight)


def center_offset_distance_mm(placements: list[WeightedPlacedItem3D], container: Container) -> float:
    """Return horizontal center-of-gravity distance from the floor center."""
    cg_x, cg_y = horizontal_center_of_gravity(placements)
    return hypot(cg_x - container.l / 2, cg_y - container.w / 2)


def translate_bin_toward_center(
    bin_: WeightedPackedBin3D, max_center_offset_mm: float
) -> CenterBalancedBin3D:
    """Translate one whole Step3 bin within the container to reduce center offset."""
    if max_center_offset_mm < 0:
        raise ValueError("max_center_offset_mm must be non-negative")
    if not bin_.placements:
        raise ValueError("bin placements must be non-empty")

    x_min = min(placement.x for placement in bin_.placements)
    x_max = max(placement.box.x_max for placement in bin_.placements)
    y_min = min(placement.y for placement in bin_.placements)
    y_max = max(placement.box.y_max for placement in bin_.placements)

    cg_x, cg_y = horizontal_center_of_gravity(bin_.placements)
    target_dx = bin_.container.l / 2 - cg_x
    target_dy = bin_.container.w / 2 - cg_y

    min_dx = -x_min
    max_dx = bin_.container.l - x_max
    min_dy = -y_min
    max_dy = bin_.container.w - y_max
    dx = min(max(target_dx, min_dx), max_dx)
    dy = min(max(target_dy, min_dy), max_dy)

    translated = [
        WeightedPlacedItem3D(
            item=placement.item,
            x=placement.x + dx,
            y=placement.y + dy,
            z=placement.z,
            length=placement.length,
            width=placement.width,
            height=placement.height,
            rotated=placement.rotated,
        )
        for placement in bin_.placements
    ]
    validate_stable_placements(translated)

    return CenterBalancedBin3D(
        container=bin_.container,
        dest=bin_.dest,
        max_weight_kg=bin_.max_weight_kg,
        max_center_offset_mm=max_center_offset_mm,
        placements=translated,
    )


def pack_center_balanced_3d_by_destination_ffd(
    items: list[WeightedItem3D],
    container: Container,
    max_weight_kg: float,
    max_center_offset_mm: float,
) -> CenterBalancedPackingSummary3D:
    """Apply Step3 packing, then translate each bin toward the floor center."""
    if max_center_offset_mm < 0:
        raise ValueError("max_center_offset_mm must be non-negative")

    step3_summary = pack_weighted_3d_by_destination_ffd(items, container, max_weight_kg)
    balanced_bins = [
        translate_bin_toward_center(bin_, max_center_offset_mm)
        for bin_ in step3_summary.bins
    ]
    summary = CenterBalancedPackingSummary3D(
        bins=balanced_bins,
        max_center_offset_mm=max_center_offset_mm,
    )

    if not summary.all_bins_within_center_constraint:
        raise ValueError("center of gravity constraint violated")

    return summary

"""Step5: realistic stability with multi-support, support-area ratio, and center projection."""

from dataclasses import dataclass, field

from vanning.geometry import Container, boxes_collide
from vanning.problem_spec import STEP5_MIN_SUPPORT_AREA_RATIO
from vanning.step3_weighted_3d import (
    WeightedItem3D,
    WeightedPackedBin3D,
    WeightedPlacedItem3D,
    _exceeds_weight_limit,
    assign_by_destination_and_weight_ffd,
)
from vanning.step4_center_of_gravity_3d import CenterBalancedBin3D, translate_bin_toward_center


SupportRectangle = tuple[float, float, float, float]


@dataclass(frozen=True)
class RealisticStablePackingSummary3D:
    """Summary of the Step5 realistic-stability packing result."""

    bins: list[CenterBalancedBin3D]
    max_center_offset_mm: float
    min_support_area_ratio: float

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


def support_contact_rectangles(
    placement: WeightedPlacedItem3D, placements: list[WeightedPlacedItem3D]
) -> list[SupportRectangle]:
    """Return bottom-face contact rectangles with supporters directly underneath."""
    if placement.z == 0:
        return []

    contacts: list[SupportRectangle] = []
    for supporter in placements:
        if supporter is placement or supporter.box.z_max != placement.z:
            continue

        overlap_x_min = max(placement.x, supporter.x)
        overlap_x_max = min(placement.box.x_max, supporter.box.x_max)
        overlap_y_min = max(placement.y, supporter.y)
        overlap_y_max = min(placement.box.y_max, supporter.box.y_max)
        if overlap_x_min >= overlap_x_max or overlap_y_min >= overlap_y_max:
            continue

        contacts.append((overlap_x_min, overlap_x_max, overlap_y_min, overlap_y_max))

    return contacts


def supported_area_ratio(
    placement: WeightedPlacedItem3D, placements: list[WeightedPlacedItem3D]
) -> float:
    """Return the fraction of the bottom face covered by direct supporters."""
    if placement.z == 0:
        return 1.0

    base_area = placement.length * placement.width
    if base_area <= 0:
        raise ValueError(f"placement base area must be positive: {placement.item.item_id}")

    supported_area = sum((x_max - x_min) * (y_max - y_min) for x_min, x_max, y_min, y_max in support_contact_rectangles(placement, placements))
    return supported_area / base_area


def is_projection_supported(
    placement: WeightedPlacedItem3D, placements: list[WeightedPlacedItem3D]
) -> bool:
    """Return True when the bottom-face center projects onto the supported region."""
    if placement.z == 0:
        return True

    center_x = placement.x + placement.length / 2
    center_y = placement.y + placement.width / 2
    return any(
        x_min <= center_x <= x_max and y_min <= center_y <= y_max
        for x_min, x_max, y_min, y_max in support_contact_rectangles(placement, placements)
    )


def is_realistically_supported(
    placement: WeightedPlacedItem3D,
    placements: list[WeightedPlacedItem3D],
    min_support_area_ratio: float = STEP5_MIN_SUPPORT_AREA_RATIO,
) -> bool:
    """Return True when a placement satisfies the Step5 realistic support rule."""
    if not 0 < min_support_area_ratio <= 1:
        raise ValueError("min_support_area_ratio must be in (0, 1]")
    if placement.z == 0:
        return True

    return (
        supported_area_ratio(placement, placements) >= min_support_area_ratio
        and is_projection_supported(placement, placements)
    )


def validate_realistic_stability(
    placements: list[WeightedPlacedItem3D],
    min_support_area_ratio: float = STEP5_MIN_SUPPORT_AREA_RATIO,
) -> None:
    """Raise when any placement violates the Step5 realistic support rule."""
    for placement in sorted(placements, key=lambda placed: (placed.z, placed.y, placed.x, placed.item.item_id)):
        if not is_realistically_supported(placement, placements, min_support_area_ratio=min_support_area_ratio):
            raise ValueError(f"unstable placement under Step5 rule: {placement.item.item_id}")


@dataclass
class _StableWeightedBin3D:
    """A weighted bin that allows multi-support under the Step5 rule."""

    container: Container
    dest: str
    max_weight_kg: float
    min_support_area_ratio: float
    placements: list[WeightedPlacedItem3D] = field(default_factory=list)

    @property
    def total_weight_kg(self) -> float:
        return sum(placement.item.weight_kg for placement in self.placements)

    @property
    def remaining_weight_kg(self) -> float:
        return self.max_weight_kg - self.total_weight_kg

    def add(self, item: WeightedItem3D) -> bool:
        if item.dest != self.dest:
            return False
        if item.length <= 0 or item.width <= 0 or item.height <= 0:
            return False
        if item.weight_kg <= 0 or _exceeds_weight_limit(item.weight_kg, self.remaining_weight_kg):
            return False

        placement = self._find_best_placement(item)
        if placement is None:
            return False

        self.placements.append(placement)
        return True

    def _find_best_placement(self, item: WeightedItem3D) -> WeightedPlacedItem3D | None:
        best: WeightedPlacedItem3D | None = None
        best_score: tuple[float, float, float, float, int] | None = None

        for x, y, z in self._candidate_positions():
            for length, width, rotated in _orientation_candidates(item):
                candidate = WeightedPlacedItem3D(
                    item=item,
                    x=x,
                    y=y,
                    z=z,
                    length=length,
                    width=width,
                    height=item.height,
                    rotated=rotated,
                )
                if not self._is_valid(candidate):
                    continue

                score = (
                    candidate.y,
                    candidate.x,
                    candidate.z,
                    self.container.h - candidate.box.z_max,
                    1 if candidate.rotated else 0,
                )
                if best_score is None or score < best_score:
                    best_score = score
                    best = candidate

        return best

    def _candidate_positions(self) -> list[tuple[float, float, float]]:
        candidates: set[tuple[float, float, float]] = {(0.0, 0.0, 0.0)}
        for placed in self.placements:
            candidates.add((placed.box.x_max, placed.y, placed.z))
            candidates.add((placed.x, placed.box.y_max, placed.z))
            candidates.add((placed.x, placed.y, placed.box.z_max))

        valid = [
            (x, y, z)
            for x, y, z in candidates
            if 0 <= x <= self.container.l and 0 <= y <= self.container.w and 0 <= z <= self.container.h
        ]
        return sorted(valid, key=lambda candidate: (candidate[2], candidate[1], candidate[0]))

    def _is_valid(self, placement: WeightedPlacedItem3D) -> bool:
        box = placement.box
        if box.x_max > self.container.l or box.y_max > self.container.w or box.z_max > self.container.h:
            return False

        for existing in self.placements:
            if boxes_collide(box, existing.box):
                return False

        return is_realistically_supported(
            placement,
            self.placements,
            min_support_area_ratio=self.min_support_area_ratio,
        )


def pack_realistic_stable_3d_by_destination_ffd(
    items: list[WeightedItem3D],
    container: Container,
    max_weight_kg: float,
    max_center_offset_mm: float,
    min_support_area_ratio: float = STEP5_MIN_SUPPORT_AREA_RATIO,
) -> RealisticStablePackingSummary3D:
    """Pack items with destination, weight, center-of-gravity, and Step5 stability rules."""
    if container.l <= 0 or container.w <= 0 or container.h <= 0:
        raise ValueError("container dimensions must be positive")
    if max_center_offset_mm < 0:
        raise ValueError("max_center_offset_mm must be non-negative")
    if not 0 < min_support_area_ratio <= 1:
        raise ValueError("min_support_area_ratio must be in (0, 1]")

    allocations = assign_by_destination_and_weight_ffd(items, max_weight_kg)
    centered_bins: list[CenterBalancedBin3D] = []

    for allocation_bin in allocations.bins:
        for packed_bin in _pack_allocation_bin(
            allocation_bin.items,
            container,
            max_weight_kg,
            min_support_area_ratio,
        ):
            centered_bin = translate_bin_toward_center(packed_bin, max_center_offset_mm)
            validate_realistic_stability(centered_bin.placements, min_support_area_ratio=min_support_area_ratio)
            centered_bins.append(centered_bin)

    summary = RealisticStablePackingSummary3D(
        bins=centered_bins,
        max_center_offset_mm=max_center_offset_mm,
        min_support_area_ratio=min_support_area_ratio,
    )
    if not summary.all_bins_within_center_constraint:
        raise ValueError("center of gravity constraint violated")

    return summary


def pack_single_realistic_stable_bin(
    items: list[WeightedItem3D],
    container: Container,
    max_weight_kg: float,
    max_center_offset_mm: float,
    min_support_area_ratio: float = STEP5_MIN_SUPPORT_AREA_RATIO,
) -> CenterBalancedBin3D | None:
    """Try to pack one destination-specific item set into a single centered bin."""
    if not items:
        raise ValueError("items must be non-empty")
    if container.l <= 0 or container.w <= 0 or container.h <= 0:
        raise ValueError("container dimensions must be positive")
    if max_weight_kg <= 0:
        raise ValueError("max_weight_kg must be positive")
    if max_center_offset_mm < 0:
        raise ValueError("max_center_offset_mm must be non-negative")
    if not 0 < min_support_area_ratio <= 1:
        raise ValueError("min_support_area_ratio must be in (0, 1]")

    dest = items[0].dest
    bin_ = _StableWeightedBin3D(
        container=container,
        dest=dest,
        max_weight_kg=max_weight_kg,
        min_support_area_ratio=min_support_area_ratio,
    )

    ordered = sorted(items, key=lambda item: (-item.volume, -max(item.length, item.width), item.item_id))
    for item in ordered:
        if item.dest != dest:
            raise ValueError("all items must have the same destination")
        _validate_item_can_fit(item, container)
        if not bin_.add(item):
            return None

    packed_bin = WeightedPackedBin3D(
        container=container,
        dest=dest,
        max_weight_kg=max_weight_kg,
        placements=bin_.placements.copy(),
    )
    centered_bin = translate_bin_toward_center(packed_bin, max_center_offset_mm)
    validate_realistic_stability(
        centered_bin.placements,
        min_support_area_ratio=min_support_area_ratio,
    )
    if not centered_bin.satisfies_center_constraint:
        return None
    return centered_bin


def _pack_allocation_bin(
    items: list[WeightedItem3D],
    container: Container,
    max_weight_kg: float,
    min_support_area_ratio: float,
) -> list[WeightedPackedBin3D]:
    ordered = sorted(items, key=lambda item: (-item.volume, -max(item.length, item.width), item.item_id))
    bins: list[_StableWeightedBin3D] = []

    for item in ordered:
        _validate_item_can_fit(item, container)

        placed = False
        for bin_ in bins:
            if bin_.add(item):
                placed = True
                break

        if not placed:
            new_bin = _StableWeightedBin3D(
                container=container,
                dest=item.dest,
                max_weight_kg=max_weight_kg,
                min_support_area_ratio=min_support_area_ratio,
            )
            if not new_bin.add(item):
                raise ValueError(f"item cannot fit in any bin: {item.item_id}")
            bins.append(new_bin)

    return [
        WeightedPackedBin3D(
            container=container,
            dest=bin_.dest,
            max_weight_kg=max_weight_kg,
            placements=bin_.placements.copy(),
        )
        for bin_ in bins
    ]


def _validate_item_can_fit(item: WeightedItem3D, container: Container) -> None:
    fits_without_rotation = (
        item.length <= container.l and item.width <= container.w and item.height <= container.h
    )
    fits_with_rotation = (
        item.allow_rotate
        and item.width <= container.l
        and item.length <= container.w
        and item.height <= container.h
    )
    if not (fits_without_rotation or fits_with_rotation):
        raise ValueError(f"item cannot fit in any bin: {item.item_id}")


def _orientation_candidates(item: WeightedItem3D) -> list[tuple[float, float, bool]]:
    candidates = [(item.length, item.width, False)]
    if item.allow_rotate and item.length != item.width:
        candidates.append((item.width, item.length, True))
    return candidates

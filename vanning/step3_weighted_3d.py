"""Step3: weight-constrained 3D packing built on top of Step2 placement."""

from dataclasses import dataclass, field

from vanning.geometry import BoxPlacement, Container
from vanning.step2_3d import Item3D, pack_3d_by_destination_ffd


@dataclass(frozen=True)
class WeightedItem3D:
    """A 3D item with destination and payload weight."""

    item_id: str
    length: float
    width: float
    height: float
    weight_kg: float
    dest: str
    allow_rotate: bool = True

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height

    def to_step2_item(self) -> Item3D:
        return Item3D(
            item_id=self.item_id,
            length=self.length,
            width=self.width,
            height=self.height,
            dest=self.dest,
            allow_rotate=self.allow_rotate,
        )


@dataclass(frozen=True)
class WeightedPlacedItem3D:
    """A weighted item placed at a concrete 3D position."""

    item: WeightedItem3D
    x: float
    y: float
    z: float
    length: float
    width: float
    height: float
    rotated: bool

    @property
    def box(self) -> BoxPlacement:
        return BoxPlacement(
            x=self.x,
            y=self.y,
            z=self.z,
            l=self.length,
            w=self.width,
            h=self.height,
        )


@dataclass
class WeightAllocationBin:
    """A destination-specific bin assignment constrained only by payload weight."""

    dest: str
    max_weight_kg: float
    items: list[WeightedItem3D] = field(default_factory=list)

    @property
    def total_weight_kg(self) -> float:
        return sum(item.weight_kg for item in self.items)

    @property
    def remaining_weight_kg(self) -> float:
        return self.max_weight_kg - self.total_weight_kg

    def add(self, item: WeightedItem3D) -> bool:
        if item.dest != self.dest:
            return False
        if item.weight_kg <= 0 or item.weight_kg > self.remaining_weight_kg:
            return False
        self.items.append(item)
        return True


@dataclass(frozen=True)
class WeightAllocationSummary:
    """Summary of the Step3 weight-only assignment phase."""

    bins: list[WeightAllocationBin]

    @property
    def bin_count(self) -> int:
        return len(self.bins)


@dataclass
class WeightedPackedBin3D:
    """A placed 3D bin that also tracks payload weight."""

    container: Container
    dest: str
    max_weight_kg: float
    placements: list[WeightedPlacedItem3D] = field(default_factory=list)

    @property
    def total_weight_kg(self) -> float:
        return sum(placement.item.weight_kg for placement in self.placements)

    @property
    def remaining_weight_kg(self) -> float:
        return self.max_weight_kg - self.total_weight_kg


@dataclass(frozen=True)
class WeightedPackingSummary3D:
    """Summary of the Step3 weight-aware 3D packing result."""

    bins: list[WeightedPackedBin3D]

    @property
    def bin_count(self) -> int:
        return len(self.bins)

    @property
    def total_weight_kg(self) -> float:
        return sum(bin_.total_weight_kg for bin_ in self.bins)


def assign_by_destination_and_weight_ffd(
    items: list[WeightedItem3D], max_weight_kg: float
) -> WeightAllocationSummary:
    """Assign items to bins using destination-aware first-fit decreasing by weight."""
    if max_weight_kg <= 0:
        raise ValueError("max_weight_kg must be positive")

    for item in items:
        if item.length <= 0 or item.width <= 0 or item.height <= 0:
            raise ValueError(f"item dimensions must be positive: {item.item_id}")
        if item.weight_kg <= 0:
            raise ValueError(f"item weight must be positive: {item.item_id}")
        if item.weight_kg > max_weight_kg:
            raise ValueError(f"item exceeds max_weight_kg: {item.item_id}")
        if not item.dest:
            raise ValueError(f"item.dest must be non-empty: {item.item_id}")

    ordered = sorted(
        items,
        key=lambda item: (item.dest, -item.weight_kg, -item.volume, item.item_id),
    )
    bins: list[WeightAllocationBin] = []

    for item in ordered:
        placed = False
        for bin_ in bins:
            if bin_.dest != item.dest:
                continue
            if bin_.add(item):
                placed = True
                break

        if not placed:
            new_bin = WeightAllocationBin(dest=item.dest, max_weight_kg=max_weight_kg)
            if not new_bin.add(item):
                raise ValueError(f"item exceeds max_weight_kg: {item.item_id}")
            bins.append(new_bin)

    return WeightAllocationSummary(bins=bins)


def pack_weighted_3d_by_destination_ffd(
    items: list[WeightedItem3D], container: Container, max_weight_kg: float
) -> WeightedPackingSummary3D:
    """Apply Step3 weight assignment, then pack each assigned bin with Step2 3D placement."""
    allocations = assign_by_destination_and_weight_ffd(items, max_weight_kg)
    packed_bins: list[WeightedPackedBin3D] = []

    for allocation_bin in allocations.bins:
        weight_by_id = {item.item_id: item for item in allocation_bin.items}
        step2_summary = pack_3d_by_destination_ffd(
            [item.to_step2_item() for item in allocation_bin.items],
            container,
        )

        for step2_bin in step2_summary.bins:
            placements = [
                WeightedPlacedItem3D(
                    item=weight_by_id[placement.item.item_id],
                    x=placement.x,
                    y=placement.y,
                    z=placement.z,
                    length=placement.length,
                    width=placement.width,
                    height=placement.height,
                    rotated=placement.rotated,
                )
                for placement in step2_bin.placements
            ]
            packed_bins.append(
                WeightedPackedBin3D(
                    container=container,
                    dest=step2_bin.dest,
                    max_weight_kg=max_weight_kg,
                    placements=placements,
                )
            )

    return WeightedPackingSummary3D(bins=packed_bins)

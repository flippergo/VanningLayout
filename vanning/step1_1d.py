"""Step 1-1: destination-aware 1D bin packing helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item1D:
    """1D packing item.

    Attributes:
        item_id: unique identifier.
        length: required length [mm]. Must be positive.
        dest: destination label (e.g. "X" or "Y").
    """

    item_id: str
    length: float
    dest: str


@dataclass
class Bin1D:
    """A single 1D container bin for one destination only."""

    capacity: float
    dest: str
    items: list[Item1D]
    used_length: float = 0.0

    @property
    def remaining_length(self) -> float:
        return self.capacity - self.used_length

    def can_fit(self, item: Item1D) -> bool:
        return item.dest == self.dest and item.length <= self.remaining_length

    def add(self, item: Item1D) -> None:
        if not self.can_fit(item):
            raise ValueError("item cannot be packed into this bin")
        self.items.append(item)
        self.used_length += item.length


@dataclass(frozen=True)
class PackingSummary:
    """Result summary for destination-aware 1D packing."""

    bins: list[Bin1D]

    @property
    def bin_count(self) -> int:
        return len(self.bins)

    @property
    def total_unused_length(self) -> float:
        return sum(bin_.remaining_length for bin_ in self.bins)


def pack_1d_by_destination_ffd(items: list[Item1D], bin_capacity: float) -> PackingSummary:
    """Pack 1D items using First-Fit Decreasing per destination.

    Constraints:
      - A bin can contain only one destination.
      - Item length must be <= bin_capacity.

    This is a heuristic (not guaranteed globally optimal).
    """
    if bin_capacity <= 0:
        raise ValueError("bin_capacity must be positive")

    for item in items:
        if item.length <= 0:
            raise ValueError(f"item.length must be positive: {item.item_id}")
        if item.length > bin_capacity:
            raise ValueError(f"item cannot fit in any bin: {item.item_id}")
        if not item.dest:
            raise ValueError(f"item.dest must be non-empty: {item.item_id}")

    bins: list[Bin1D] = []

    # Sort by destination first (for deterministic grouping), then by descending length.
    ordered = sorted(items, key=lambda i: (i.dest, -i.length, i.item_id))

    for item in ordered:
        placed = False
        for bin_ in bins:
            if bin_.can_fit(item):
                bin_.add(item)
                placed = True
                break

        if not placed:
            new_bin = Bin1D(capacity=bin_capacity, dest=item.dest, items=[])
            new_bin.add(item)
            bins.append(new_bin)

    return PackingSummary(bins=bins)

"""Step2: 重さ・重心なしの 3D パッキング。"""

from dataclasses import dataclass, field

from vanning.geometry import BoxPlacement, Container, boxes_collide


@dataclass(frozen=True)
class Item3D:
    """3D パッキング対象の箱。"""

    item_id: str
    length: float
    width: float
    height: float
    dest: str
    allow_rotate: bool = True

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass(frozen=True)
class PlacedItem3D:
    """3D で配置済みの箱。"""

    item: Item3D
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
class Bin3D:
    """1コンテナ分の 3D パッキング状態。"""

    container: Container
    dest: str
    placements: list[PlacedItem3D] = field(default_factory=list)

    @property
    def used_volume(self) -> float:
        return sum(p.item.volume for p in self.placements)

    @property
    def remaining_volume(self) -> float:
        return self.container.l * self.container.w * self.container.h - self.used_volume

    def add(self, item: Item3D) -> bool:
        placement = self._find_best_placement(item)
        if placement is None:
            return False
        self.placements.append(placement)
        return True

    def _find_best_placement(self, item: Item3D) -> PlacedItem3D | None:
        best: PlacedItem3D | None = None
        best_score: tuple[float, float, float, float, int] | None = None

        for x, y, z in self._candidate_positions():
            for length, width, rotated in _orientation_candidates(item):
                candidate = PlacedItem3D(
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
                    candidate.z,
                    candidate.y,
                    candidate.x,
                    self.container.h - candidate.box.z_max,
                    1 if candidate.rotated else 0,
                )
                if best_score is None or score < best_score:
                    best_score = score
                    best = candidate

        return best

    def _candidate_positions(self) -> list[tuple[float, float, float]]:
        candidates: set[tuple[float, float, float]] = {(0.0, 0.0, 0.0)}
        for p in self.placements:
            candidates.add((p.box.x_max, p.y, p.z))
            candidates.add((p.x, p.box.y_max, p.z))
            candidates.add((p.x, p.y, p.box.z_max))

        valid = [
            (x, y, z)
            for x, y, z in candidates
            if 0 <= x <= self.container.l and 0 <= y <= self.container.w and 0 <= z <= self.container.h
        ]
        return sorted(valid, key=lambda c: (c[2], c[1], c[0]))

    def _is_valid(self, placement: PlacedItem3D) -> bool:
        box = placement.box
        if box.x_max > self.container.l or box.y_max > self.container.w or box.z_max > self.container.h:
            return False

        for existing in self.placements:
            if boxes_collide(box, existing.box):
                return False

        return self._is_supported(placement)

    def _is_supported(self, placement: PlacedItem3D) -> bool:
        if placement.z == 0:
            return True

        for existing in self.placements:
            if existing.box.z_max != placement.z:
                continue
            x_overlap = _strict_overlap_len(existing.x, existing.box.x_max, placement.x, placement.box.x_max)
            y_overlap = _strict_overlap_len(existing.y, existing.box.y_max, placement.y, placement.box.y_max)
            if x_overlap > 0 and y_overlap > 0:
                return True

        return False


@dataclass(frozen=True)
class PackingSummary3D:
    """3D パッキング結果の要約。"""

    bins: list[Bin3D]

    @property
    def bin_count(self) -> int:
        return len(self.bins)


def pack_3d_by_destination_ffd(items: list[Item3D], container: Container) -> PackingSummary3D:
    """行先ごとの First-Fit Decreasing で 3D パッキングを実行する。"""
    if container.l <= 0 or container.w <= 0 or container.h <= 0:
        raise ValueError("container dimensions must be positive")

    for item in items:
        if item.length <= 0 or item.width <= 0 or item.height <= 0:
            raise ValueError(f"item dimensions must be positive: {item.item_id}")
        if not item.dest:
            raise ValueError(f"item.dest must be non-empty: {item.item_id}")

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

    ordered = sorted(items, key=lambda i: (i.dest, -i.volume, -max(i.length, i.width), i.item_id))
    bins: list[Bin3D] = []

    for item in ordered:
        placed = False
        for bin_ in bins:
            if bin_.dest != item.dest:
                continue
            if bin_.add(item):
                placed = True
                break

        if not placed:
            bin_ = Bin3D(container=container, dest=item.dest)
            if not bin_.add(item):
                raise ValueError(f"item cannot fit in any bin: {item.item_id}")
            bins.append(bin_)

    return PackingSummary3D(bins=bins)


def _orientation_candidates(item: Item3D) -> list[tuple[float, float, bool]]:
    candidates = [(item.length, item.width, False)]
    if item.allow_rotate and item.length != item.width:
        candidates.append((item.width, item.length, True))
    return candidates


def _strict_overlap_len(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return min(a_max, b_max) - max(a_min, b_min)

"""Step 1-2: 行先混載禁止付きの 2D 床面パッキング。"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item2D:
    """2次元パッキング対象の荷物。

    属性:
        item_id: 荷物ID。
        length: 占有長さ[mm]（x方向）。
        width: 占有幅[mm]（y方向）。
        dest: 行先ラベル（例: "X", "Y"）。
        allow_rotate: 90°回転（length/width入れ替え）を許可するか。
    """

    item_id: str
    length: float
    width: float
    dest: str
    allow_rotate: bool = True

    @property
    def area(self) -> float:
        """床面積[mm^2]を返す。"""
        return self.length * self.width


@dataclass(frozen=True)
class PlacedItem2D:
    """2D パッキング後の配置情報。"""

    item: Item2D
    x: float
    y: float
    length: float
    width: float
    rotated: bool

    @property
    def x_max(self) -> float:
        """x方向の終端座標。"""
        return self.x + self.length

    @property
    def y_max(self) -> float:
        """y方向の終端座標。"""
        return self.y + self.width

    @property
    def area(self) -> float:
        """配置後の占有面積[mm^2]。"""
        return self.length * self.width


@dataclass(frozen=True)
class _FreeRect:
    """未使用の長方形領域。"""

    x: float
    y: float
    length: float
    width: float

    @property
    def x_max(self) -> float:
        """x方向の終端座標。"""
        return self.x + self.length

    @property
    def y_max(self) -> float:
        """y方向の終端座標。"""
        return self.y + self.width

    @property
    def area(self) -> float:
        """空き領域の面積[mm^2]。"""
        return self.length * self.width


@dataclass
class Bin2D:
    """2D コンテナ（1行先専用）。"""

    capacity_length: float
    capacity_width: float
    dest: str
    placements: list[PlacedItem2D] = field(default_factory=list)
    free_rectangles: list[_FreeRect] = field(default_factory=list)

    def __post_init__(self) -> None:
        """初期空き領域を構築する。"""
        if not self.free_rectangles:
            self.free_rectangles = [
                _FreeRect(
                    x=0.0,
                    y=0.0,
                    length=self.capacity_length,
                    width=self.capacity_width,
                )
            ]

    @property
    def remaining_area(self) -> float:
        """残り面積[mm^2]を返す。"""
        used_area = sum(placement.area for placement in self.placements)
        return self.capacity_length * self.capacity_width - used_area

    def add(self, item: Item2D) -> bool:
        """荷物を1つ配置する。配置できたら True を返す。"""
        if item.dest != self.dest:
            return False

        candidate = self._find_best_candidate(item)
        if candidate is None:
            return False

        self.placements.append(candidate)
        self._split_free_rectangles(candidate)
        self._prune_free_rectangles()
        return True

    def _find_best_candidate(self, item: Item2D) -> PlacedItem2D | None:
        """Best Short Side Fit で最良候補を探す。"""
        orientations: list[tuple[float, float, bool]] = [(item.length, item.width, False)]
        if item.allow_rotate and item.length != item.width:
            orientations.append((item.width, item.length, True))

        best_score: tuple[float, float, float, int, float, float] | None = None
        best_placement: PlacedItem2D | None = None

        for free_rect in self.free_rectangles:
            for length, width, rotated in orientations:
                if length > free_rect.length or width > free_rect.width:
                    continue

                leftover_length = free_rect.length - length
                leftover_width = free_rect.width - width
                short_side_fit = min(leftover_length, leftover_width)
                long_side_fit = max(leftover_length, leftover_width)
                area_fit = free_rect.area - length * width
                rotation_penalty = 1 if rotated else 0
                score = (
                    short_side_fit,
                    long_side_fit,
                    area_fit,
                    rotation_penalty,
                    free_rect.y,
                    free_rect.x,
                )

                if best_score is None or score < best_score:
                    best_score = score
                    best_placement = PlacedItem2D(
                        item=item,
                        x=free_rect.x,
                        y=free_rect.y,
                        length=length,
                        width=width,
                        rotated=rotated,
                    )

        return best_placement

    def _split_free_rectangles(self, used: PlacedItem2D) -> None:
        """配置した矩形で空き領域を分割する。"""
        next_free_rectangles: list[_FreeRect] = []
        for free_rect in self.free_rectangles:
            if not _rectangles_overlap(
                free_rect.x,
                free_rect.y,
                free_rect.length,
                free_rect.width,
                used.x,
                used.y,
                used.length,
                used.width,
            ):
                next_free_rectangles.append(free_rect)
                continue

            if used.x > free_rect.x:
                next_free_rectangles.append(
                    _FreeRect(
                        x=free_rect.x,
                        y=free_rect.y,
                        length=used.x - free_rect.x,
                        width=free_rect.width,
                    )
                )
            if used.x_max < free_rect.x_max:
                next_free_rectangles.append(
                    _FreeRect(
                        x=used.x_max,
                        y=free_rect.y,
                        length=free_rect.x_max - used.x_max,
                        width=free_rect.width,
                    )
                )
            if used.y > free_rect.y:
                next_free_rectangles.append(
                    _FreeRect(
                        x=free_rect.x,
                        y=free_rect.y,
                        length=free_rect.length,
                        width=used.y - free_rect.y,
                    )
                )
            if used.y_max < free_rect.y_max:
                next_free_rectangles.append(
                    _FreeRect(
                        x=free_rect.x,
                        y=used.y_max,
                        length=free_rect.length,
                        width=free_rect.y_max - used.y_max,
                    )
                )

        self.free_rectangles = [
            rect for rect in next_free_rectangles if rect.length > 0 and rect.width > 0
        ]

    def _prune_free_rectangles(self) -> None:
        """包含関係にある空き領域を削除する。"""
        unique: list[_FreeRect] = []
        seen: set[tuple[float, float, float, float]] = set()
        for rect in self.free_rectangles:
            key = (rect.x, rect.y, rect.length, rect.width)
            if key in seen:
                continue
            seen.add(key)
            unique.append(rect)

        pruned: list[_FreeRect] = []
        for i, rect in enumerate(unique):
            contained = False
            for j, other in enumerate(unique):
                if i == j:
                    continue
                if _is_contained(rect, other):
                    contained = True
                    break
            if not contained:
                pruned.append(rect)

        self.free_rectangles = pruned


@dataclass(frozen=True)
class PackingSummary2D:
    """2D パッキング結果の要約。"""

    bins: list[Bin2D]

    @property
    def bin_count(self) -> int:
        """使用 Bin 数を返す。"""
        return len(self.bins)

    @property
    def total_unused_area(self) -> float:
        """全 Bin の未使用面積合計[mm^2]を返す。"""
        return sum(bin_.remaining_area for bin_ in self.bins)


def pack_2d_by_destination_ffd(
    items: list[Item2D], bin_length: float, bin_width: float
) -> PackingSummary2D:
    """行先ごとの First-Fit Decreasing で 2D パッキングを実行する。"""
    if bin_length <= 0 or bin_width <= 0:
        raise ValueError("bin_length and bin_width must be positive")

    for item in items:
        if item.length <= 0 or item.width <= 0:
            raise ValueError(f"item dimensions must be positive: {item.item_id}")
        if not item.dest:
            raise ValueError(f"item.dest must be non-empty: {item.item_id}")

        fits_without_rotation = item.length <= bin_length and item.width <= bin_width
        fits_with_rotation = (
            item.allow_rotate and item.width <= bin_length and item.length <= bin_width
        )
        if not (fits_without_rotation or fits_with_rotation):
            raise ValueError(f"item cannot fit in any bin: {item.item_id}")

    bins: list[Bin2D] = []

    # 再現性のため、行先→面積降順→長辺降順→ID の順で並べる。
    ordered = sorted(
        items,
        key=lambda i: (i.dest, -i.area, -max(i.length, i.width), i.item_id),
    )

    for item in ordered:
        placed = False
        for bin_ in bins:
            if bin_.dest != item.dest:
                continue
            if bin_.add(item):
                placed = True
                break

        if not placed:
            new_bin = Bin2D(capacity_length=bin_length, capacity_width=bin_width, dest=item.dest)
            if not new_bin.add(item):
                raise ValueError(f"item cannot fit in any bin: {item.item_id}")
            bins.append(new_bin)

    return PackingSummary2D(bins=bins)


def _rectangles_overlap(
    ax: float,
    ay: float,
    al: float,
    aw: float,
    bx: float,
    by: float,
    bl: float,
    bw: float,
) -> bool:
    """2矩形が内部で重なるか判定する（接触のみは重なり扱いしない）。"""
    return ax < bx + bl and ax + al > bx and ay < by + bw and ay + aw > by


def _is_contained(inner: _FreeRect, outer: _FreeRect) -> bool:
    """inner が outer に完全内包されるか判定する。"""
    return (
        inner.x >= outer.x
        and inner.y >= outer.y
        and inner.x_max <= outer.x_max
        and inner.y_max <= outer.y_max
    )

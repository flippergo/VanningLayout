"""Step 1-1: 行先混載禁止付きの 1D ビンパッキング。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item1D:
    """1次元パッキング対象の荷物。

    属性:
        item_id: 荷物ID。
        length: 占有長さ[mm]。正の値のみ許可。
        dest: 行先ラベル（例: "X", "Y"）。
    """

    item_id: str
    length: float
    dest: str


@dataclass
class Bin1D:
    """1D コンテナ（1行先専用）。

    1つの Bin には同一行先の荷物のみを載せる。
    """

    capacity: float
    dest: str
    items: list[Item1D]
    used_length: float = 0.0

    @property
    def remaining_length(self) -> float:
        """残り長さ[mm]を返す。"""
        return self.capacity - self.used_length

    def can_fit(self, item: Item1D) -> bool:
        """荷物がこの Bin に入るか判定する。"""
        return item.dest == self.dest and item.length <= self.remaining_length

    def add(self, item: Item1D) -> None:
        """荷物を Bin に追加する。追加不可なら例外を送出する。"""
        if not self.can_fit(item):
            raise ValueError("item cannot be packed into this bin")
        self.items.append(item)
        self.used_length += item.length


@dataclass(frozen=True)
class PackingSummary:
    """1D パッキング結果の要約。"""

    bins: list[Bin1D]

    @property
    def bin_count(self) -> int:
        """使用 Bin 数を返す。"""
        return len(self.bins)

    @property
    def total_unused_length(self) -> float:
        """全 Bin の未使用長さ合計[mm]を返す。"""
        return sum(bin_.remaining_length for bin_ in self.bins)


def pack_1d_by_destination_ffd(items: list[Item1D], bin_capacity: float) -> PackingSummary:
    """First-Fit Decreasing で 1D パッキングを実行する。

    仕様:
      - 1つの Bin に複数行先を混載しない。
      - 各荷物は bin_capacity 以下でなければならない。

    注意:
      - 近似解法であり、常に大域最適を保証するものではない。
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

    # 再現性のため、行先→長さ降順→ID の順で並べる。
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

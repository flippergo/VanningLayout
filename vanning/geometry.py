from dataclasses import dataclass


@dataclass(frozen=True)
class BoxPlacement:
    """箱の配置を表す。

    (x, y, z) は「左・手前・下」の角の座標、
    (l, w, h) はその向きでの長さ・幅・高さ。
    """

    x: float
    y: float
    z: float
    l: float
    w: float
    h: float

    @property
    def x_max(self) -> float:
        """箱が x 方向にどこまで届くか（右端）"""
        return self.x + self.l

    @property
    def y_max(self) -> float:
        """箱が y 方向にどこまで届くか（奥側の端）"""
        return self.y + self.w

    @property
    def z_max(self) -> float:
        """箱が z 方向にどこまで届くか（上端）"""
        return self.z + self.h


@dataclass(frozen=True)
class Container:
    """コンテナの内寸（長さ・幅・高さ）"""

    l: float
    w: float
    h: float


def oriented_size(length: float, width: float, height: float, yaw_deg: int) -> tuple[float, float, float]:
    """箱の向き（0°/90°）を反映した寸法を返す。

    0°: (length, width, height) のまま
    90°: length と width を入れ替える
    """
    if yaw_deg == 0:
        return (length, width, height)
    if yaw_deg == 90:
        return (width, length, height)
    raise ValueError("yaw_deg must be either 0 or 90")


def _strict_interval_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> bool:
    """2区間が「内部で」重なるかを判定する。

    端点が一致するだけ（面接触・辺接触）は重なりとみなさない。
    """
    return max(a_min, b_min) < min(a_max, b_max)


def boxes_collide(a: BoxPlacement, b: BoxPlacement) -> bool:
    """2つの箱が衝突しているかを判定する。

    x/y/z の3方向すべてで内部重なりがあるときだけ衝突とする。
    どれか1方向でも重なっていなければ衝突ではない。
    """
    return (
        # 3軸すべてで重なっているかを論理積で判定する
        _strict_interval_overlap(a.x, a.x_max, b.x, b.x_max)
        and _strict_interval_overlap(a.y, a.y_max, b.y, b.y_max)
        and _strict_interval_overlap(a.z, a.z_max, b.z, b.z_max)
    )


def is_inside_container(box: BoxPlacement, container: Container) -> bool:
    """箱がコンテナ内に完全に入っているかを判定する。

    境界ちょうど（例: x_max == container.l）は許容する。
    """
    return (
        # まずは左・手前・下にはみ出していないこと
        box.x >= 0
        and box.y >= 0
        and box.z >= 0
        # 次に右・奥・上にはみ出していないこと
        and box.x_max <= container.l
        and box.y_max <= container.w
        and box.z_max <= container.h
    )

"""バンニング問題で共通利用する定数・補助関数。"""

from vanning.geometry import BoxPlacement, Container, oriented_size


# 20ftコンテナの内寸 [mm]
CONTAINER_20FT = Container(l=5898, w=2352, h=2393)

# 箱タイプごとの外形寸法 [mm]（長さ, 幅, 高さ）
BOX_DIMS: dict[str, tuple[int, int, int]] = {
    "A": (1400, 1000, 800),
    "B": (1200, 900, 700),
    "C": (800, 600, 600),
}


def box_size(box_type: str, yaw_deg: int) -> tuple[float, float, float]:
    """箱タイプと向き(0°/90°)から、実際に使う寸法[mm]を返す。"""
    if yaw_deg not in {0, 90}:
        raise ValueError(f"yaw_deg は 0 または 90 を指定してください: {yaw_deg}")

    key = box_type.upper()
    if key not in BOX_DIMS:
        raise ValueError(f"未知の box_type です: {box_type}")

    length, width, height = BOX_DIMS[key]
    return oriented_size(length, width, height, yaw_deg)


def place_box(box_type: str, x: float, y: float, z: float, yaw_deg: int) -> BoxPlacement:
    """箱タイプ・座標[mm]・向き(0°/90°)から BoxPlacement を生成する。"""
    l, w, h = box_size(box_type, yaw_deg)
    return BoxPlacement(x=x, y=y, z=z, l=l, w=w, h=h)

"""バンニング問題で共通利用する定数・補助関数。"""

from vanning.geometry import BoxPlacement, Container, oriented_size


# 20ftコンテナの内寸 [mm]
CONTAINER_20FT = Container(l=5898, w=2352, h=2393)

# 箱タイプごとの外形寸法 [mm]（長さ, 幅, 高さ）
BOX_DIMS = {
    "A": (1400, 1000, 800),
    "B": (1200, 900, 700),
    "C": (800, 600, 600),
}


def box_size(box_type: str, yaw_deg: int) -> tuple[float, float, float]:
    """箱タイプと向き(0°/90°)から、実際に使う寸法を返す。"""
    key = box_type.upper()
    if key not in BOX_DIMS:
        raise ValueError(f"未知の box_type です: {box_type}")
    length, width, height = BOX_DIMS[key]
    return oriented_size(length, width, height, yaw_deg)


def place_box(box_type: str, x: float, y: float, z: float, yaw_deg: int) -> BoxPlacement:
    """箱タイプ・座標・向きから BoxPlacement を生成する。"""
    l, w, h = box_size(box_type, yaw_deg)
    return BoxPlacement(x=x, y=y, z=z, l=l, w=w, h=h)

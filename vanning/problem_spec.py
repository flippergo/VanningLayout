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

# 問題インスタンスで使う箱数（IDレンジ）
REALDATA_BOX_COUNTS: dict[str, int] = {
    "A": 30,
    "B": 30,
    "C": 20,
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


def realdata_box_ids() -> list[str]:
    """問題インスタンスで使う箱ID一覧を返す。"""
    ids: list[str] = []
    for box_type, count in REALDATA_BOX_COUNTS.items():
        for idx in range(1, count + 1):
            ids.append(f"{box_type}{idx:02d}")
    return ids


def box_type_from_id(box_id: str) -> str:
    """箱IDから箱タイプ（A/B/C）を返す。"""
    if len(box_id) < 3:
        raise ValueError(f"不正な箱IDです: {box_id}")
    box_type = box_id[0].upper()
    if box_type not in BOX_DIMS:
        raise ValueError(f"未知の箱タイプです: {box_id}")
    return box_type


def destination_for_box_id(box_id: str) -> str:
    """箱IDに対応する行先(X/Y)を返す。"""
    box_type = box_type_from_id(box_id)
    try:
        serial = int(box_id[1:])
    except ValueError as exc:
        raise ValueError(f"不正な箱IDです: {box_id}") from exc

    count = REALDATA_BOX_COUNTS[box_type]
    if serial < 1 or serial > count:
        raise ValueError(f"箱IDの連番が範囲外です: {box_id}")

    if box_type in {"A", "B"}:
        return "X" if serial <= 15 else "Y"
    return "X" if serial <= 10 else "Y"


def build_step1_2d_realdata_items(allow_rotate: bool = True) -> list["Item2D"]:
    """Step1-2D 用に、本番データ80箱を Item2D の配列へ変換する。"""
    # 循環参照を避けるため、必要時に import する。
    from vanning.step1_2d import Item2D

    items: list[Item2D] = []
    for box_id in realdata_box_ids():
        box_type = box_type_from_id(box_id)
        length, width, _ = BOX_DIMS[box_type]
        items.append(
            Item2D(
                item_id=box_id,
                length=float(length),
                width=float(width),
                dest=destination_for_box_id(box_id),
                allow_rotate=allow_rotate,
            )
        )
    return items

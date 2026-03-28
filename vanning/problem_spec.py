"""バンニング問題で共通利用する定数・補助関数。"""

from vanning.geometry import BoxPlacement, Container, oriented_size


# 20ftコンテナの内寸 [mm]
CONTAINER_20FT = Container(l=5898, w=2352, h=2393)
CONTAINER_20FT_MAX_PAYLOAD_KG = 12000.0
CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM = 300.0
STEP5_MIN_SUPPORT_AREA_RATIO = 0.8

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

REALDATA_BOX_WEIGHTS_KG: dict[str, float] = {
    "A01": 420.0,
    "A02": 380.0,
    "A03": 310.0,
    "A04": 450.0,
    "A05": 275.0,
    "A06": 360.0,
    "A07": 330.0,
    "A08": 290.0,
    "A09": 405.0,
    "A10": 315.0,
    "A11": 260.0,
    "A12": 440.0,
    "A13": 355.0,
    "A14": 300.0,
    "A15": 395.0,
    "A16": 285.0,
    "A17": 410.0,
    "A18": 340.0,
    "A19": 270.0,
    "A20": 365.0,
    "A21": 320.0,
    "A22": 295.0,
    "A23": 430.0,
    "A24": 305.0,
    "A25": 280.0,
    "A26": 370.0,
    "A27": 335.0,
    "A28": 255.0,
    "A29": 390.0,
    "A30": 345.0,
    "B01": 260.0,
    "B02": 240.0,
    "B03": 310.0,
    "B04": 180.0,
    "B05": 205.0,
    "B06": 295.0,
    "B07": 225.0,
    "B08": 270.0,
    "B09": 190.0,
    "B10": 330.0,
    "B11": 250.0,
    "B12": 210.0,
    "B13": 285.0,
    "B14": 235.0,
    "B15": 320.0,
    "B16": 175.0,
    "B17": 265.0,
    "B18": 200.0,
    "B19": 305.0,
    "B20": 245.0,
    "B21": 215.0,
    "B22": 290.0,
    "B23": 230.0,
    "B24": 340.0,
    "B25": 185.0,
    "B26": 275.0,
    "B27": 220.0,
    "B28": 315.0,
    "B29": 255.0,
    "B30": 195.0,
    "C01": 150.0,
    "C02": 120.0,
    "C03": 180.0,
    "C04": 90.0,
    "C05": 110.0,
    "C06": 160.0,
    "C07": 130.0,
    "C08": 170.0,
    "C09": 100.0,
    "C10": 190.0,
    "C11": 140.0,
    "C12": 115.0,
    "C13": 165.0,
    "C14": 125.0,
    "C15": 200.0,
    "C16": 85.0,
    "C17": 155.0,
    "C18": 105.0,
    "C19": 175.0,
    "C20": 135.0,
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


def weight_for_box_id(box_id: str) -> float:
    """箱IDに対応する重量[kg]を返す。"""
    if box_id not in REALDATA_BOX_WEIGHTS_KG:
        raise ValueError(f"重量データがありません: {box_id}")
    return REALDATA_BOX_WEIGHTS_KG[box_id]


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


def build_step2_3d_realdata_items(allow_rotate: bool = True) -> list["Item3D"]:
    """Build the real-data box set as Step2 3D items."""
    from vanning.step2_3d import Item3D

    items: list[Item3D] = []
    for box_id in realdata_box_ids():
        box_type = box_type_from_id(box_id)
        length, width, height = BOX_DIMS[box_type]
        items.append(
            Item3D(
                item_id=box_id,
                length=float(length),
                width=float(width),
                height=float(height),
                dest=destination_for_box_id(box_id),
                allow_rotate=allow_rotate,
            )
        )
    return items


def build_step3_weighted_realdata_items(allow_rotate: bool = True) -> list["WeightedItem3D"]:
    """Step3 用に、本番データ80箱を重量つき3Dアイテムへ変換する。"""
    from vanning.step3_weighted_3d import WeightedItem3D

    items: list[WeightedItem3D] = []
    for box_id in realdata_box_ids():
        box_type = box_type_from_id(box_id)
        length, width, height = BOX_DIMS[box_type]
        items.append(
            WeightedItem3D(
                item_id=box_id,
                length=float(length),
                width=float(width),
                height=float(height),
                weight_kg=weight_for_box_id(box_id),
                dest=destination_for_box_id(box_id),
                allow_rotate=allow_rotate,
            )
        )
    return items

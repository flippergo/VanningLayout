"""SVG visualization helpers for Step2 3D packing results."""

from html import escape
from math import cos, radians, sin
from pathlib import Path

from vanning.step2_3d import Bin3D, PackingSummary3D, PlacedItem3D


_BOX_COLORS: dict[str, str] = {
    "A": "#4E79A7",
    "B": "#F28E2B",
    "C": "#59A14F",
}
_DEFAULT_COLOR = "#BAB0AC"
_ISO_COS = cos(radians(30))
_ISO_SIN = sin(radians(30))


def _box_type_from_item_id(item_id: str) -> str:
    if not item_id:
        return "?"
    return item_id[0].upper()


def _fill_color(placement: PlacedItem3D) -> str:
    return _BOX_COLORS.get(_box_type_from_item_id(placement.item.item_id), _DEFAULT_COLOR)


def _shade_color(hex_color: str, factor: float) -> str:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return f"#{hex_color}"

    parts = [int(hex_color[idx : idx + 2], 16) for idx in (0, 2, 4)]
    adjusted = [max(0, min(255, int(round(channel * factor)))) for channel in parts]
    return "#" + "".join(f"{channel:02X}" for channel in adjusted)


def _iso_project(x: float, y: float, z: float) -> tuple[float, float]:
    return ((x - y) * _ISO_COS, (x + y) * _ISO_SIN - z)


def _iso_polygon(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def render_bin_isometric_svg(
    bin_: Bin3D,
    *,
    title: str | None = None,
    max_width_px: int = 760,
    max_height_px: int = 520,
    margin_px: int = 32,
) -> str:
    """Render one 3D bin as an isometric SVG view."""
    if max_width_px <= 0 or max_height_px <= 0:
        raise ValueError("max_width_px and max_height_px must be positive")
    if margin_px < 0:
        raise ValueError("margin_px must be non-negative")

    container_points = [
        _iso_project(x, y, z)
        for x in (0.0, bin_.container.l)
        for y in (0.0, bin_.container.w)
        for z in (0.0, bin_.container.h)
    ]
    min_x = min(point[0] for point in container_points)
    max_x = max(point[0] for point in container_points)
    min_y = min(point[1] for point in container_points)
    max_y = max(point[1] for point in container_points)

    raw_width = max_x - min_x
    raw_height = max_y - min_y
    scale = min(max_width_px / raw_width, max_height_px / raw_height)

    title_height = 34
    footer_height = 54
    svg_width = int(round(raw_width * scale + margin_px * 2))
    svg_height = int(round(raw_height * scale + margin_px * 2 + title_height + footer_height))
    offset_x = margin_px - min_x * scale
    offset_y = margin_px + title_height - min_y * scale

    def point(x: float, y: float, z: float) -> tuple[float, float]:
        px, py = _iso_project(x, y, z)
        return (offset_x + px * scale, offset_y + py * scale)

    def box_vertices(placement: PlacedItem3D) -> dict[str, tuple[float, float]]:
        x0 = placement.x
        x1 = placement.x + placement.length
        y0 = placement.y
        y1 = placement.y + placement.width
        z0 = placement.z
        z1 = placement.z + placement.height
        return {
            "000": point(x0, y0, z0),
            "100": point(x1, y0, z0),
            "010": point(x0, y1, z0),
            "110": point(x1, y1, z0),
            "001": point(x0, y0, z1),
            "101": point(x1, y0, z1),
            "011": point(x0, y1, z1),
            "111": point(x1, y1, z1),
        }

    title_text = title or f"Dest {bin_.dest} isometric layout ({len(bin_.placements)} items)"
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
            f'height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">'
        ),
        '<rect x="0" y="0" width="100%" height="100%" fill="#F8F9FB"/>',
        f'<text x="{margin_px}" y="{margin_px + 6}" font-size="18" '
        'font-family="Segoe UI, sans-serif" fill="#1F2937">'
        f"{escape(title_text)}</text>",
    ]

    container = {
        "000": point(0.0, 0.0, 0.0),
        "100": point(bin_.container.l, 0.0, 0.0),
        "010": point(0.0, bin_.container.w, 0.0),
        "110": point(bin_.container.l, bin_.container.w, 0.0),
        "001": point(0.0, 0.0, bin_.container.h),
        "1001": point(bin_.container.l, 0.0, bin_.container.h),
        "0101": point(0.0, bin_.container.w, bin_.container.h),
        "1101": point(bin_.container.l, bin_.container.w, bin_.container.h),
    }
    container_edges = [
        ("000", "100"),
        ("000", "010"),
        ("000", "001"),
        ("100", "110"),
        ("100", "1001"),
        ("010", "110"),
        ("010", "0101"),
        ("110", "1101"),
        ("001", "1001"),
        ("001", "0101"),
        ("1001", "1101"),
        ("0101", "1101"),
    ]

    for start, end in container_edges:
        sx, sy = container[start]
        ex, ey = container[end]
        lines.append(
            f'<line x1="{sx:.2f}" y1="{sy:.2f}" x2="{ex:.2f}" y2="{ey:.2f}" '
            'stroke="#CBD5E1" stroke-width="1.5"/>'
        )

    for placement in sorted(bin_.placements, key=lambda p: (p.x + p.y + p.z, p.z, p.y, p.x)):
        vertices = box_vertices(placement)
        base_color = _fill_color(placement)
        top_face = [vertices["001"], vertices["101"], vertices["111"], vertices["011"]]
        x_face = [vertices["000"], vertices["100"], vertices["101"], vertices["001"]]
        y_face = [vertices["000"], vertices["010"], vertices["011"], vertices["001"]]
        label_x = sum(vertex[0] for vertex in top_face) / 4
        label_y = sum(vertex[1] for vertex in top_face) / 4
        label = placement.item.item_id + (" (R)" if placement.rotated else "")

        lines.extend(
            [
                f'<polygon points="{_iso_polygon(y_face)}" fill="{_shade_color(base_color, 0.82)}" '
                'stroke="#111827" stroke-width="1"/>',
                f'<polygon points="{_iso_polygon(x_face)}" fill="{_shade_color(base_color, 0.94)}" '
                'stroke="#111827" stroke-width="1"/>',
                f'<polygon points="{_iso_polygon(top_face)}" fill="{_shade_color(base_color, 1.10)}" '
                'stroke="#111827" stroke-width="1"/>',
                f'<text x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="middle" '
                'dominant-baseline="middle" font-size="10" font-family="Consolas, monospace" '
                f'fill="#111827">{escape(label)}</text>',
            ]
        )

    utilization = 1.0 - (bin_.remaining_volume / (bin_.container.l * bin_.container.w * bin_.container.h))
    footer_y = svg_height - margin_px
    lines.extend(
        [
            f'<text x="{margin_px}" y="{footer_y - 18}" font-size="13" '
            'font-family="Segoe UI, sans-serif" fill="#374151">'
            f'Dest: {escape(bin_.dest)}  Items: {len(bin_.placements)}  Volume utilization: {utilization:.1%}'
            "</text>",
            f'<text x="{margin_px}" y="{footer_y}" font-size="12" '
            'font-family="Consolas, monospace" fill="#6B7280">'
            f"L={int(bin_.container.l)}mm W={int(bin_.container.w)}mm H={int(bin_.container.h)}mm"
            "</text>",
            "</svg>",
        ]
    )
    return "\n".join(lines)


def render_bin_orthographic_svg(
    bin_: Bin3D,
    *,
    title: str | None = None,
    max_panel_px: int = 420,
    margin_px: int = 28,
    gap_px: int = 30,
) -> str:
    """Render one 3D bin as top/front/side orthographic SVG panels."""
    if max_panel_px <= 0:
        raise ValueError("max_panel_px must be positive")
    if margin_px < 0:
        raise ValueError("margin_px must be non-negative")
    if gap_px < 0:
        raise ValueError("gap_px must be non-negative")

    scale = min(
        max_panel_px / bin_.container.l,
        max_panel_px / bin_.container.w,
        max_panel_px / bin_.container.h,
    )
    top_w = int(round(bin_.container.l * scale))
    top_h = int(round(bin_.container.w * scale))
    front_w = int(round(bin_.container.l * scale))
    front_h = int(round(bin_.container.h * scale))
    side_w = int(round(bin_.container.w * scale))
    side_h = int(round(bin_.container.h * scale))

    title_height = 30
    footer_height = 58
    label_gap = 18
    row_height = max(top_h, front_h)
    svg_width = margin_px * 2 + top_w + gap_px + side_w
    svg_height = margin_px * 2 + title_height + label_gap * 2 + row_height + gap_px + front_h + footer_height

    top_left_x = margin_px
    top_left_y = margin_px + title_height + label_gap
    side_left_x = top_left_x + top_w + gap_px
    side_left_y = top_left_y
    front_left_x = margin_px
    front_left_y = top_left_y + row_height + gap_px + label_gap

    top_title = "Top (X-Y)"
    side_title = "Side (Y-Z)"
    front_title = "Front (X-Z)"
    title_text = title or f"Dest {bin_.dest} 3D layout ({len(bin_.placements)} items)"

    def top_x(mm: float) -> float:
        return top_left_x + mm * scale

    def top_y(mm: float) -> float:
        return top_left_y + (bin_.container.w - mm) * scale

    def side_x(mm: float) -> float:
        return side_left_x + mm * scale

    def side_y(mm: float) -> float:
        return side_left_y + (bin_.container.h - mm) * scale

    def front_x(mm: float) -> float:
        return front_left_x + mm * scale

    def front_y(mm: float) -> float:
        return front_left_y + (bin_.container.h - mm) * scale

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
            f'height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">'
        ),
        '<rect x="0" y="0" width="100%" height="100%" fill="#F8F9FB"/>',
        f'<text x="{margin_px}" y="{margin_px + 6}" font-size="18" '
        'font-family="Segoe UI, sans-serif" fill="#1F2937">'
        f"{escape(title_text)}</text>",
        f'<text x="{top_left_x}" y="{top_left_y - 8}" font-size="13" font-family="Segoe UI, sans-serif" fill="#374151">{top_title}</text>',
        f'<text x="{side_left_x}" y="{side_left_y - 8}" font-size="13" font-family="Segoe UI, sans-serif" fill="#374151">{side_title}</text>',
        f'<text x="{front_left_x}" y="{front_left_y - 8}" font-size="13" font-family="Segoe UI, sans-serif" fill="#374151">{front_title}</text>',
        (
            f'<rect x="{top_left_x}" y="{top_left_y}" width="{top_w}" height="{top_h}" '
            'fill="#FFFFFF" stroke="#1F2937" stroke-width="2"/>'
        ),
        (
            f'<rect x="{side_left_x}" y="{side_left_y}" width="{side_w}" height="{side_h}" '
            'fill="#FFFFFF" stroke="#1F2937" stroke-width="2"/>'
        ),
        (
            f'<rect x="{front_left_x}" y="{front_left_y}" width="{front_w}" height="{front_h}" '
            'fill="#FFFFFF" stroke="#1F2937" stroke-width="2"/>'
        ),
    ]

    for placement in sorted(bin_.placements, key=lambda p: (p.z, p.y, p.x, p.item.item_id)):
        label = placement.item.item_id + (" (R)" if placement.rotated else "")
        fill = _fill_color(placement)

        tx = top_x(placement.x)
        ty = top_y(placement.y + placement.width)
        tw = placement.length * scale
        th = placement.width * scale
        lines.append(
            (
                f'<rect x="{tx:.2f}" y="{ty:.2f}" width="{tw:.2f}" height="{th:.2f}" '
                f'fill="{fill}" fill-opacity="0.78" stroke="#111827" stroke-width="1"/>'
            )
        )
        lines.append(
            (
                f'<text x="{tx + tw / 2:.2f}" y="{ty + th / 2:.2f}" text-anchor="middle" '
                'dominant-baseline="middle" font-size="10" font-family="Consolas, monospace" '
                f'fill="#111827">{escape(label)}</text>'
            )
        )

    for placement in sorted(bin_.placements, key=lambda p: (p.x, p.z, p.y, p.item.item_id)):
        label = placement.item.item_id
        fill = _fill_color(placement)

        sx = side_x(placement.y)
        sy = side_y(placement.z + placement.height)
        sw = placement.width * scale
        sh = placement.height * scale
        lines.append(
            (
                f'<rect x="{sx:.2f}" y="{sy:.2f}" width="{sw:.2f}" height="{sh:.2f}" '
                f'fill="{fill}" fill-opacity="0.72" stroke="#111827" stroke-width="1"/>'
            )
        )
        lines.append(
            (
                f'<text x="{sx + sw / 2:.2f}" y="{sy + sh / 2:.2f}" text-anchor="middle" '
                'dominant-baseline="middle" font-size="10" font-family="Consolas, monospace" '
                f'fill="#111827">{escape(label)}</text>'
            )
        )

    for placement in sorted(bin_.placements, key=lambda p: (p.y, p.z, p.x, p.item.item_id)):
        label = placement.item.item_id
        fill = _fill_color(placement)

        fx = front_x(placement.x)
        fy = front_y(placement.z + placement.height)
        fw = placement.length * scale
        fh = placement.height * scale
        lines.append(
            (
                f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{fw:.2f}" height="{fh:.2f}" '
                f'fill="{fill}" fill-opacity="0.72" stroke="#111827" stroke-width="1"/>'
            )
        )
        lines.append(
            (
                f'<text x="{fx + fw / 2:.2f}" y="{fy + fh / 2:.2f}" text-anchor="middle" '
                'dominant-baseline="middle" font-size="10" font-family="Consolas, monospace" '
                f'fill="#111827">{escape(label)}</text>'
            )
        )

    utilization = 1.0 - (bin_.remaining_volume / (bin_.container.l * bin_.container.w * bin_.container.h))
    footer_y = svg_height - margin_px
    lines.extend(
        [
            f'<text x="{margin_px}" y="{footer_y - 18}" font-size="13" '
            'font-family="Segoe UI, sans-serif" fill="#374151">'
            f'Dest: {escape(bin_.dest)}  Items: {len(bin_.placements)}  Volume utilization: {utilization:.1%}'
            "</text>",
            f'<text x="{margin_px}" y="{footer_y}" font-size="12" '
            'font-family="Consolas, monospace" fill="#6B7280">'
            f"L={int(bin_.container.l)}mm W={int(bin_.container.w)}mm H={int(bin_.container.h)}mm"
            "</text>",
            "</svg>",
        ]
    )
    return "\n".join(lines)


def save_packing_summary_svgs(
    summary: PackingSummary3D,
    output_dir: str | Path,
    *,
    prefix: str = "step2_3d",
) -> list[Path]:
    """Save one orthographic SVG per bin in the packing summary."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        file_path = out_dir / f"{prefix}_bin{idx:02d}_{bin_.dest}.svg"
        svg = render_bin_orthographic_svg(
            bin_,
            title=f"Bin {idx:02d} (Dest {bin_.dest})",
        )
        file_path.write_text(svg, encoding="utf-8")
        generated.append(file_path)

    return generated


def save_packing_summary_isometric_svgs(
    summary: PackingSummary3D,
    output_dir: str | Path,
    *,
    prefix: str = "step2_3d_iso",
) -> list[Path]:
    """Save one isometric SVG per bin in the packing summary."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        file_path = out_dir / f"{prefix}_bin{idx:02d}_{bin_.dest}.svg"
        svg = render_bin_isometric_svg(
            bin_,
            title=f"Bin {idx:02d} (Dest {bin_.dest}) isometric",
        )
        file_path.write_text(svg, encoding="utf-8")
        generated.append(file_path)

    return generated

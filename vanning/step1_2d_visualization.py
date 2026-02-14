"""Step1-2D パッキング結果の可視化（SVG 出力）。"""

from html import escape
from pathlib import Path

from vanning.step1_2d import Bin2D, PackingSummary2D, PlacedItem2D


_BOX_COLORS: dict[str, str] = {
    "A": "#4E79A7",
    "B": "#F28E2B",
    "C": "#59A14F",
}
_DEFAULT_COLOR = "#BAB0AC"


def _box_type_from_item_id(item_id: str) -> str:
    if not item_id:
        return "?"
    return item_id[0].upper()


def _fill_color(placement: PlacedItem2D) -> str:
    return _BOX_COLORS.get(_box_type_from_item_id(placement.item.item_id), _DEFAULT_COLOR)


def render_bin_layout_svg(
    bin_: Bin2D,
    *,
    title: str | None = None,
    pixels_per_mm: float = 0.09,
    margin_px: int = 36,
) -> str:
    """1コンテナ分の2D床面レイアウトを SVG 文字列として返す。"""
    if pixels_per_mm <= 0:
        raise ValueError("pixels_per_mm must be positive")
    if margin_px < 0:
        raise ValueError("margin_px must be non-negative")

    panel_length = int(round(bin_.capacity_length * pixels_per_mm))
    panel_width = int(round(bin_.capacity_width * pixels_per_mm))
    footer_height = 56
    svg_width = panel_length + margin_px * 2
    svg_height = panel_width + margin_px * 2 + footer_height

    def to_x(mm: float) -> float:
        return margin_px + mm * pixels_per_mm

    # SVG の y は上向きに増えるため、床面座標(y=0)を下側に合わせる。
    def to_y(mm: float) -> float:
        return margin_px + (bin_.capacity_width - mm) * pixels_per_mm

    top = margin_px
    left = margin_px
    right = left + panel_length
    bottom = top + panel_width
    title_text = title or f"Dest {bin_.dest} layout ({len(bin_.placements)} items)"

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
            f'height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">'
        ),
        '<rect x="0" y="0" width="100%" height="100%" fill="#F8F9FB"/>',
        f'<text x="{left}" y="22" font-size="16" font-family="Segoe UI, sans-serif" '
        f'fill="#1F2937">{escape(title_text)}</text>',
        (
            f'<rect x="{left}" y="{top}" width="{panel_length}" height="{panel_width}" '
            'fill="#FFFFFF" stroke="#1F2937" stroke-width="2"/>'
        ),
    ]

    for placement in sorted(bin_.placements, key=lambda p: (p.y, p.x, p.item.item_id)):
        x = to_x(placement.x)
        y = to_y(placement.y + placement.width)
        w = placement.length * pixels_per_mm
        h = placement.width * pixels_per_mm
        label = placement.item.item_id
        if placement.rotated:
            label += " (R)"

        lines.append(
            (
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                f'fill="{_fill_color(placement)}" fill-opacity="0.88" '
                'stroke="#111827" stroke-width="1"/>'
            )
        )
        lines.append(
            f'<text x="{x + w / 2:.2f}" y="{y + h / 2:.2f}" text-anchor="middle" '
            'dominant-baseline="middle" font-size="10" font-family="Consolas, monospace" '
            f'fill="#111827">{escape(label)}</text>'
        )

    util = 1.0 - (bin_.remaining_area / (bin_.capacity_length * bin_.capacity_width))
    lines.extend(
        [
            f'<text x="{left}" y="{bottom + 24}" font-size="13" '
            'font-family="Segoe UI, sans-serif" fill="#374151">'
            f'Dest: {escape(bin_.dest)}  Items: {len(bin_.placements)}  Utilization: {util:.1%}'
            "</text>",
            f'<text x="{right}" y="{bottom + 24}" text-anchor="end" font-size="12" '
            'font-family="Consolas, monospace" fill="#6B7280">'
            f"L={int(bin_.capacity_length)}mm W={int(bin_.capacity_width)}mm"
            "</text>",
            "</svg>",
        ]
    )
    return "\n".join(lines)


def save_packing_summary_svgs(
    summary: PackingSummary2D,
    output_dir: str | Path,
    *,
    prefix: str = "step1_2d_realdata",
    pixels_per_mm: float = 0.09,
) -> list[Path]:
    """パッキング結果をコンテナごとに SVG ファイルとして保存する。"""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        file_path = out_dir / f"{prefix}_bin{idx:02d}_{bin_.dest}.svg"
        svg = render_bin_layout_svg(
            bin_,
            title=f"Bin {idx:02d} (Dest {bin_.dest})",
            pixels_per_mm=pixels_per_mm,
        )
        file_path.write_text(svg, encoding="utf-8")
        generated.append(file_path)

    return generated

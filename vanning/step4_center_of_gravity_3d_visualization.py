"""SVG visualization helpers for Step4 center-of-gravity constrained 3D packing."""

from html import escape
from pathlib import Path

from vanning.step3_weighted_3d_visualization import (
    render_weighted_bin_isometric_svg,
    render_weighted_bin_orthographic_svg,
)
from vanning.step4_center_of_gravity_3d import (
    CenterBalancedBin3D,
    CenterBalancedPackingSummary3D,
    center_offset_distance_mm,
    horizontal_center_of_gravity,
)


def render_center_balanced_bin_orthographic_svg(
    bin_: CenterBalancedBin3D, *, title: str | None = None
) -> str:
    """Render one Step4 bin as top/front/side orthographic SVG panels."""
    return render_weighted_bin_orthographic_svg(
        bin_,
        title=title
        or (
            f"Dest {bin_.dest} center-balanced layout "
            f"({len(bin_.placements)} items, offset {bin_.center_offset_mm:.1f} mm)"
        ),
    )


def render_center_balanced_bin_isometric_svg(
    bin_: CenterBalancedBin3D, *, title: str | None = None
) -> str:
    """Render one Step4 bin as an isometric SVG view."""
    return render_weighted_bin_isometric_svg(
        bin_,
        title=title
        or (
            f"Dest {bin_.dest} center-balanced isometric "
            f"({len(bin_.placements)} items, offset {bin_.center_offset_mm:.1f} mm)"
        ),
    )


def render_center_balance_topdown_svg(
    bin_: CenterBalancedBin3D,
    *,
    title: str | None = None,
    max_panel_px: int = 560,
    margin_px: int = 28,
) -> str:
    """Render a top-down SVG showing the center point, limit circle, and actual gravity center."""
    if max_panel_px <= 0:
        raise ValueError("max_panel_px must be positive")
    if margin_px < 0:
        raise ValueError("margin_px must be non-negative")

    scale = min(max_panel_px / bin_.container.l, max_panel_px / bin_.container.w)
    panel_w = int(round(bin_.container.l * scale))
    panel_h = int(round(bin_.container.w * scale))
    title_height = 30
    footer_height = 76
    svg_width = margin_px * 2 + panel_w
    svg_height = margin_px * 2 + title_height + panel_h + footer_height
    panel_left = margin_px
    panel_top = margin_px + title_height

    def screen_x(mm: float) -> float:
        return panel_left + mm * scale

    def screen_y(mm: float) -> float:
        return panel_top + (bin_.container.w - mm) * scale

    center_x = bin_.container.l / 2
    center_y = bin_.container.w / 2
    cg_x, cg_y = horizontal_center_of_gravity(bin_.placements)
    title_text = title or f"Dest {bin_.dest} center balance ({bin_.center_offset_mm:.1f} mm)"

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
            f'height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">'
        ),
        '<rect x="0" y="0" width="100%" height="100%" fill="#F8F9FB"/>',
        f'<text x="{margin_px}" y="{margin_px + 6}" font-size="18" '
        'font-family="Segoe UI, sans-serif" fill="#1F2937">'
        f"{escape(title_text)}</text>",
        (
            f'<rect x="{panel_left}" y="{panel_top}" width="{panel_w}" height="{panel_h}" '
            'fill="#FFFFFF" stroke="#1F2937" stroke-width="2"/>'
        ),
        (
            f'<circle cx="{screen_x(center_x):.2f}" cy="{screen_y(center_y):.2f}" '
            f'r="{bin_.max_center_offset_mm * scale:.2f}" fill="none" '
            'stroke="#2563EB" stroke-width="2" stroke-dasharray="6 4"/>'
        ),
    ]

    for placement in sorted(bin_.placements, key=lambda p: (p.z, p.y, p.x, p.item.item_id)):
        x = screen_x(placement.x)
        y = screen_y(placement.y + placement.width)
        w = placement.length * scale
        h = placement.width * scale
        lines.append(
            (
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                'fill="#D97706" fill-opacity="0.45" stroke="#111827" stroke-width="1"/>'
            )
        )
        lines.append(
            (
                f'<text x="{x + w / 2:.2f}" y="{y + h / 2:.2f}" text-anchor="middle" '
                'dominant-baseline="middle" font-size="10" font-family="Consolas, monospace" '
                f'fill="#111827">{escape(placement.item.item_id)}</text>'
            )
        )

    lines.extend(
        [
            (
                f'<line x1="{screen_x(center_x):.2f}" y1="{screen_y(center_y):.2f}" '
                f'x2="{screen_x(cg_x):.2f}" y2="{screen_y(cg_y):.2f}" '
                'stroke="#DC2626" stroke-width="2" stroke-dasharray="4 3"/>'
            ),
            (
                f'<circle cx="{screen_x(center_x):.2f}" cy="{screen_y(center_y):.2f}" '
                'r="5" fill="#2563EB"/>'
            ),
            (
                f'<circle cx="{screen_x(cg_x):.2f}" cy="{screen_y(cg_y):.2f}" '
                'r="5" fill="#DC2626"/>'
            ),
        ]
    )

    footer_y = svg_height - margin_px
    lines.extend(
        [
            f'<text x="{margin_px}" y="{footer_y - 36}" font-size="13" '
            'font-family="Segoe UI, sans-serif" fill="#374151">'
            f'Center offset: {bin_.center_offset_mm:.1f}/{bin_.max_center_offset_mm:.1f} mm'
            "</text>",
            f'<text x="{margin_px}" y="{footer_y - 18}" font-size="12" '
            'font-family="Consolas, monospace" fill="#374151">'
            f'Container center=({center_x:.1f}, {center_y:.1f})  CG=({cg_x:.1f}, {cg_y:.1f})'
            "</text>",
            f'<text x="{margin_px}" y="{footer_y}" font-size="12" '
            'font-family="Consolas, monospace" fill="#6B7280">'
            'Blue: allowed center region  Red: actual center of gravity'
            "</text>",
            "</svg>",
        ]
    )
    return "\n".join(lines)


def save_center_balanced_packing_summary_svgs(
    summary: CenterBalancedPackingSummary3D,
    output_dir: str | Path,
    *,
    prefix: str = "step4_center_balance",
) -> list[Path]:
    """Save one orthographic SVG per Step4 bin."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        file_path = out_dir / f"{prefix}_bin{idx:02d}_{bin_.dest}.svg"
        file_path.write_text(
            render_center_balanced_bin_orthographic_svg(
                bin_,
                title=(
                    f"Bin {idx:02d} (Dest {bin_.dest}, "
                    f"offset {bin_.center_offset_mm:.1f}/{bin_.max_center_offset_mm:.1f} mm)"
                ),
            ),
            encoding="utf-8",
        )
        generated.append(file_path)
    return generated


def save_center_balanced_packing_summary_isometric_svgs(
    summary: CenterBalancedPackingSummary3D,
    output_dir: str | Path,
    *,
    prefix: str = "step4_center_balance_isometric",
) -> list[Path]:
    """Save one isometric SVG per Step4 bin."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        file_path = out_dir / f"{prefix}_bin{idx:02d}_{bin_.dest}.svg"
        file_path.write_text(
            render_center_balanced_bin_isometric_svg(
                bin_,
                title=(
                    f"Bin {idx:02d} (Dest {bin_.dest}, "
                    f"offset {bin_.center_offset_mm:.1f}/{bin_.max_center_offset_mm:.1f} mm) isometric"
                ),
            ),
            encoding="utf-8",
        )
        generated.append(file_path)
    return generated


def save_center_balance_topdown_svgs(
    summary: CenterBalancedPackingSummary3D,
    output_dir: str | Path,
    *,
    prefix: str = "step4_center_balance_topdown",
) -> list[Path]:
    """Save one top-down center-balance SVG per Step4 bin."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        file_path = out_dir / f"{prefix}_bin{idx:02d}_{bin_.dest}.svg"
        file_path.write_text(
            render_center_balance_topdown_svg(
                bin_,
                title=f"Bin {idx:02d} (Dest {bin_.dest}) center-of-gravity view",
            ),
            encoding="utf-8",
        )
        generated.append(file_path)
    return generated

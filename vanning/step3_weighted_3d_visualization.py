"""SVG visualization helpers for Step3 weighted 3D packing results."""

from dataclasses import dataclass
from pathlib import Path

from vanning.geometry import Container
from vanning.step2_3d_visualization import render_bin_isometric_svg, render_bin_orthographic_svg
from vanning.step3_weighted_3d import WeightedPackedBin3D, WeightedPackingSummary3D, WeightedPlacedItem3D


@dataclass(frozen=True)
class _VisualizationBinAdapter:
    """Adapter that exposes the fields expected by Step2 SVG renderers."""

    container: Container
    dest: str
    placements: list[WeightedPlacedItem3D]

    @property
    def used_volume(self) -> float:
        return sum(placement.item.volume for placement in self.placements)

    @property
    def remaining_volume(self) -> float:
        return self.container.l * self.container.w * self.container.h - self.used_volume


def _adapt_bin(bin_: WeightedPackedBin3D) -> _VisualizationBinAdapter:
    return _VisualizationBinAdapter(
        container=bin_.container,
        dest=bin_.dest,
        placements=bin_.placements,
    )


def render_weighted_bin_orthographic_svg(bin_: WeightedPackedBin3D, *, title: str | None = None) -> str:
    """Render one weighted 3D bin as top/front/side orthographic SVG panels."""
    weight_text = f"{bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg"
    return render_bin_orthographic_svg(
        _adapt_bin(bin_),
        title=title or f"Dest {bin_.dest} weighted layout ({len(bin_.placements)} items, {weight_text})",
    )


def render_weighted_bin_isometric_svg(bin_: WeightedPackedBin3D, *, title: str | None = None) -> str:
    """Render one weighted 3D bin as an isometric SVG view."""
    weight_text = f"{bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg"
    return render_bin_isometric_svg(
        _adapt_bin(bin_),
        title=title or f"Dest {bin_.dest} weighted isometric ({len(bin_.placements)} items, {weight_text})",
    )


def save_weighted_packing_summary_svgs(
    summary: WeightedPackingSummary3D,
    output_dir: str | Path,
    *,
    prefix: str = "step3_weighted_3d",
) -> list[Path]:
    """Save one orthographic SVG per weighted bin in the packing summary."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        file_path = out_dir / f"{prefix}_bin{idx:02d}_{bin_.dest}.svg"
        svg = render_weighted_bin_orthographic_svg(
            bin_,
            title=(
                f"Bin {idx:02d} (Dest {bin_.dest}, "
                f"{bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg)"
            ),
        )
        file_path.write_text(svg, encoding="utf-8")
        generated.append(file_path)

    return generated


def save_weighted_packing_summary_isometric_svgs(
    summary: WeightedPackingSummary3D,
    output_dir: str | Path,
    *,
    prefix: str = "step3_weighted_3d_iso",
) -> list[Path]:
    """Save one isometric SVG per weighted bin in the packing summary."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        file_path = out_dir / f"{prefix}_bin{idx:02d}_{bin_.dest}.svg"
        svg = render_weighted_bin_isometric_svg(
            bin_,
            title=(
                f"Bin {idx:02d} (Dest {bin_.dest}, "
                f"{bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg) isometric"
            ),
        )
        file_path.write_text(svg, encoding="utf-8")
        generated.append(file_path)

    return generated

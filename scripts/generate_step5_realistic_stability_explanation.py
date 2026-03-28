"""Generate explainable Step5 realistic-stability artifacts for examples and real data."""

from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vanning.geometry import Container
from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    STEP5_MIN_SUPPORT_AREA_RATIO,
    build_step3_weighted_realdata_items,
)
from vanning.step3_weighted_3d import WeightedItem3D
from vanning.step4_center_of_gravity_3d import CenterBalancedPackingSummary3D
from vanning.step4_center_of_gravity_3d_visualization import (
    render_center_balance_topdown_svg,
    save_center_balance_topdown_svgs,
    save_center_balanced_packing_summary_isometric_svgs,
    save_center_balanced_packing_summary_svgs,
)
from vanning.step5_realistic_stability_3d import (
    RealisticStablePackingSummary3D,
    pack_realistic_stable_3d_by_destination_ffd,
    supported_area_ratio,
)


def _build_step5_example_items() -> tuple[Container, list[WeightedItem3D]]:
    container = Container(l=1200, w=900, h=1100)
    items = [
        WeightedItem3D("L", 600, 900, 800, 5, "X", allow_rotate=False),
        WeightedItem3D("R", 600, 900, 800, 5, "X", allow_rotate=False),
        WeightedItem3D("TOP", 1200, 900, 300, 5, "X", allow_rotate=False),
    ]
    return container, items


def _minimum_supported_area_ratio(summary: RealisticStablePackingSummary3D) -> float:
    ratios = [
        supported_area_ratio(placement, bin_.placements)
        for bin_ in summary.bins
        for placement in bin_.placements
        if placement.z > 0
    ]
    return min(ratios, default=1.0)


def _bin_summary_lines(summary: RealisticStablePackingSummary3D) -> str:
    lines = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        stacked_ratios = [
            supported_area_ratio(placement, bin_.placements)
            for placement in bin_.placements
            if placement.z > 0
        ]
        min_ratio = min(stacked_ratios, default=1.0)
        lines.append(
            f"- Bin {idx:02d}: dest={bin_.dest}, items={len(bin_.placements)}, "
            f"weight={bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg, "
            f"center_offset={bin_.center_offset_mm:.1f}/{bin_.max_center_offset_mm:.1f} mm, "
            f"min_support_ratio={min_ratio:.2f}"
        )
    return "\n".join(lines)


def _all_realdata_bin_sections(
    summary: RealisticStablePackingSummary3D,
    topdown_paths: list[Path],
    orthographic_paths: list[Path],
    isometric_paths: list[Path],
) -> str:
    sections: list[str] = []
    for idx, (bin_, top_path, ortho_path, iso_path) in enumerate(
        zip(summary.bins, topdown_paths, orthographic_paths, isometric_paths, strict=True),
        start=1,
    ):
        stacked_ratios = [
            supported_area_ratio(placement, bin_.placements)
            for placement in bin_.placements
            if placement.z > 0
        ]
        min_ratio = min(stacked_ratios, default=1.0)
        sections.append(
            "\n".join(
                [
                    f"### Bin {idx:02d}",
                    "",
                    f"- Dest: `{bin_.dest}`",
                    f"- Items: `{len(bin_.placements)}`",
                    (
                        f"- Weight: `{bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f}kg`, "
                        f"center_offset=`{bin_.center_offset_mm:.1f}/{bin_.max_center_offset_mm:.1f}mm`, "
                        f"min_support_ratio=`{min_ratio:.2f}`"
                    ),
                    "",
                    f"![realdata-top-{idx:02d}]({top_path.as_posix()})",
                    "",
                    f"![realdata-ortho-{idx:02d}]({ortho_path.as_posix()})",
                    "",
                    f"![realdata-iso-{idx:02d}]({iso_path.as_posix()})",
                ]
            )
        )
    return "\n\n".join(sections)


def _write_markdown_report(
    report_path: Path,
    *,
    example_summary: RealisticStablePackingSummary3D,
    realdata_summary: RealisticStablePackingSummary3D,
    example_topdown_path: Path,
    example_ortho_path: Path,
    example_iso_path: Path,
    realdata_topdown_paths: list[Path],
    realdata_ortho_paths: list[Path],
    realdata_iso_paths: list[Path],
) -> None:
    counts = Counter(bin_.dest for bin_ in realdata_summary.bins)
    example_bin = example_summary.bins[0]
    example_support_ratios = [
        supported_area_ratio(placement, example_bin.placements)
        for placement in example_bin.placements
        if placement.z > 0
    ]
    content = f"""# Step5 現実寄り安定条件つき 3D 配置の説明

## 何をしているか

Step5 では、Step4 の実行可能解を拡張して、複数箱またぎを許可しつつ、支持面積率と重心投影で安定性を判定します。

今の実装では、各積み上げ箱について次の 2 条件を同時に満たす必要があります。

- 底面の支持面積率が `{example_summary.min_support_area_ratio:.2f}` 以上
- 底面中心の投影点が支持領域上にある

## 例題

- コンテナ: `L=1200, W=900, H=1100`
- 支持面積率の下限: `{example_summary.min_support_area_ratio:.2f}`
- 箱L: `600x900x800 (5kg)`
- 箱R: `600x900x800 (5kg)`
- 箱TOP: `1200x900x300 (5kg)`

この例では、箱TOP は左右 2 箱の上にまたいで載ります。
単一箱では支えきれませんが、2 箱を合わせると底面の全域が支持されるため、Step5 では同一 bin に積載できます。

### 例題の支持率

- TOP の支持面積率: `{min(example_support_ratios, default=1.0):.2f}`
- TOP の中心投影: `支持領域内`

### Step5 の重心位置

![example-topdown]({example_topdown_path.as_posix()})

### Step5 の配置図

![example-ortho]({example_ortho_path.as_posix()})

![example-iso]({example_iso_path.as_posix()})

## 本番データの結果

- 箱数: `80`
- 使用コンテナ数: `{realdata_summary.bin_count}`
- 行先X用: `{counts.get('X', 0)}`
- 行先Y用: `{counts.get('Y', 0)}`
- 最大重心距離: `{realdata_summary.max_observed_center_offset_mm:.1f} mm`
- 最小支持面積率: `{_minimum_supported_area_ratio(realdata_summary):.2f}`

### 本番データの bin サマリ

{_bin_summary_lines(realdata_summary)}

## 本番データの全 bin 図

{_all_realdata_bin_sections(realdata_summary, realdata_topdown_paths, realdata_ortho_paths, realdata_iso_paths)}
"""
    report_path.write_text(content, encoding="utf-8")


def _as_step4_summary(summary: RealisticStablePackingSummary3D) -> CenterBalancedPackingSummary3D:
    return CenterBalancedPackingSummary3D(
        bins=summary.bins,
        max_center_offset_mm=summary.max_center_offset_mm,
    )


def main() -> None:
    output_root = Path("artifacts/step5_realistic_stability_explanation")
    example_dir = output_root / "example"
    realdata_dir = output_root / "realdata"
    output_root.mkdir(parents=True, exist_ok=True)
    example_dir.mkdir(parents=True, exist_ok=True)
    realdata_dir.mkdir(parents=True, exist_ok=True)

    example_container, example_items = _build_step5_example_items()
    example_summary = pack_realistic_stable_3d_by_destination_ffd(
        example_items,
        example_container,
        max_weight_kg=20,
        max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
        min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
    )
    example_as_step4 = _as_step4_summary(example_summary)
    example_topdowns = save_center_balance_topdown_svgs(
        example_as_step4,
        example_dir,
        prefix="step5_example_topdown",
    )
    example_orthos = save_center_balanced_packing_summary_svgs(
        example_as_step4,
        example_dir,
        prefix="step5_example",
    )
    example_isos = save_center_balanced_packing_summary_isometric_svgs(
        example_as_step4,
        example_dir,
        prefix="step5_example_isometric",
    )

    realdata_items = build_step3_weighted_realdata_items(allow_rotate=True)
    realdata_summary = pack_realistic_stable_3d_by_destination_ffd(
        realdata_items,
        CONTAINER_20FT,
        max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
        max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
        min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
    )
    realdata_as_step4 = _as_step4_summary(realdata_summary)
    realdata_topdowns = save_center_balance_topdown_svgs(
        realdata_as_step4,
        realdata_dir,
        prefix="step5_realdata_topdown",
    )
    realdata_orthos = save_center_balanced_packing_summary_svgs(
        realdata_as_step4,
        realdata_dir,
        prefix="step5_realdata",
    )
    realdata_isos = save_center_balanced_packing_summary_isometric_svgs(
        realdata_as_step4,
        realdata_dir,
        prefix="step5_realdata_isometric",
    )

    report_path = output_root / "README.md"
    _write_markdown_report(
        report_path,
        example_summary=example_summary,
        realdata_summary=realdata_summary,
        example_topdown_path=example_topdowns[0].relative_to(output_root),
        example_ortho_path=example_orthos[0].relative_to(output_root),
        example_iso_path=example_isos[0].relative_to(output_root),
        realdata_topdown_paths=[path.relative_to(output_root) for path in realdata_topdowns],
        realdata_ortho_paths=[path.relative_to(output_root) for path in realdata_orthos],
        realdata_iso_paths=[path.relative_to(output_root) for path in realdata_isos],
    )

    print(f"report: {report_path.resolve()}")
    print(f"example files: {len(example_topdowns) + len(example_orthos) + len(example_isos)} in {example_dir.resolve()}")
    print(f"realdata topdown svgs: {len(realdata_topdowns)} files in {realdata_dir.resolve()}")
    print(f"realdata orthographic svgs: {len(realdata_orthos)} files in {realdata_dir.resolve()}")
    print(f"realdata isometric svgs: {len(realdata_isos)} files in {realdata_dir.resolve()}")


if __name__ == "__main__":
    main()

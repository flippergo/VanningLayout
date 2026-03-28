"""Generate explainable Step4 center-of-gravity artifacts for examples and real data."""

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
    build_step3_weighted_realdata_items,
)
from vanning.step3_weighted_3d import WeightedItem3D, pack_weighted_3d_by_destination_ffd
from vanning.step4_center_of_gravity_3d import (
    CenterBalancedPackingSummary3D,
    pack_center_balanced_3d_by_destination_ffd,
)
from vanning.step4_center_of_gravity_3d_visualization import (
    render_center_balance_topdown_svg,
    save_center_balance_topdown_svgs,
    save_center_balanced_packing_summary_isometric_svgs,
    save_center_balanced_packing_summary_svgs,
)


def _build_step4_example_items() -> tuple[Container, list[WeightedItem3D]]:
    container = Container(l=9000, w=7000, h=3000)
    items = [
        WeightedItem3D("A", 2000, 2000, 3000, 5, "X", allow_rotate=False),
        WeightedItem3D("B", 6000, 2000, 1000, 4, "X", allow_rotate=False),
        WeightedItem3D("C", 6000, 2000, 2000, 3, "X", allow_rotate=False),
    ]
    return container, items


def _bin_summary_lines(summary: CenterBalancedPackingSummary3D) -> str:
    lines = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        lines.append(
            f"- Bin {idx:02d}: dest={bin_.dest}, items={len(bin_.placements)}, "
            f"weight={bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg, "
            f"center_offset={bin_.center_offset_mm:.1f}/{bin_.max_center_offset_mm:.1f} mm"
        )
    return "\n".join(lines)


def _all_realdata_bin_sections(
    summary: CenterBalancedPackingSummary3D,
    topdown_paths: list[Path],
    orthographic_paths: list[Path],
    isometric_paths: list[Path],
) -> str:
    sections: list[str] = []
    for idx, (bin_, top_path, ortho_path, iso_path) in enumerate(
        zip(summary.bins, topdown_paths, orthographic_paths, isometric_paths, strict=True),
        start=1,
    ):
        sections.append(
            "\n".join(
                [
                    f"### Bin {idx:02d}",
                    "",
                    f"- Dest: `{bin_.dest}`",
                    f"- Items: `{len(bin_.placements)}`",
                    (
                        f"- Weight: `{bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f}kg`, "
                        f"center_offset=`{bin_.center_offset_mm:.1f}/{bin_.max_center_offset_mm:.1f}mm`"
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
    step3_before_offset_mm: float,
    step4_summary: CenterBalancedPackingSummary3D,
    example_before_topdown_path: Path,
    example_after_topdown_path: Path,
    example_after_ortho_path: Path,
    example_after_iso_path: Path,
    realdata_topdown_paths: list[Path],
    realdata_ortho_paths: list[Path],
    realdata_iso_paths: list[Path],
) -> None:
    counts = Counter(bin_.dest for bin_ in step4_summary.bins)
    example_bin = step4_summary.bins[0]
    content = f"""# Step4 重心制約つき 3D 配置の説明

## 何をしているか

Step4 では、Step3 の実行可能解を初期解として、各 bin の水平重心が床面中心から半径 `300mm` 以内に収まるように調整します。

今の実装では、同一 bin 内の箱の相対配置を壊さずに、bin 全体を水平移動して床面中心へ寄せます。

## 例題

- コンテナ: `L=9000, W=7000, H=3000`
- 重心上限: `300mm`
- 箱A: `2000x2000x3000 (5kg)`
- 箱B: `6000x2000x1000 (4kg)`
- 箱C: `6000x2000x2000 (3kg)`

この例では、Step3 の結果は左前に寄っているため、重心が中心から外れます。  
Step4 では、bin 全体を平行移動して重心を中心へ近づけます。

### 重心の変化

- Step3 の offset: `{step3_before_offset_mm:.1f} mm`
- Step4 の offset: `{example_bin.center_offset_mm:.1f} mm`

### Step3 の重心位置

![example-before-topdown]({example_before_topdown_path.as_posix()})

### Step4 の重心位置

![example-after-topdown]({example_after_topdown_path.as_posix()})

### Step4 の配置図

![example-after-ortho]({example_after_ortho_path.as_posix()})

![example-after-iso]({example_after_iso_path.as_posix()})

## 本番データの結果

- 箱数: `80`
- 使用コンテナ数: `{step4_summary.bin_count}`
- 行先X用: `{counts.get('X', 0)}`
- 行先Y用: `{counts.get('Y', 0)}`
- 最大重心距離: `{step4_summary.max_observed_center_offset_mm:.1f} mm`

### 本番データの bin サマリ

{_bin_summary_lines(step4_summary)}

## 本番データの全 bin 図

{_all_realdata_bin_sections(step4_summary, realdata_topdown_paths, realdata_ortho_paths, realdata_iso_paths)}
"""
    report_path.write_text(content, encoding="utf-8")


def main() -> None:
    output_root = Path("artifacts/step4_center_of_gravity_explanation")
    example_dir = output_root / "example"
    realdata_dir = output_root / "realdata"
    output_root.mkdir(parents=True, exist_ok=True)
    example_dir.mkdir(parents=True, exist_ok=True)
    realdata_dir.mkdir(parents=True, exist_ok=True)

    example_container, example_items = _build_step4_example_items()
    example_step3 = pack_weighted_3d_by_destination_ffd(
        example_items,
        example_container,
        max_weight_kg=12,
    )
    example_summary = pack_center_balanced_3d_by_destination_ffd(
        example_items,
        example_container,
        max_weight_kg=12,
        max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    )

    example_before_topdown = example_dir / "step4_example_before_topdown.svg"
    example_before_topdown.write_text(
        render_center_balance_topdown_svg(
            example_summary.bins[0].__class__(
                container=example_step3.bins[0].container,
                dest=example_step3.bins[0].dest,
                max_weight_kg=example_step3.bins[0].max_weight_kg,
                max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
                placements=example_step3.bins[0].placements,
            ),
            title="Example: Step3 center of gravity",
        ),
        encoding="utf-8",
    )

    example_topdowns = save_center_balance_topdown_svgs(
        example_summary,
        example_dir,
        prefix="step4_example_topdown",
    )
    example_orthos = save_center_balanced_packing_summary_svgs(
        example_summary,
        example_dir,
        prefix="step4_example",
    )
    example_isos = save_center_balanced_packing_summary_isometric_svgs(
        example_summary,
        example_dir,
        prefix="step4_example_isometric",
    )

    realdata_items = build_step3_weighted_realdata_items(allow_rotate=True)
    realdata_summary = pack_center_balanced_3d_by_destination_ffd(
        realdata_items,
        CONTAINER_20FT,
        max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
        max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    )
    realdata_topdowns = save_center_balance_topdown_svgs(
        realdata_summary,
        realdata_dir,
        prefix="step4_realdata_topdown",
    )
    realdata_orthos = save_center_balanced_packing_summary_svgs(
        realdata_summary,
        realdata_dir,
        prefix="step4_realdata",
    )
    realdata_isos = save_center_balanced_packing_summary_isometric_svgs(
        realdata_summary,
        realdata_dir,
        prefix="step4_realdata_isometric",
    )

    report_path = output_root / "README.md"
    _write_markdown_report(
        report_path,
        step3_before_offset_mm=center_offset_distance_mm(
            example_step3.bins[0].placements,
            example_container,
        ),
        step4_summary=realdata_summary,
        example_before_topdown_path=example_before_topdown.relative_to(output_root),
        example_after_topdown_path=example_topdowns[0].relative_to(output_root),
        example_after_ortho_path=example_orthos[0].relative_to(output_root),
        example_after_iso_path=example_isos[0].relative_to(output_root),
        realdata_topdown_paths=[path.relative_to(output_root) for path in realdata_topdowns],
        realdata_ortho_paths=[path.relative_to(output_root) for path in realdata_orthos],
        realdata_iso_paths=[path.relative_to(output_root) for path in realdata_isos],
    )

    print(f"report: {report_path.resolve()}")
    print(f"example files: {len(example_topdowns) + len(example_orthos) + len(example_isos) + 1} in {example_dir.resolve()}")
    print(f"realdata topdown svgs: {len(realdata_topdowns)} files in {realdata_dir.resolve()}")
    print(f"realdata orthographic svgs: {len(realdata_orthos)} files in {realdata_dir.resolve()}")
    print(f"realdata isometric svgs: {len(realdata_isos)} files in {realdata_dir.resolve()}")


if __name__ == "__main__":
    from vanning.step4_center_of_gravity_3d import center_offset_distance_mm

    main()

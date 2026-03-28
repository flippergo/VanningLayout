"""Generate explainable Step3 weighted 3D packing artifacts for examples and real data."""

from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vanning.geometry import Container
from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    build_step3_weighted_realdata_items,
)
from vanning.step3_weighted_3d import WeightedItem3D, WeightedPackingSummary3D, pack_weighted_3d_by_destination_ffd
from vanning.step3_weighted_3d_visualization import (
    save_weighted_packing_summary_isometric_svgs,
    save_weighted_packing_summary_svgs,
)


def _build_small_step32_example() -> tuple[Container, list[WeightedItem3D], WeightedPackingSummary3D]:
    container = Container(l=6, w=4, h=3)
    items = [
        WeightedItem3D("A", 2, 2, 3, 5, "X", allow_rotate=False),
        WeightedItem3D("B", 6, 2, 1, 4, "X", allow_rotate=False),
        WeightedItem3D("C", 6, 2, 2, 3, "X", allow_rotate=False),
    ]
    summary = pack_weighted_3d_by_destination_ffd(items, container, max_weight_kg=12)
    return container, items, summary


def _placement_table(summary: WeightedPackingSummary3D) -> str:
    lines = [
        "| bin | item | dest | weight_kg | x | y | z | l | w | h | rotated |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for bin_idx, bin_ in enumerate(summary.bins, start=1):
        for placement in sorted(bin_.placements, key=lambda p: (p.z, p.y, p.x, p.item.item_id)):
            lines.append(
                f"| {bin_idx} | {placement.item.item_id} | {placement.item.dest} | "
                f"{placement.item.weight_kg:g} | {placement.x:g} | {placement.y:g} | {placement.z:g} | "
                f"{placement.length:g} | {placement.width:g} | {placement.height:g} | "
                f"{'yes' if placement.rotated else 'no'} |"
            )
    return "\n".join(lines)


def _bin_summary_lines(summary: WeightedPackingSummary3D) -> str:
    lines = []
    for idx, bin_ in enumerate(summary.bins, start=1):
        lines.append(
            f"- Bin {idx:02d}: dest={bin_.dest}, items={len(bin_.placements)}, "
            f"weight={bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg"
        )
    return "\n".join(lines)


def _all_realdata_bin_sections(
    summary: WeightedPackingSummary3D,
    orthographic_paths: list[Path],
    isometric_paths: list[Path],
) -> str:
    sections: list[str] = []
    for idx, (bin_, ortho_path, iso_path) in enumerate(
        zip(summary.bins, orthographic_paths, isometric_paths, strict=True),
        start=1,
    ):
        sections.append(
            "\n".join(
                [
                    f"### Bin {idx:02d}",
                    "",
                    f"- 行先: `{bin_.dest}`",
                    f"- 箱数: `{len(bin_.placements)}`",
                    f"- 重量: `{bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f}kg`",
                    "",
                    f"![realdata-bin-{idx:02d}]({ortho_path.as_posix()})",
                    "",
                    f"![realdata-bin-{idx:02d}-iso]({iso_path.as_posix()})",
                ]
            )
        )
    return "\n\n".join(sections)


def _write_markdown_report(
    report_path: Path,
    *,
    example_summary: WeightedPackingSummary3D,
    realdata_summary: WeightedPackingSummary3D,
    example_svgs: list[Path],
    example_isometric_svgs: list[Path],
    realdata_svgs: list[Path],
    realdata_isometric_svgs: list[Path],
) -> None:
    counts = Counter(bin_.dest for bin_ in realdata_summary.bins)
    content = f"""# Step3 重量制約つき 3D 配置の説明

## 何をしているか

Step3 では、Step2 の 3D 配置に次の 2 つを追加します。

1. 行先を混ぜずに、箱重量の合計が `max_weight_kg` を超えないように bin を分ける
2. 配置後に、各箱の重心の鉛直投影が床または支持面に入っていることを確認する

実装の流れは次のとおりです。

1. 行先ごとに箱を分け、重い順に `first-fit decreasing` で重量割当する
2. 各重量 bin に対して Step2 の 3D 配置を実行する
3. 出来上がった配置に対して、箱ごとの支持安定性を検証する

## 例題

`approach.md` の **小3-2** に合わせて、**小2-1 と同じ箱セット**に重量を付けた例です。

- コンテナ: `L=6, W=4, H=3`
- 重量上限: `12kg`
- 箱A: `2x2x3 (5kg)`
- 箱B: `6x2x1 (4kg)`
- 箱C: `6x2x2 (3kg)`

この箱セットは、床面に `C` を置き、その上に `B` を積み、残りの床面に `A` を立てる積み上げ例です。  
Step3 ではこの Step2 の積み上げに対して、重量上限と支持安定性を同時に確認します。

### 例題の bin サマリ

{_bin_summary_lines(example_summary)}

### 例題の平面図・正面図・側面図

{chr(10).join(f"![example-{idx}]({path.as_posix()})" for idx, path in enumerate(example_svgs, start=1))}

### 例題の立体図

{chr(10).join(f"![example-iso-{idx}]({path.as_posix()})" for idx, path in enumerate(example_isometric_svgs, start=1))}

### 例題の配置結果

{_placement_table(example_summary)}

## 本番データの結果

- 箱数: `80`
- 総重量: `{realdata_summary.total_weight_kg:.0f}kg`
- 使用コンテナ数: `{realdata_summary.bin_count}`
- 行先X用: `{counts.get('X', 0)}`
- 行先Y用: `{counts.get('Y', 0)}`

### 本番データの bin サマリ

{_bin_summary_lines(realdata_summary)}

### 本番データの可視化ファイル

{chr(10).join(f"- `{path.as_posix()}`" for path in realdata_svgs)}

### 本番データの立体図ファイル

{chr(10).join(f"- `{path.as_posix()}`" for path in realdata_isometric_svgs)}

## 本番データの全 bin 図

見る人が bin を選べるように、全コンテナの図を並べています。

{_all_realdata_bin_sections(realdata_summary, realdata_svgs, realdata_isometric_svgs)}

## 読み方

- 3 面図では、各箱の `x / y / z` 位置と積み上がり方を確認できます
- 立体図では、箱の前後関係や積層を直感的に確認できます
- Step3 では、配置できても重量超過や支持不安定なら採用しません
"""
    report_path.write_text(content, encoding="utf-8")


def main() -> None:
    output_root = Path("artifacts/step3_weighted_3d_explanation")
    example_dir = output_root / "example"
    realdata_dir = output_root / "realdata"
    output_root.mkdir(parents=True, exist_ok=True)

    _, _, example_summary = _build_small_step32_example()
    example_dir.mkdir(parents=True, exist_ok=True)
    example_svgs = save_weighted_packing_summary_svgs(
        example_summary,
        example_dir,
        prefix="step3_weighted_example",
    )
    example_isometric_svgs = save_weighted_packing_summary_isometric_svgs(
        example_summary,
        example_dir,
        prefix="step3_weighted_example_isometric",
    )

    realdata_items = build_step3_weighted_realdata_items(allow_rotate=True)
    realdata_summary = pack_weighted_3d_by_destination_ffd(
        realdata_items,
        CONTAINER_20FT,
        max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
    )
    realdata_svgs = save_weighted_packing_summary_svgs(
        realdata_summary,
        realdata_dir,
        prefix="step3_weighted_realdata",
    )
    realdata_isometric_svgs = save_weighted_packing_summary_isometric_svgs(
        realdata_summary,
        realdata_dir,
        prefix="step3_weighted_realdata_isometric",
    )

    report_path = output_root / "README.md"
    _write_markdown_report(
        report_path,
        example_summary=example_summary,
        realdata_summary=realdata_summary,
        example_svgs=[path.relative_to(output_root) for path in example_svgs],
        example_isometric_svgs=[path.relative_to(output_root) for path in example_isometric_svgs],
        realdata_svgs=[path.relative_to(output_root) for path in realdata_svgs],
        realdata_isometric_svgs=[path.relative_to(output_root) for path in realdata_isometric_svgs],
    )

    print(f"report: {report_path.resolve()}")
    print(f"example orthographic svgs: {len(example_svgs)} files in {example_dir.resolve()}")
    print(f"example isometric svgs: {len(example_isometric_svgs)} files in {example_dir.resolve()}")
    print(f"realdata orthographic svgs: {len(realdata_svgs)} files in {realdata_dir.resolve()}")
    print(f"realdata isometric svgs: {len(realdata_isometric_svgs)} files in {realdata_dir.resolve()}")


if __name__ == "__main__":
    main()

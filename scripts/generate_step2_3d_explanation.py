"""Generate explainable Step2 3D packing artifacts for examples and real data."""

from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vanning.geometry import Container
from vanning.problem_spec import CONTAINER_20FT, build_step2_3d_realdata_items
from vanning.step2_3d import Item3D, PackingSummary3D, pack_3d_by_destination_ffd
from vanning.step2_3d_visualization import (
    render_bin_isometric_svg,
    render_bin_orthographic_svg,
    save_packing_summary_isometric_svgs,
    save_packing_summary_svgs,
)


def _build_stacking_example() -> tuple[Container, list[Item3D], PackingSummary3D]:
    container = Container(l=3, w=3, h=2)
    items = [
        Item3D("A", length=1, width=1, height=2, dest="X", allow_rotate=False),
        Item3D("B", length=3, width=1, height=1, dest="X", allow_rotate=False),
        Item3D("C", length=3, width=2, height=1, dest="X", allow_rotate=False),
    ]
    summary = pack_3d_by_destination_ffd(items, container)
    return container, items, summary


def _placement_table(summary: PackingSummary3D) -> str:
    lines = [
        "| bin | item | dest | x | y | z | l | w | h | rotated |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for bin_idx, bin_ in enumerate(summary.bins, start=1):
        for placement in sorted(bin_.placements, key=lambda p: (p.z, p.y, p.x, p.item.item_id)):
            lines.append(
                f"| {bin_idx} | {placement.item.item_id} | {placement.item.dest} | "
                f"{placement.x:g} | {placement.y:g} | {placement.z:g} | "
                f"{placement.length:g} | {placement.width:g} | {placement.height:g} | "
                f"{'yes' if placement.rotated else 'no'} |"
            )
    return "\n".join(lines)


def _write_markdown_report(
    report_path: Path,
    *,
    example_summary: PackingSummary3D,
    realdata_summary: PackingSummary3D,
    example_svg_path: Path,
    example_iso_svg_path: Path,
    realdata_svgs: list[Path],
    realdata_isometric_svgs: list[Path],
) -> None:
    counts = Counter(bin_.dest for bin_ in realdata_summary.bins)
    content = f"""# Step2 3D配置の説明資料

## この実装で何をしているか

Step2 では、重量制約や重心制約はまだ入れずに、まず「箱を3Dで置ける」実行可能解を作ります。

実装しているルールは次のとおりです。

1. 行先ごとに箱を分け、体積の大きい順に処理する
2. 既に置いた箱の `+x / +y / +z` 面から候補座標を作る
3. 各候補座標で、回転なし / 90度回転を試す
4. `コンテナ内`、`非重複`、`床置きまたは完全支持` を満たす配置だけ残す
5. `y -> x -> z` を優先するスコアで、その bin の最良配置を選ぶ
6. 既存の bin に入らなければ、新しい bin を作る

## 例題

「積み上げれば 1 bin に収まる」ことを見せる最小例です。

- コンテナ: `L=3, W=3, H=2`
- 箱A: `1x1x2`
- 箱B: `3x1x1`
- 箱C: `3x2x1`

期待する見え方は、床面を C が埋め、その上に B が積まれ、縦長の A が残りの床面に入る形です。

![example]({example_svg_path.as_posix()})

### 立体図

斜め上から見た図も追加しています。箱の上下関係と、床面のどこを使っているかを同時に把握しやすくなります。

![example-iso]({example_iso_svg_path.as_posix()})

### 例題の配置結果

{_placement_table(example_summary)}

## 本番データの結果

- 箱数: `80`
- 使用コンテナ数: `{realdata_summary.bin_count}`
- 行先X用: `{counts.get('X', 0)}`
- 行先Y用: `{counts.get('Y', 0)}`

### 本番データの可視化ファイル

{chr(10).join(f"- `{path.as_posix()}`" for path in realdata_svgs)}

### 本番データの立体図ファイル

{chr(10).join(f"- `{path.as_posix()}`" for path in realdata_isometric_svgs)}

三面図として出しているので、次を見分けやすくしています。

- Top: 床面の詰まり方
- Front: 長さ方向に見た積み上がり
- Side: 幅方向に見た積み上がり

立体図では、次が見やすくなります。

- どの箱が上に載っているか
- 手前と奥の箱の位置関係
- 1つの箱がどのくらい高さを使っているか
"""
    report_path.write_text(content, encoding="utf-8")


def main() -> None:
    output_root = Path("artifacts/step2_3d_explanation")
    example_dir = output_root / "example"
    realdata_dir = output_root / "realdata"
    output_root.mkdir(parents=True, exist_ok=True)

    _, _, example_summary = _build_stacking_example()
    example_dir.mkdir(parents=True, exist_ok=True)
    example_svg = example_dir / "stacking_single_bin_example.svg"
    example_iso_svg = example_dir / "stacking_single_bin_example_isometric.svg"
    example_svg.write_text(
        render_bin_orthographic_svg(example_summary.bins[0], title="Example: stacking keeps one bin"),
        encoding="utf-8",
    )
    example_iso_svg.write_text(
        render_bin_isometric_svg(example_summary.bins[0], title="Example: stacking keeps one bin"),
        encoding="utf-8",
    )

    realdata_items = build_step2_3d_realdata_items(allow_rotate=True)
    realdata_summary = pack_3d_by_destination_ffd(realdata_items, CONTAINER_20FT)
    realdata_svgs = save_packing_summary_svgs(
        realdata_summary,
        realdata_dir,
        prefix="step2_3d_realdata",
    )
    realdata_isometric_svgs = save_packing_summary_isometric_svgs(
        realdata_summary,
        realdata_dir,
        prefix="step2_3d_realdata_isometric",
    )

    report_path = output_root / "README.md"
    _write_markdown_report(
        report_path,
        example_summary=example_summary,
        realdata_summary=realdata_summary,
        example_svg_path=example_svg.relative_to(output_root),
        example_iso_svg_path=example_iso_svg.relative_to(output_root),
        realdata_svgs=[path.relative_to(output_root) for path in realdata_svgs],
        realdata_isometric_svgs=[path.relative_to(output_root) for path in realdata_isometric_svgs],
    )

    print(f"report: {report_path.resolve()}")
    print(f"example svg: {example_svg.resolve()}")
    print(f"example isometric svg: {example_iso_svg.resolve()}")
    print(f"realdata orthographic svgs: {len(realdata_svgs)} files in {realdata_dir.resolve()}")
    print(f"realdata isometric svgs: {len(realdata_isometric_svgs)} files in {realdata_dir.resolve()}")


if __name__ == "__main__":
    main()

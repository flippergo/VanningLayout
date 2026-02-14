"""Step1: 本番2Dデータ適用 + 可視化を実行するスクリプト。"""

from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vanning.problem_spec import CONTAINER_20FT, build_step1_2d_realdata_items
from vanning.step1_2d import pack_2d_by_destination_ffd
from vanning.step1_2d_visualization import save_packing_summary_svgs


def main() -> None:
    items = build_step1_2d_realdata_items(allow_rotate=True)
    summary = pack_2d_by_destination_ffd(
        items,
        bin_length=CONTAINER_20FT.l,
        bin_width=CONTAINER_20FT.w,
    )
    output_dir = Path("artifacts/step1_2d_realdata")
    files = save_packing_summary_svgs(summary, output_dir)

    counts = Counter(bin_.dest for bin_ in summary.bins)
    print(f"items: {len(items)}")
    print(f"bins: {summary.bin_count} (X={counts.get('X', 0)}, Y={counts.get('Y', 0)})")
    print(f"total unused area: {summary.total_unused_area:.0f} mm^2")
    print(f"svg files: {len(files)}")
    print(f"output directory: {output_dir.resolve()}")


if __name__ == "__main__":
    main()

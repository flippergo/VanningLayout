"""Run Step2 3D packing on the real-data box set."""

from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vanning.problem_spec import CONTAINER_20FT, build_step2_3d_realdata_items
from vanning.step2_3d import pack_3d_by_destination_ffd


def main() -> None:
    items = build_step2_3d_realdata_items(allow_rotate=True)
    summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

    counts = Counter(bin_.dest for bin_ in summary.bins)
    used_volume = sum(bin_.used_volume for bin_ in summary.bins)
    capacity_volume = summary.bin_count * CONTAINER_20FT.l * CONTAINER_20FT.w * CONTAINER_20FT.h

    print(f"items: {len(items)}")
    print(f"bins: {summary.bin_count} (X={counts.get('X', 0)}, Y={counts.get('Y', 0)})")
    print(f"used volume: {used_volume:.0f} mm^3")
    print(f"unused volume: {capacity_volume - used_volume:.0f} mm^3")


if __name__ == "__main__":
    main()

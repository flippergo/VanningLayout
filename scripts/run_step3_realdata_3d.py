"""Run Step3 weight-constrained 3D packing on the real-data box set."""

from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    build_step3_weighted_realdata_items,
)
from vanning.step3_weighted_3d import pack_weighted_3d_by_destination_ffd


def main() -> None:
    items = build_step3_weighted_realdata_items(allow_rotate=True)
    summary = pack_weighted_3d_by_destination_ffd(
        items,
        CONTAINER_20FT,
        max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
    )

    counts = Counter(bin_.dest for bin_ in summary.bins)
    print(f"items: {len(items)}")
    print(f"bins: {summary.bin_count} (X={counts.get('X', 0)}, Y={counts.get('Y', 0)})")
    print(f"total weight: {summary.total_weight_kg:.0f} kg")
    for idx, bin_ in enumerate(summary.bins, start=1):
        print(
            f"bin {idx:02d}: dest={bin_.dest} items={len(bin_.placements)} "
            f"weight={bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg"
        )


if __name__ == "__main__":
    main()

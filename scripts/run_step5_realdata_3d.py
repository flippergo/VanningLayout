"""Run Step5 realistic-stability 3D packing on the real-data box set."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    STEP5_MIN_SUPPORT_AREA_RATIO,
    build_step3_weighted_realdata_items,
)
from vanning.step5_realistic_stability_3d import pack_realistic_stable_3d_by_destination_ffd


def main() -> None:
    items = build_step3_weighted_realdata_items(allow_rotate=True)
    summary = pack_realistic_stable_3d_by_destination_ffd(
        items,
        CONTAINER_20FT,
        max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
        max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
        min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
    )

    print(f"items: {len(items)}")
    print(f"bins: {summary.bin_count}")
    print(f"max observed center offset: {summary.max_observed_center_offset_mm:.1f} mm")
    print(f"min support area ratio: {summary.min_support_area_ratio:.2f}")
    for idx, bin_ in enumerate(summary.bins, start=1):
        print(
            f"bin {idx:02d}: dest={bin_.dest} items={len(bin_.placements)} "
            f"weight={bin_.total_weight_kg:.0f}/{bin_.max_weight_kg:.0f} kg "
            f"center_offset={bin_.center_offset_mm:.1f}/{bin_.max_center_offset_mm:.1f} mm"
        )


if __name__ == "__main__":
    main()

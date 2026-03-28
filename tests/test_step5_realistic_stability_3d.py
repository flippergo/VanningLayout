import unittest

from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    STEP5_MIN_SUPPORT_AREA_RATIO,
    build_step3_weighted_realdata_items,
)
from vanning.step3_weighted_3d import WeightedItem3D, WeightedPlacedItem3D, is_stably_supported
from vanning.step4_center_of_gravity_3d import pack_center_balanced_3d_by_destination_ffd
from vanning.step5_realistic_stability_3d import (
    is_projection_supported,
    is_realistically_supported,
    pack_realistic_stable_3d_by_destination_ffd,
    supported_area_ratio,
    validate_realistic_stability,
)


class Step5RealisticStabilityPackingTests(unittest.TestCase):
    def test_multi_support_counts_as_full_support_when_base_is_fully_covered(self) -> None:
        base_left = WeightedPlacedItem3D(
            item=WeightedItem3D("L", 500, 1000, 500, 5, "X", allow_rotate=False),
            x=0,
            y=0,
            z=0,
            length=500,
            width=1000,
            height=500,
            rotated=False,
        )
        base_right = WeightedPlacedItem3D(
            item=WeightedItem3D("R", 500, 1000, 500, 5, "X", allow_rotate=False),
            x=500,
            y=0,
            z=0,
            length=500,
            width=1000,
            height=500,
            rotated=False,
        )
        top = WeightedPlacedItem3D(
            item=WeightedItem3D("TOP", 1000, 1000, 400, 5, "X", allow_rotate=False),
            x=0,
            y=0,
            z=500,
            length=1000,
            width=1000,
            height=400,
            rotated=False,
        )

        placements = [base_left, base_right, top]

        self.assertAlmostEqual(supported_area_ratio(top, placements), 1.0)
        self.assertTrue(is_projection_supported(top, placements))
        self.assertTrue(is_realistically_supported(top, placements))

    def test_stability_rejects_support_area_below_threshold(self) -> None:
        base = WeightedPlacedItem3D(
            item=WeightedItem3D("BASE", 700, 1000, 500, 5, "X", allow_rotate=False),
            x=0,
            y=0,
            z=0,
            length=700,
            width=1000,
            height=500,
            rotated=False,
        )
        top = WeightedPlacedItem3D(
            item=WeightedItem3D("TOP", 1000, 1000, 400, 5, "X", allow_rotate=False),
            x=0,
            y=0,
            z=500,
            length=1000,
            width=1000,
            height=400,
            rotated=False,
        )

        placements = [base, top]

        self.assertAlmostEqual(supported_area_ratio(top, placements), 0.7)
        self.assertTrue(is_stably_supported(top, placements))
        self.assertTrue(is_projection_supported(top, placements))
        self.assertFalse(is_realistically_supported(top, placements, min_support_area_ratio=0.8))
        with self.assertRaisesRegex(ValueError, "unstable placement under Step5 rule: TOP"):
            validate_realistic_stability(placements, min_support_area_ratio=0.8)

    def test_step5_packing_uses_multi_support_to_keep_single_bin(self) -> None:
        bridge_container = type(CONTAINER_20FT)(l=1200, w=900, h=1100)
        items = [
            WeightedItem3D("L", 600, 900, 800, 5, "X", allow_rotate=False),
            WeightedItem3D("R", 600, 900, 800, 5, "X", allow_rotate=False),
            WeightedItem3D("TOP", 1200, 900, 300, 5, "X", allow_rotate=False),
        ]

        step4_summary = pack_center_balanced_3d_by_destination_ffd(
            items,
            bridge_container,
            max_weight_kg=20,
            max_center_offset_mm=300,
        )
        step5_summary = pack_realistic_stable_3d_by_destination_ffd(
            items,
            bridge_container,
            max_weight_kg=20,
            max_center_offset_mm=300,
            min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
        )

        self.assertEqual(step4_summary.bin_count, 2)
        self.assertEqual(step5_summary.bin_count, 1)
        validate_realistic_stability(
            step5_summary.bins[0].placements,
            min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
        )

    def test_realdata_packing_is_valid(self) -> None:
        items = build_step3_weighted_realdata_items()
        step4_summary = pack_center_balanced_3d_by_destination_ffd(
            items,
            CONTAINER_20FT,
            max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
            max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
        )
        step5_summary = pack_realistic_stable_3d_by_destination_ffd(
            items,
            CONTAINER_20FT,
            max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
            max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
            min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
        )

        self.assertGreater(step5_summary.bin_count, 0)
        self.assertEqual(step5_summary.total_weight_kg, sum(item.weight_kg for item in items))
        self.assertLessEqual(step5_summary.bin_count, step4_summary.bin_count)
        self.assertTrue(step5_summary.all_bins_within_center_constraint)
        for bin_ in step5_summary.bins:
            self.assertLessEqual(bin_.center_offset_mm, CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM)
            self.assertLessEqual(bin_.total_weight_kg, CONTAINER_20FT_MAX_PAYLOAD_KG)
            validate_realistic_stability(
                bin_.placements,
                min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
            )


if __name__ == "__main__":
    unittest.main()

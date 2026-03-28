import unittest

from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    build_step3_weighted_realdata_items,
)
from vanning.step3_weighted_3d import (
    WeightedItem3D,
    WeightedPlacedItem3D,
    pack_weighted_3d_by_destination_ffd,
    validate_stable_placements,
)
from vanning.step4_center_of_gravity_3d import (
    center_offset_distance_mm,
    horizontal_center_of_gravity,
    pack_center_balanced_3d_by_destination_ffd,
    translate_bin_toward_center,
)


class Step4CenterOfGravityThreeDimensionalPackingTests(unittest.TestCase):
    def test_horizontal_center_of_gravity_matches_weighted_average(self) -> None:
        placements = [
            WeightedPlacedItem3D(
                item=WeightedItem3D("L", 1000, 1000, 1000, 7, "X", allow_rotate=False),
                x=0,
                y=0,
                z=0,
                length=1000,
                width=1000,
                height=1000,
                rotated=False,
            ),
            WeightedPlacedItem3D(
                item=WeightedItem3D("R", 1000, 1000, 1000, 5, "X", allow_rotate=False),
                x=1000,
                y=0,
                z=0,
                length=1000,
                width=1000,
                height=1000,
                rotated=False,
            ),
        ]
        cg_x, cg_y = horizontal_center_of_gravity(placements)

        self.assertAlmostEqual(cg_x, (500 * 7 + 1500 * 5) / 12)
        self.assertAlmostEqual(cg_y, 500)

    def test_translate_bin_toward_center_reduces_offset_when_space_is_available(self) -> None:
        items = [
            WeightedItem3D("A1", 1000, 1000, 1000, 7, "X", allow_rotate=False),
            WeightedItem3D("A2", 1000, 1000, 1000, 7, "X", allow_rotate=False),
            WeightedItem3D("A3", 1000, 1000, 1000, 5, "X", allow_rotate=False),
        ]
        roomy_container = type(CONTAINER_20FT)(l=6000, w=3000, h=3000)
        step3_summary = pack_weighted_3d_by_destination_ffd(items, roomy_container, max_weight_kg=20)

        before = center_offset_distance_mm(step3_summary.bins[0].placements, roomy_container)
        centered_bin = translate_bin_toward_center(step3_summary.bins[0], max_center_offset_mm=300)
        after = centered_bin.center_offset_mm

        self.assertLess(after, before)
        self.assertAlmostEqual(centered_bin.center_of_gravity_x, roomy_container.l / 2)
        self.assertAlmostEqual(centered_bin.center_of_gravity_y, roomy_container.w / 2)
        validate_stable_placements(centered_bin.placements)

    def test_center_balanced_packing_rejects_negative_radius(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_center_offset_mm must be non-negative"):
            pack_center_balanced_3d_by_destination_ffd(
                [],
                CONTAINER_20FT,
                max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
                max_center_offset_mm=-1,
            )

    def test_realdata_center_balanced_packing_is_valid(self) -> None:
        items = build_step3_weighted_realdata_items()
        summary = pack_center_balanced_3d_by_destination_ffd(
            items,
            CONTAINER_20FT,
            max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
            max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
        )

        self.assertEqual(summary.bin_count, 4)
        self.assertTrue(summary.all_bins_within_center_constraint)
        for bin_ in summary.bins:
            self.assertLessEqual(bin_.center_offset_mm, CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM)
            self.assertLessEqual(bin_.total_weight_kg, CONTAINER_20FT_MAX_PAYLOAD_KG)
            validate_stable_placements(bin_.placements)


if __name__ == "__main__":
    unittest.main()

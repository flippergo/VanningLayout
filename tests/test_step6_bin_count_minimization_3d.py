import unittest
from unittest.mock import patch

from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    STEP5_MIN_SUPPORT_AREA_RATIO,
    build_step3_weighted_realdata_items,
)
from vanning.step3_weighted_3d import WeightedItem3D
from vanning.step5_realistic_stability_3d import (
    pack_realistic_stable_3d_by_destination_ffd,
    validate_realistic_stability,
)
from vanning.step6_bin_count_minimization_3d import (
    _try_pack_items_into_bin_count,
    pack_min_bin_count_3d_by_destination,
)


class Step6BinCountMinimizationTests(unittest.TestCase):
    def test_reduces_ffd_weight_split_by_repartitioning_bins(self) -> None:
        roomy_container = type(CONTAINER_20FT)(l=2000, w=2000, h=2000)
        items = [
            WeightedItem3D("A", 400, 400, 400, 6, "X", allow_rotate=False),
            WeightedItem3D("B", 400, 400, 400, 5, "X", allow_rotate=False),
            WeightedItem3D("C", 400, 400, 400, 3, "X", allow_rotate=False),
            WeightedItem3D("D", 400, 400, 400, 2, "X", allow_rotate=False),
            WeightedItem3D("E", 400, 400, 400, 2, "X", allow_rotate=False),
            WeightedItem3D("F", 400, 400, 400, 2, "X", allow_rotate=False),
        ]

        step5_summary = pack_realistic_stable_3d_by_destination_ffd(
            items,
            roomy_container,
            max_weight_kg=10,
            max_center_offset_mm=1000,
            min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
        )
        step6_summary = pack_min_bin_count_3d_by_destination(
            items,
            roomy_container,
            max_weight_kg=10,
            max_center_offset_mm=1000,
            min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
        )

        self.assertEqual(step5_summary.bin_count, 3)
        self.assertEqual(step6_summary.initial_bin_count, 3)
        self.assertEqual(step6_summary.bin_count, 2)
        self.assertEqual(step6_summary.total_weight_kg, sum(item.weight_kg for item in items))
        for bin_ in step6_summary.bins:
            self.assertLessEqual(bin_.total_weight_kg, 10)
            validate_realistic_stability(
                bin_.placements,
                min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
            )

    def test_keeps_bin_count_when_weight_lower_bound_is_already_tight(self) -> None:
        roomy_container = type(CONTAINER_20FT)(l=2000, w=2000, h=2000)
        items = [
            WeightedItem3D("A", 400, 400, 400, 6, "X", allow_rotate=False),
            WeightedItem3D("B", 400, 400, 400, 4, "X", allow_rotate=False),
            WeightedItem3D("C", 400, 400, 400, 6, "X", allow_rotate=False),
            WeightedItem3D("D", 400, 400, 400, 4, "X", allow_rotate=False),
        ]

        step6_summary = pack_min_bin_count_3d_by_destination(
            items,
            roomy_container,
            max_weight_kg=10,
            max_center_offset_mm=1000,
            min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
        )

        self.assertEqual(step6_summary.initial_bin_count, 2)
        self.assertEqual(step6_summary.bin_count, 2)

    def test_trial_pack_value_error_is_treated_as_infeasible_branch(self) -> None:
        roomy_container = type(CONTAINER_20FT)(l=2000, w=2000, h=2000)
        items = [
            WeightedItem3D("A", 400, 400, 400, 6, "X", allow_rotate=False),
            WeightedItem3D("B", 400, 400, 400, 4, "X", allow_rotate=False),
            WeightedItem3D("C", 400, 400, 400, 6, "X", allow_rotate=False),
            WeightedItem3D("D", 400, 400, 400, 4, "X", allow_rotate=False),
        ]

        original_helper = (
            "vanning.step6_bin_count_minimization_3d.pack_single_realistic_stable_bin"
        )

        from vanning.step6_bin_count_minimization_3d import pack_single_realistic_stable_bin as real_helper

        def flaky_helper(*args, **kwargs):
            bin_items = args[0]
            if len(bin_items) == 2 and sum(item.weight_kg for item in bin_items) == 10:
                raise ValueError("synthetic trial-pack failure")
            return real_helper(*args, **kwargs)

        with patch(original_helper, side_effect=flaky_helper):
            step6_summary = pack_min_bin_count_3d_by_destination(
                items,
                roomy_container,
                max_weight_kg=10,
                max_center_offset_mm=1000,
                min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
            )

        self.assertEqual(step6_summary.initial_bin_count, 2)
        self.assertEqual(step6_summary.bin_count, 2)

    def test_search_does_not_prune_partial_bucket_that_becomes_packable_later(self) -> None:
        roomy_container = type(CONTAINER_20FT)(l=2000, w=2000, h=2000)
        items = [
            WeightedItem3D("0", 400, 400, 400, 6, "X", allow_rotate=False),
            WeightedItem3D("1", 400, 400, 400, 4, "X", allow_rotate=False),
            WeightedItem3D("2", 400, 400, 400, 3, "X", allow_rotate=False),
            WeightedItem3D("3", 400, 400, 400, 3, "X", allow_rotate=False),
            WeightedItem3D("4", 400, 400, 400, 2, "X", allow_rotate=False),
            WeightedItem3D("5", 400, 400, 400, 2, "X", allow_rotate=False),
        ]

        original_helper = (
            "vanning.step6_bin_count_minimization_3d.pack_single_realistic_stable_bin"
        )

        valid_partitions = {
            frozenset({"0", "1"}),
            frozenset({"2", "3", "4", "5"}),
        }

        def non_monotonic_helper(*args, **kwargs):
            bin_items = args[0]
            key = frozenset(item.item_id for item in bin_items)
            if key in valid_partitions:
                return object()
            if key == frozenset({"2"}):
                return None
            return None

        with patch(original_helper, side_effect=non_monotonic_helper):
            packed_bins = _try_pack_items_into_bin_count(
                items,
                target_bin_count=2,
                container=roomy_container,
                max_weight_kg=10,
                max_center_offset_mm=1000,
                min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
            )

        self.assertIsNotNone(packed_bins)
        self.assertEqual(len(packed_bins), 2)

    def test_realdata_packing_is_valid_and_not_worse_than_step5(self) -> None:
        items = build_step3_weighted_realdata_items()
        step5_summary = pack_realistic_stable_3d_by_destination_ffd(
            items,
            CONTAINER_20FT,
            max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
            max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
            min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
        )
        step6_summary = pack_min_bin_count_3d_by_destination(
            items,
            CONTAINER_20FT,
            max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
            max_center_offset_mm=CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
            min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
        )

        self.assertEqual(step6_summary.total_weight_kg, sum(item.weight_kg for item in items))
        self.assertLessEqual(step6_summary.bin_count, step5_summary.bin_count)
        self.assertTrue(step6_summary.all_bins_within_center_constraint)
        for bin_ in step6_summary.bins:
            self.assertLessEqual(bin_.center_offset_mm, CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM)
            self.assertLessEqual(bin_.total_weight_kg, CONTAINER_20FT_MAX_PAYLOAD_KG)
            validate_realistic_stability(
                bin_.placements,
                min_support_area_ratio=STEP5_MIN_SUPPORT_AREA_RATIO,
            )


if __name__ == "__main__":
    unittest.main()

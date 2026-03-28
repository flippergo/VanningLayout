import unittest

from vanning.geometry import boxes_collide
from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    REALDATA_BOX_WEIGHTS_KG,
    build_step3_weighted_realdata_items,
    weight_for_box_id,
)
from vanning.step3_weighted_3d import (
    WeightedItem3D,
    assign_by_destination_and_weight_ffd,
    pack_weighted_3d_by_destination_ffd,
)


class Step3WeightedThreeDimensionalPackingTests(unittest.TestCase):
    def test_weight_lookup_covers_realdata(self) -> None:
        items = build_step3_weighted_realdata_items()
        self.assertEqual(len(items), len(REALDATA_BOX_WEIGHTS_KG))
        for item in items:
            self.assertEqual(item.weight_kg, weight_for_box_id(item.item_id))

    def test_weight_assignment_respects_dest_and_capacity(self) -> None:
        items = [
            WeightedItem3D("X1", 1, 1, 1, 7, "X"),
            WeightedItem3D("X2", 1, 1, 1, 5, "X"),
            WeightedItem3D("X3", 1, 1, 1, 4, "X"),
            WeightedItem3D("Y1", 1, 1, 1, 8, "Y"),
        ]

        summary = assign_by_destination_and_weight_ffd(items, max_weight_kg=12)

        self.assertEqual(summary.bin_count, 3)
        for bin_ in summary.bins:
            self.assertLessEqual(bin_.total_weight_kg, 12)
            self.assertTrue(all(item.dest == bin_.dest for item in bin_.items))

    def test_weighted_packing_splits_by_weight_even_when_space_is_available(self) -> None:
        roomy_container = type(CONTAINER_20FT)(l=6000, w=3000, h=3000)
        items = [
            WeightedItem3D("A1", 1000, 1000, 1000, 7, "X", allow_rotate=False),
            WeightedItem3D("A2", 1000, 1000, 1000, 7, "X", allow_rotate=False),
            WeightedItem3D("A3", 1000, 1000, 1000, 5, "X", allow_rotate=False),
        ]

        summary = pack_weighted_3d_by_destination_ffd(items, roomy_container, max_weight_kg=12)

        self.assertEqual(summary.bin_count, 2)
        for bin_ in summary.bins:
            self.assertLessEqual(bin_.total_weight_kg, 12)

    def test_duplicate_item_ids_preserve_individual_weights(self) -> None:
        roomy_container = type(CONTAINER_20FT)(l=4000, w=2000, h=2000)
        items = [
            WeightedItem3D("DUP", 1000, 1000, 1000, 7, "X", allow_rotate=False),
            WeightedItem3D("DUP", 1000, 1000, 1000, 5, "X", allow_rotate=False),
        ]

        summary = pack_weighted_3d_by_destination_ffd(items, roomy_container, max_weight_kg=20)

        self.assertEqual(summary.bin_count, 1)
        self.assertEqual(summary.bins[0].total_weight_kg, 12)
        self.assertCountEqual(
            [placement.item.weight_kg for placement in summary.bins[0].placements],
            [7, 5],
        )

    def test_realdata_weighted_packing_is_valid(self) -> None:
        items = build_step3_weighted_realdata_items()
        summary = pack_weighted_3d_by_destination_ffd(
            items,
            CONTAINER_20FT,
            max_weight_kg=CONTAINER_20FT_MAX_PAYLOAD_KG,
        )

        self.assertGreater(summary.bin_count, 0)
        self.assertEqual(sum(len(bin_.placements) for bin_ in summary.bins), len(items))

        for bin_ in summary.bins:
            self.assertLessEqual(bin_.total_weight_kg, CONTAINER_20FT_MAX_PAYLOAD_KG)
            self.assertTrue(all(placement.item.dest == bin_.dest for placement in bin_.placements))
            for placement in bin_.placements:
                self.assertGreaterEqual(placement.x, 0)
                self.assertGreaterEqual(placement.y, 0)
                self.assertGreaterEqual(placement.z, 0)
                self.assertLessEqual(placement.box.x_max, CONTAINER_20FT.l)
                self.assertLessEqual(placement.box.y_max, CONTAINER_20FT.w)
                self.assertLessEqual(placement.box.z_max, CONTAINER_20FT.h)
            for i in range(len(bin_.placements)):
                for j in range(i + 1, len(bin_.placements)):
                    self.assertFalse(boxes_collide(bin_.placements[i].box, bin_.placements[j].box))


if __name__ == "__main__":
    unittest.main()

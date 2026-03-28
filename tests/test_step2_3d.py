import unittest

from vanning.geometry import boxes_collide
from vanning.problem_spec import CONTAINER_20FT, build_step2_3d_realdata_items
from vanning.step2_3d import Bin3D, Item3D, pack_3d_by_destination_ffd


class Step2ThreeDimensionalPackingTests(unittest.TestCase):
    def test_destination_is_never_mixed_in_a_bin(self) -> None:
        items = [
            Item3D("X1", length=1400, width=1000, height=800, dest="X"),
            Item3D("X2", length=1200, width=900, height=700, dest="X"),
            Item3D("Y1", length=1400, width=1000, height=800, dest="Y"),
        ]
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        for bin_ in summary.bins:
            self.assertTrue(all(placement.item.dest == bin_.dest for placement in bin_.placements))

    def test_placements_are_inside_and_non_overlapping(self) -> None:
        items = [
            Item3D("A1", length=1400, width=1000, height=800, dest="X"),
            Item3D("B1", length=1200, width=900, height=700, dest="X"),
            Item3D("C1", length=800, width=600, height=600, dest="X"),
            Item3D("C2", length=800, width=600, height=600, dest="X"),
        ]
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        self.assertEqual(summary.bin_count, 1)
        placements = summary.bins[0].placements
        for placement in placements:
            self.assertGreaterEqual(placement.x, 0)
            self.assertGreaterEqual(placement.y, 0)
            self.assertGreaterEqual(placement.z, 0)
            self.assertLessEqual(placement.box.x_max, CONTAINER_20FT.l)
            self.assertLessEqual(placement.box.y_max, CONTAINER_20FT.w)
            self.assertLessEqual(placement.box.z_max, CONTAINER_20FT.h)

        for i in range(len(placements)):
            for j in range(i + 1, len(placements)):
                self.assertFalse(boxes_collide(placements[i].box, placements[j].box))

    def test_stacking_support_rule(self) -> None:
        small_container = type(CONTAINER_20FT)(l=1200, w=900, h=1400)
        items = [
            Item3D("B1", length=1200, width=900, height=700, dest="X"),
            Item3D("B2", length=1200, width=900, height=700, dest="X"),
        ]
        summary = pack_3d_by_destination_ffd(items, small_container)
        placements = summary.bins[0].placements

        self.assertTrue(any(placement.z > 0 for placement in placements))
        for placement in placements:
            if placement.z == 0:
                continue
            supporters = [
                other
                for other in placements
                if other is not placement
                and other.box.z_max == placement.z
                and other.x <= placement.x
                and placement.box.x_max <= other.box.x_max
                and other.y <= placement.y
                and placement.box.y_max <= other.box.y_max
            ]
            self.assertTrue(supporters, msg=f"{placement.item.item_id} at z={placement.z} is unsupported")

    def test_rejects_bridging_across_two_support_boxes(self) -> None:
        bridge_container = type(CONTAINER_20FT)(l=1200, w=900, h=1500)
        bin_ = Bin3D(container=bridge_container, dest="X")

        self.assertTrue(bin_.add(Item3D("L", length=600, width=900, height=700, dest="X", allow_rotate=False)))
        self.assertTrue(bin_.add(Item3D("R", length=600, width=900, height=700, dest="X", allow_rotate=False)))
        self.assertFalse(
            bin_.add(Item3D("TOP", length=1200, width=900, height=700, dest="X", allow_rotate=False))
        )

    def test_rejects_overhang_when_support_is_smaller(self) -> None:
        overhang_container = type(CONTAINER_20FT)(l=900, w=900, h=1500)
        bin_ = Bin3D(container=overhang_container, dest="X")

        self.assertTrue(
            bin_.add(Item3D("BASE", length=800, width=900, height=700, dest="X", allow_rotate=False))
        )
        self.assertFalse(
            bin_.add(Item3D("TOP", length=900, width=900, height=700, dest="X", allow_rotate=False))
        )

    def test_bin_add_rejects_destination_mismatch(self) -> None:
        bin_ = Bin3D(container=CONTAINER_20FT, dest="X")
        self.assertFalse(bin_.add(Item3D("Y1", length=1000, width=800, height=600, dest="Y")))

    def test_bin_add_rejects_non_positive_dimensions(self) -> None:
        bin_ = Bin3D(container=CONTAINER_20FT, dest="X")
        self.assertFalse(bin_.add(Item3D("ZERO", length=0, width=800, height=600, dest="X")))
        self.assertFalse(bin_.add(Item3D("NEG", length=1000, width=800, height=-1, dest="X")))

    def test_packing_prefers_single_bin_when_stacking_avoids_extra_bin(self) -> None:
        container = type(CONTAINER_20FT)(l=3, w=3, h=2)
        items = [
            Item3D("A", length=1, width=1, height=2, dest="X", allow_rotate=False),
            Item3D("B", length=3, width=1, height=1, dest="X", allow_rotate=False),
            Item3D("C", length=3, width=2, height=1, dest="X", allow_rotate=False),
        ]

        summary = pack_3d_by_destination_ffd(items, container)

        self.assertEqual(summary.bin_count, 1)

    def test_realdata_3d_packing_is_valid(self) -> None:
        items = build_step2_3d_realdata_items()
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        self.assertGreater(summary.bin_count, 0)
        self.assertEqual(sum(len(bin_.placements) for bin_ in summary.bins), len(items))

        for bin_ in summary.bins:
            self.assertTrue(all(placement.item.dest == bin_.dest for placement in bin_.placements))
            for i in range(len(bin_.placements)):
                for j in range(i + 1, len(bin_.placements)):
                    self.assertFalse(boxes_collide(bin_.placements[i].box, bin_.placements[j].box))


if __name__ == "__main__":
    unittest.main()

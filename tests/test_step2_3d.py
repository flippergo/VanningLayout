import unittest

from vanning.geometry import boxes_collide
from vanning.problem_spec import CONTAINER_20FT, build_step2_3d_realdata_items
from vanning.step2_3d import Item3D, pack_3d_by_destination_ffd


class Step2ThreeDimensionalPackingTests(unittest.TestCase):
    def test_destination_is_never_mixed_in_a_bin(self) -> None:
        items = [
            Item3D("X1", length=1400, width=1000, height=800, dest="X"),
            Item3D("X2", length=1200, width=900, height=700, dest="X"),
            Item3D("Y1", length=1400, width=1000, height=800, dest="Y"),
        ]
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        for bin_ in summary.bins:
            self.assertTrue(all(p.item.dest == bin_.dest for p in bin_.placements))

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
        for p in placements:
            self.assertGreaterEqual(p.x, 0)
            self.assertGreaterEqual(p.y, 0)
            self.assertGreaterEqual(p.z, 0)
            self.assertLessEqual(p.box.x_max, CONTAINER_20FT.l)
            self.assertLessEqual(p.box.y_max, CONTAINER_20FT.w)
            self.assertLessEqual(p.box.z_max, CONTAINER_20FT.h)

        for i in range(len(placements)):
            for j in range(i + 1, len(placements)):
                self.assertFalse(boxes_collide(placements[i].box, placements[j].box))

    def test_stacking_support_rule(self) -> None:
        # 床面が狭いコンテナを使い、必ず積み上げが発生するケースを作る。
        small_container = type(CONTAINER_20FT)(l=1200, w=900, h=1400)
        items = [
            Item3D("B1", length=1200, width=900, height=700, dest="X"),
            Item3D("B2", length=1200, width=900, height=700, dest="X"),
        ]
        summary = pack_3d_by_destination_ffd(items, small_container)
        placements = summary.bins[0].placements

        self.assertTrue(any(p.z > 0 for p in placements))
        for p in placements:
            if p.z == 0:
                continue
            supported = False
            for other in placements:
                if other is p or other.box.z_max != p.z:
                    continue
                x_overlap = min(other.box.x_max, p.box.x_max) - max(other.x, p.x)
                y_overlap = min(other.box.y_max, p.box.y_max) - max(other.y, p.y)
                if x_overlap > 0 and y_overlap > 0:
                    supported = True
                    break
            self.assertTrue(supported, msg=f"{p.item.item_id} at z={p.z} is unsupported")

    def test_realdata_3d_packing_is_valid(self) -> None:
        items = build_step2_3d_realdata_items()
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        self.assertGreater(summary.bin_count, 0)
        self.assertEqual(sum(len(bin_.placements) for bin_ in summary.bins), len(items))

        for bin_ in summary.bins:
            self.assertTrue(all(p.item.dest == bin_.dest for p in bin_.placements))
            for i in range(len(bin_.placements)):
                for j in range(i + 1, len(bin_.placements)):
                    self.assertFalse(boxes_collide(bin_.placements[i].box, bin_.placements[j].box))


if __name__ == "__main__":
    unittest.main()

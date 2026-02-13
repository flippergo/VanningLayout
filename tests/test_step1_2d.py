import unittest

from vanning.step1_2d import Item2D, pack_2d_by_destination_ffd


def _placements_overlap(a, b) -> bool:
    return a.x < b.x_max and a.x_max > b.x and a.y < b.y_max and a.y_max > b.y


class Step1TwoDimensionalPackingTests(unittest.TestCase):
    def test_destination_is_never_mixed_in_a_bin(self) -> None:
        items = [
            Item2D("X1", length=4, width=2, dest="X"),
            Item2D("X2", length=2, width=2, dest="X"),
            Item2D("Y1", length=3, width=2, dest="Y"),
            Item2D("Y2", length=2, width=1, dest="Y"),
        ]
        result = pack_2d_by_destination_ffd(items, bin_length=6, bin_width=4)

        for bin_ in result.bins:
            self.assertTrue(all(placement.item.dest == bin_.dest for placement in bin_.placements))

    def test_all_placements_are_inside_and_non_overlapping(self) -> None:
        items = [
            Item2D("A1", length=4, width=2, dest="X"),
            Item2D("A2", length=2, width=2, dest="X"),
            Item2D("A3", length=2, width=2, dest="X"),
            Item2D("A4", length=2, width=2, dest="X"),
        ]
        result = pack_2d_by_destination_ffd(items, bin_length=6, bin_width=4)

        self.assertEqual(result.bin_count, 1)
        placements = result.bins[0].placements
        for placement in placements:
            self.assertGreaterEqual(placement.x, 0)
            self.assertGreaterEqual(placement.y, 0)
            self.assertLessEqual(placement.x_max, 6)
            self.assertLessEqual(placement.y_max, 4)

        for i in range(len(placements)):
            for j in range(i + 1, len(placements)):
                self.assertFalse(_placements_overlap(placements[i], placements[j]))

    def test_rotation_case_can_be_packed(self) -> None:
        items = [Item2D("R1", length=3, width=4, dest="X", allow_rotate=True)]
        result = pack_2d_by_destination_ffd(items, bin_length=4, bin_width=3)

        self.assertEqual(result.bin_count, 1)
        placement = result.bins[0].placements[0]
        self.assertTrue(placement.rotated)
        self.assertEqual((placement.length, placement.width), (4, 3))

    def test_simple_case_expected_bin_count(self) -> None:
        items = [
            Item2D("X1", length=5, width=3, dest="X"),
            Item2D("X2", length=5, width=2, dest="X"),
            Item2D("Y1", length=4, width=4, dest="Y"),
        ]
        result = pack_2d_by_destination_ffd(items, bin_length=5, bin_width=4)
        self.assertEqual(result.bin_count, 3)

    def test_invalid_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            pack_2d_by_destination_ffd(
                [Item2D("bad-dim", length=0, width=1, dest="X")], bin_length=5, bin_width=4
            )
        with self.assertRaises(ValueError):
            pack_2d_by_destination_ffd(
                [Item2D("bad-dest", length=1, width=1, dest="")], bin_length=5, bin_width=4
            )
        with self.assertRaises(ValueError):
            pack_2d_by_destination_ffd(
                [Item2D("too-large", length=6, width=5, dest="X")], bin_length=5, bin_width=4
            )
        with self.assertRaises(ValueError):
            pack_2d_by_destination_ffd(
                [Item2D("need-rotate", length=3, width=4, dest="X", allow_rotate=False)],
                bin_length=4,
                bin_width=3,
            )
        with self.assertRaises(ValueError):
            pack_2d_by_destination_ffd([Item2D("ok", length=1, width=1, dest="X")], 0, 3)


if __name__ == "__main__":
    unittest.main()

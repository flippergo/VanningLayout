import unittest

from vanning.step1_1d import Item1D, pack_1d_by_destination_ffd


class Step1OneDimensionalPackingTests(unittest.TestCase):
    def test_destination_is_never_mixed_in_a_bin(self) -> None:
        items = [
            Item1D("A01", length=3000, dest="X"),
            Item1D("A02", length=2500, dest="X"),
            Item1D("B01", length=3200, dest="Y"),
            Item1D("B02", length=2000, dest="Y"),
        ]
        result = pack_1d_by_destination_ffd(items, bin_capacity=5898)

        for bin_ in result.bins:
            self.assertTrue(all(item.dest == bin_.dest for item in bin_.items))

    def test_capacity_is_respected(self) -> None:
        items = [
            Item1D("X1", length=3000, dest="X"),
            Item1D("X2", length=2900, dest="X"),
            Item1D("X3", length=1000, dest="X"),
        ]
        result = pack_1d_by_destination_ffd(items, bin_capacity=5898)

        for bin_ in result.bins:
            self.assertLessEqual(bin_.used_length, 5898)

    def test_simple_case_expected_bin_count(self) -> None:
        items = [
            Item1D("X1", length=4000, dest="X"),
            Item1D("X2", length=2000, dest="X"),
            Item1D("Y1", length=3500, dest="Y"),
            Item1D("Y2", length=3000, dest="Y"),
        ]
        # X requires 2 bins, Y requires 2 bins -> total 4 bins under capacity 5898.
        result = pack_1d_by_destination_ffd(items, bin_capacity=5898)
        self.assertEqual(result.bin_count, 4)

    def test_invalid_item_length_raises(self) -> None:
        with self.assertRaises(ValueError):
            pack_1d_by_destination_ffd([Item1D("bad", length=0, dest="X")], bin_capacity=100)

    def test_item_too_long_raises(self) -> None:
        with self.assertRaises(ValueError):
            pack_1d_by_destination_ffd([Item1D("too-long", length=101, dest="X")], bin_capacity=100)


if __name__ == "__main__":
    unittest.main()

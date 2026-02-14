import tempfile
import unittest
from collections import Counter
from pathlib import Path

from vanning.problem_spec import (
    BOX_DIMS,
    CONTAINER_20FT,
    box_type_from_id,
    build_step1_2d_realdata_items,
    destination_for_box_id,
    realdata_box_ids,
)
from vanning.step1_2d import pack_2d_by_destination_ffd
from vanning.step1_2d_visualization import save_packing_summary_svgs


def _placements_overlap(a, b) -> bool:
    return a.x < b.x_max and a.x_max > b.x and a.y < b.y_max and a.y_max > b.y


class Step1TwoDimensionalRealDataTests(unittest.TestCase):
    def test_realdata_ids_and_destinations(self) -> None:
        ids = realdata_box_ids()
        self.assertEqual(len(ids), 80)
        self.assertEqual(ids[0], "A01")
        self.assertEqual(ids[-1], "C20")

        dest_counts = Counter(destination_for_box_id(item_id) for item_id in ids)
        self.assertEqual(dest_counts["X"], 40)
        self.assertEqual(dest_counts["Y"], 40)

    def test_realdata_item_build(self) -> None:
        items = build_step1_2d_realdata_items()
        self.assertEqual(len(items), 80)

        for item in items:
            box_type = box_type_from_id(item.item_id)
            length, width, _ = BOX_DIMS[box_type]
            self.assertEqual((item.length, item.width), (float(length), float(width)))
            self.assertIn(item.dest, {"X", "Y"})

    def test_realdata_2d_packing_is_valid(self) -> None:
        items = build_step1_2d_realdata_items()
        summary = pack_2d_by_destination_ffd(
            items,
            bin_length=CONTAINER_20FT.l,
            bin_width=CONTAINER_20FT.w,
        )

        self.assertGreater(summary.bin_count, 0)

        for bin_ in summary.bins:
            self.assertTrue(all(p.item.dest == bin_.dest for p in bin_.placements))
            for placement in bin_.placements:
                self.assertGreaterEqual(placement.x, 0)
                self.assertGreaterEqual(placement.y, 0)
                self.assertLessEqual(placement.x_max, CONTAINER_20FT.l)
                self.assertLessEqual(placement.y_max, CONTAINER_20FT.w)

            for i in range(len(bin_.placements)):
                for j in range(i + 1, len(bin_.placements)):
                    self.assertFalse(_placements_overlap(bin_.placements[i], bin_.placements[j]))

    def test_realdata_visualization_svg_generation(self) -> None:
        items = build_step1_2d_realdata_items()
        summary = pack_2d_by_destination_ffd(
            items,
            bin_length=CONTAINER_20FT.l,
            bin_width=CONTAINER_20FT.w,
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            files = save_packing_summary_svgs(summary, output_dir)
            self.assertEqual(len(files), summary.bin_count)
            for file_path in files:
                self.assertTrue(file_path.exists())
                content = file_path.read_text(encoding="utf-8")
                self.assertIn("<svg", content)
                self.assertIn("Bin", content)


if __name__ == "__main__":
    unittest.main()

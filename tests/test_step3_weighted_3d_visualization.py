import unittest
from pathlib import Path
import shutil

from vanning.geometry import Container
from vanning.step3_weighted_3d import WeightedItem3D, pack_weighted_3d_by_destination_ffd
from vanning.step3_weighted_3d_visualization import (
    render_weighted_bin_isometric_svg,
    render_weighted_bin_orthographic_svg,
    save_weighted_packing_summary_isometric_svgs,
    save_weighted_packing_summary_svgs,
)


class Step3WeightedThreeDimensionalVisualizationTests(unittest.TestCase):
    def _build_summary(self):
        container = Container(l=6, w=4, h=3)
        items = [
            WeightedItem3D("A", 2, 2, 3, 5, "X", allow_rotate=False),
            WeightedItem3D("B", 6, 2, 1, 4, "X", allow_rotate=False),
            WeightedItem3D("C", 6, 2, 2, 3, "X", allow_rotate=False),
        ]
        return pack_weighted_3d_by_destination_ffd(items, container, max_weight_kg=12)

    def test_render_weighted_bin_orthographic_svg_contains_expected_labels(self) -> None:
        summary = self._build_summary()

        svg = render_weighted_bin_orthographic_svg(summary.bins[0], title="Weighted Demo")

        self.assertIn("<svg", svg)
        self.assertIn("Weighted Demo", svg)
        self.assertIn("Top (X-Y)", svg)
        self.assertIn("A", svg)

    def test_render_weighted_bin_isometric_svg_contains_expected_labels(self) -> None:
        summary = self._build_summary()

        svg = render_weighted_bin_isometric_svg(summary.bins[0], title="Weighted Isometric Demo")

        self.assertIn("<svg", svg)
        self.assertIn("Weighted Isometric Demo", svg)
        self.assertIn("polygon", svg)
        self.assertIn("A", svg)

    def test_save_weighted_packing_summary_svgs_writes_files(self) -> None:
        summary = self._build_summary()
        output_dir = Path("artifacts/test_step3_weighted_3d_visualization")
        if output_dir.exists():
            shutil.rmtree(output_dir)

        files = save_weighted_packing_summary_svgs(summary, output_dir, prefix="weighted_viz_test")

        self.assertEqual(len(files), summary.bin_count)
        for file_path in files:
            self.assertTrue(file_path.exists())
            content = file_path.read_text(encoding="utf-8")
            self.assertIn("<svg", content)
            self.assertIn("kg", content)

    def test_save_weighted_packing_summary_isometric_svgs_writes_files(self) -> None:
        summary = self._build_summary()
        output_dir = Path("artifacts/test_step3_weighted_3d_isometric_visualization")
        if output_dir.exists():
            shutil.rmtree(output_dir)

        files = save_weighted_packing_summary_isometric_svgs(summary, output_dir, prefix="weighted_viz_iso_test")

        self.assertEqual(len(files), summary.bin_count)
        for file_path in files:
            self.assertTrue(file_path.exists())
            content = file_path.read_text(encoding="utf-8")
            self.assertIn("<svg", content)
            self.assertIn("isometric", content)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
import shutil

from vanning.geometry import Container
from vanning.step3_weighted_3d import WeightedItem3D
from vanning.step4_center_of_gravity_3d import pack_center_balanced_3d_by_destination_ffd
from vanning.step4_center_of_gravity_3d_visualization import (
    render_center_balance_topdown_svg,
    render_center_balanced_bin_isometric_svg,
    render_center_balanced_bin_orthographic_svg,
    save_center_balance_topdown_svgs,
    save_center_balanced_packing_summary_isometric_svgs,
    save_center_balanced_packing_summary_svgs,
)


class Step4CenterOfGravityThreeDimensionalVisualizationTests(unittest.TestCase):
    def _build_summary(self):
        container = Container(l=9000, w=7000, h=3000)
        items = [
            WeightedItem3D("A", 2000, 2000, 3000, 5, "X", allow_rotate=False),
            WeightedItem3D("B", 6000, 2000, 1000, 4, "X", allow_rotate=False),
            WeightedItem3D("C", 6000, 2000, 2000, 3, "X", allow_rotate=False),
        ]
        return pack_center_balanced_3d_by_destination_ffd(items, container, max_weight_kg=12, max_center_offset_mm=300)

    def test_render_center_balance_topdown_svg_contains_expected_markers(self) -> None:
        summary = self._build_summary()

        svg = render_center_balance_topdown_svg(summary.bins[0], title="Center Demo")

        self.assertIn("<svg", svg)
        self.assertIn("Center Demo", svg)
        self.assertIn("circle", svg)
        self.assertIn("Blue: allowed center region", svg)

    def test_render_center_balanced_bin_views_contain_expected_labels(self) -> None:
        summary = self._build_summary()

        ortho_svg = render_center_balanced_bin_orthographic_svg(summary.bins[0], title="Ortho Demo")
        iso_svg = render_center_balanced_bin_isometric_svg(summary.bins[0], title="Iso Demo")

        self.assertIn("Ortho Demo", ortho_svg)
        self.assertIn("A", ortho_svg)
        self.assertIn("Iso Demo", iso_svg)
        self.assertIn("polygon", iso_svg)

    def test_save_center_balance_svgs_write_files(self) -> None:
        summary = self._build_summary()
        ortho_dir = Path("artifacts/test_step4_center_balance_visualization")
        iso_dir = Path("artifacts/test_step4_center_balance_isometric_visualization")
        top_dir = Path("artifacts/test_step4_center_balance_topdown_visualization")
        for output_dir in (ortho_dir, iso_dir, top_dir):
            if output_dir.exists():
                shutil.rmtree(output_dir)

        ortho_files = save_center_balanced_packing_summary_svgs(summary, ortho_dir, prefix="step4_viz_test")
        iso_files = save_center_balanced_packing_summary_isometric_svgs(summary, iso_dir, prefix="step4_viz_iso_test")
        top_files = save_center_balance_topdown_svgs(summary, top_dir, prefix="step4_viz_top_test")

        self.assertEqual(len(ortho_files), summary.bin_count)
        self.assertEqual(len(iso_files), summary.bin_count)
        self.assertEqual(len(top_files), summary.bin_count)
        self.assertIn("offset", ortho_files[0].read_text(encoding="utf-8"))
        self.assertIn("isometric", iso_files[0].read_text(encoding="utf-8"))
        self.assertIn("Center offset", top_files[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

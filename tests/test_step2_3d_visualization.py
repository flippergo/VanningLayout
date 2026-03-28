import unittest
from pathlib import Path
import shutil

from vanning.problem_spec import CONTAINER_20FT
from vanning.step2_3d import Item3D, pack_3d_by_destination_ffd
from vanning.step2_3d_visualization import (
    render_bin_isometric_svg,
    render_bin_orthographic_svg,
    save_packing_summary_isometric_svgs,
    save_packing_summary_svgs,
)


class Step2ThreeDimensionalVisualizationTests(unittest.TestCase):
    def test_render_bin_orthographic_svg_contains_expected_labels(self) -> None:
        items = [
            Item3D("A1", length=1400, width=1000, height=800, dest="X"),
            Item3D("B1", length=1200, width=900, height=700, dest="X"),
        ]
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        svg = render_bin_orthographic_svg(summary.bins[0], title="Demo")

        self.assertIn("<svg", svg)
        self.assertIn("Top (X-Y)", svg)
        self.assertIn("Front (X-Z)", svg)
        self.assertIn("Side (Y-Z)", svg)
        self.assertIn("A1", svg)
        self.assertIn("B1", svg)

    def test_save_packing_summary_svgs_writes_files(self) -> None:
        items = [
            Item3D("A1", length=1400, width=1000, height=800, dest="X"),
            Item3D("B1", length=1200, width=900, height=700, dest="X"),
        ]
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        output_dir = Path("artifacts/test_step2_3d_visualization")
        if output_dir.exists():
            shutil.rmtree(output_dir)

        files = save_packing_summary_svgs(summary, output_dir, prefix="viz_test")
        self.assertEqual(len(files), summary.bin_count)
        for file_path in files:
            self.assertTrue(file_path.exists())
            content = file_path.read_text(encoding="utf-8")
            self.assertIn("<svg", content)
            self.assertIn("Bin", content)

    def test_render_bin_isometric_svg_contains_expected_labels(self) -> None:
        items = [
            Item3D("A1", length=1400, width=1000, height=800, dest="X"),
            Item3D("B1", length=1200, width=900, height=700, dest="X"),
        ]
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        svg = render_bin_isometric_svg(summary.bins[0], title="Isometric Demo")

        self.assertIn("<svg", svg)
        self.assertIn("Isometric Demo", svg)
        self.assertIn("A1", svg)
        self.assertIn("B1", svg)
        self.assertIn("polygon", svg)

    def test_save_packing_summary_isometric_svgs_writes_files(self) -> None:
        items = [
            Item3D("A1", length=1400, width=1000, height=800, dest="X"),
            Item3D("B1", length=1200, width=900, height=700, dest="X"),
        ]
        summary = pack_3d_by_destination_ffd(items, CONTAINER_20FT)

        output_dir = Path("artifacts/test_step2_3d_isometric_visualization")
        if output_dir.exists():
            shutil.rmtree(output_dir)

        files = save_packing_summary_isometric_svgs(summary, output_dir, prefix="viz_iso_test")
        self.assertEqual(len(files), summary.bin_count)
        for file_path in files:
            self.assertTrue(file_path.exists())
            content = file_path.read_text(encoding="utf-8")
            self.assertIn("<svg", content)
            self.assertIn("isometric", content)


if __name__ == "__main__":
    unittest.main()

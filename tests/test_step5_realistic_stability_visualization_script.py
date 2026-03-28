import unittest
from pathlib import Path
import shutil

from scripts.generate_step5_realistic_stability_explanation import main


class Step5RealisticStabilityVisualizationScriptTests(unittest.TestCase):
    def test_generate_step5_explanation_writes_expected_files(self) -> None:
        output_dir = Path("artifacts/step5_realistic_stability_explanation")
        if output_dir.exists():
            shutil.rmtree(output_dir)

        main()

        report_path = output_dir / "README.md"
        self.assertTrue(report_path.exists())
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("Step5 現実寄り安定条件つき 3D 配置の説明", content)
        self.assertIn("支持面積率", content)

        example_dir = output_dir / "example"
        realdata_dir = output_dir / "realdata"
        self.assertTrue(any(example_dir.glob("*.svg")))
        self.assertTrue(any(realdata_dir.glob("*.svg")))


if __name__ == "__main__":
    unittest.main()

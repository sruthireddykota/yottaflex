import unittest

from app.services.generator import generate
from app.services.validation import validate


class GeneratorTests(unittest.TestCase):
    def test_generation_is_reproducible(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            first = __import__("pathlib").Path(folder) / "first"
            second = __import__("pathlib").Path(folder) / "second"
            manifest_a = generate(first, assets=10, shipments=5, custody_events=20)
            manifest_b = generate(second, assets=10, shipments=5, custody_events=20)
            self.assertEqual(manifest_a["counts"], manifest_b["counts"])
            self.assertEqual(manifest_a["ground_truth_count"], 5)


    def test_validation_detects_labelled_exceptions(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            generate(folder, assets=10, shipments=5, custody_events=20)
            summary = validate(folder)
            self.assertTrue(summary["valid"])
            self.assertIn("custody_missing_actor", summary["ground_truth_issue_types"])
            self.assertEqual(summary["detected_issue_counts"]["custody_missing_actor"], 1)


if __name__ == "__main__":
    unittest.main()

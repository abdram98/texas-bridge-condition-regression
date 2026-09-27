"""Tests for bridge data preparation and model evaluation."""

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.bridge_analysis import (  # noqa: E402
    ALL_COMPLETE,
    FILTERED_SCOPE,
    coefficient_table,
    evaluate_regression,
    load_bridge_data,
    prepare_bridge_data,
    validate_bridge_data,
)


DATA_PATH = PROJECT_ROOT / "data" / "raw" / "tx19_bridges_sample.csv"


class BridgeAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = load_bridge_data(DATA_PATH)

    def test_source_shape_and_identifiers(self) -> None:
        summary = validate_bridge_data(self.raw)
        self.assertEqual(summary["rows"], 34_293)
        self.assertEqual(summary["columns"], 25)
        self.assertEqual(summary["duplicate_structure_ids"], 0)

    def test_complete_record_preparation(self) -> None:
        prepared = prepare_bridge_data(self.raw, scope=ALL_COMPLETE)
        self.assertEqual(len(prepared), 34_286)
        self.assertEqual(prepared["Age"].min(), 0)
        self.assertEqual(prepared["Age"].max(), 119)
        self.assertEqual(prepared["Current_Condition"].min(), 0)
        self.assertEqual(prepared["Current_Condition"].max(), 27)

    def test_filtered_scope_uses_2019_age(self) -> None:
        prepared = prepare_bridge_data(self.raw, scope=FILTERED_SCOPE)
        self.assertEqual(len(prepared), 31_905)
        self.assertLess(prepared["Age"].max(), 80)
        self.assertNotIn("Register", set(prepared["Historic"]))

    def test_model_evaluation_is_out_of_sample(self) -> None:
        prepared = prepare_bridge_data(self.raw, scope=FILTERED_SCOPE)
        result = evaluate_regression(prepared, scope=FILTERED_SCOPE)
        self.assertAlmostEqual(result.holdout_r2, 0.4556, places=3)
        self.assertAlmostEqual(result.holdout_rmse, 1.4336, places=3)
        self.assertAlmostEqual(result.cv_r2_mean, 0.4552, places=3)

    def test_coefficients_are_labelled(self) -> None:
        prepared = prepare_bridge_data(self.raw, scope=FILTERED_SCOPE)
        result = evaluate_regression(prepared, scope=FILTERED_SCOPE)
        labels = set(coefficient_table(result)["Predictor"])
        self.assertEqual(
            labels,
            {
                "Age",
                "AverageDaily",
                "Trucks_percent",
                "Material: Other",
                "Material: Steel",
                "Design: Other",
                "Design: Slab",
            },
        )


if __name__ == "__main__":
    unittest.main()

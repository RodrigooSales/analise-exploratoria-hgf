import hashlib
import unittest
from pathlib import Path

import pandas as pd

from src.variables import classificar_findrisc, classificar_imc


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "01_data_cleaning.ipynb"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class DataCleaningPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PROCESSED_PATH.exists():
            raise AssertionError(f"Dataset processado ausente: {PROCESSED_PATH}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.processed = pd.read_csv(PROCESSED_PATH)

    def test_required_artifacts_exist(self):
        self.assertTrue(NOTEBOOK_PATH.exists())
        self.assertTrue(PROCESSED_PATH.exists())

    def test_real_patient_count_and_identifiers(self):
        expected_ids = [f"P{number:03d}" for number in range(1, 76)]

        self.assertEqual(len(self.raw), 100)
        self.assertEqual(len(self.processed), 75)
        self.assertEqual(self.processed["patient_id"].tolist(), expected_ids)
        self.assertTrue(self.processed["patient_id"].is_unique)
        self.assertTrue(self.processed["patient_id"].str.fullmatch(r"P\d{3}").all())

    def test_processed_dataset_has_no_original_identifiers(self):
        normalized_columns = {column.strip().casefold() for column in self.processed.columns}
        self.assertNotIn("nome", normalized_columns)
        self.assertNotIn("cod", normalized_columns)

        patient_names = self.raw["nome"].dropna().str.strip()
        serialized = PROCESSED_PATH.read_text(encoding="utf-8").casefold()
        self.assertFalse(any(name.casefold() in serialized for name in patient_names if name))

    def test_original_diagnosis_is_preserved(self):
        valid = self.raw["nome"].notna() & self.raw["nome"].str.strip().ne("")
        expected = self.raw.loc[valid, "diagnóstico principal"].reset_index(drop=True)
        observed = self.processed["diagnostico_original"].astype("string")

        pd.testing.assert_series_equal(observed, expected, check_names=False)
        self.assertIn("diagnostico_padronizado", self.processed.columns)

    def test_imc_and_findrisc_are_numeric_and_reclassified(self):
        self.assertTrue(pd.api.types.is_numeric_dtype(self.processed["imc"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(self.processed["findrisc_score"]))
        self.assertEqual(self.processed["imc"].notna().sum(), 73)
        self.assertEqual(self.processed["findrisc_score"].notna().sum(), 74)

        expected_imc = self.processed["imc"].map(classificar_imc).astype("string")
        expected_findrisc = self.processed["findrisc_score"].map(classificar_findrisc).astype("string")
        pd.testing.assert_series_equal(
            self.processed["imc_categoria"].astype("string"), expected_imc, check_names=False
        )
        pd.testing.assert_series_equal(
            self.processed["findrisc_categoria"].astype("string"),
            expected_findrisc,
            check_names=False,
        )

    def test_derived_indicators_preserve_missing(self):
        for column in ["imc_categoria", "excesso_peso", "obesidade"]:
            self.assertEqual(self.processed[column].isna().sum(), 2)
        for column in ["findrisc_categoria", "findrisc_alto"]:
            self.assertEqual(self.processed[column].isna().sum(), 1)

    def test_completely_empty_source_variables_remain_missing(self):
        for column in ["altura", "peso", "basdai", "slicc", "das28"]:
            self.assertEqual(self.processed[column].notna().sum(), 0)

    def test_raw_dataset_is_unchanged(self):
        digest = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest()
        self.assertEqual(digest, RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

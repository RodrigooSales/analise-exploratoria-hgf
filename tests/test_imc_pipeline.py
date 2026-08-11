import unittest
from pathlib import Path

import nbformat
import pandas as pd

from src.cleaning import clean_numeric_column, clean_text_column


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "01_data_cleaning.ipynb"


class ImcPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(RAW_PATH)
        cls.processed = pd.read_csv(PROCESSED_PATH)

    def test_all_present_imc_values_are_converted_without_loss(self):
        valid_patient = clean_text_column(self.raw["nome"]).notna()
        raw_imc = self.raw.loc[valid_patient, "IMC"].reset_index(drop=True)
        expected = clean_numeric_column(raw_imc)

        pd.testing.assert_series_equal(
            self.processed["imc"], expected.astype(float), check_names=False
        )
        self.assertEqual(raw_imc.notna().sum(), expected.notna().sum())

    def test_imc_summary_and_category_counts(self):
        expected_counts = {
            "Baixo peso": 3,
            "Peso normal": 18,
            "Sobrepeso": 26,
            "Obesidade grau I": 15,
            "Obesidade grau II": 9,
            "Obesidade grau III": 2,
        }

        self.assertEqual(self.processed["imc"].notna().sum(), 73)
        self.assertEqual(self.processed["imc"].isna().sum(), 2)
        self.assertEqual(self.processed["imc"].min(), 17.5)
        self.assertEqual(self.processed["imc"].max(), 41.1)
        self.assertEqual(
            self.processed["imc_categoria"].value_counts().to_dict(), expected_counts
        )

    def test_no_impossible_or_iqr_extreme_values_are_removed(self):
        imc = self.processed["imc"].dropna()
        q1, q3 = imc.quantile([0.25, 0.75])
        iqr = q3 - q1
        iqr_extreme = ~imc.between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)

        self.assertTrue(imc.between(10, 80).all())
        self.assertEqual(int(iqr_extreme.sum()), 0)
        self.assertEqual(len(imc), 73)

    def test_executed_notebook_presents_complete_imc_validation(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        output_text = "\n".join(
            output.get("text", "")
            for cell in notebook.cells
            if cell.cell_type == "code"
            for output in cell.get("outputs", [])
            if output.get("output_type") == "stream"
        )

        for expected in [
            "Resumo de validação do IMC",
            "N com IMC válido: 73",
            "N sem IMC: 2",
            "Mínimo: 17.50",
            "Máximo: 41.10",
            "Falhas de conversão: 0",
            "Valores impossíveis: 0",
            "Extremos pelo critério de IQR: 0",
        ]:
            self.assertIn(expected, output_text)


if __name__ == "__main__":
    unittest.main()

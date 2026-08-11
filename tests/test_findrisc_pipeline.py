import unittest
import unicodedata
from pathlib import Path

import nbformat
import pandas as pd

from src.variables import extract_findrisc_score


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "01_data_cleaning.ipynb"


def normalize_label(value):
    if pd.isna(value):
        return pd.NA
    normalized = unicodedata.normalize("NFKD", str(value))
    return "".join(character for character in normalized if not unicodedata.combining(character)).strip().casefold()


class FindriscPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processed = pd.read_csv(PROCESSED_PATH)

    def test_score_is_extracted_from_original_field_without_loss(self):
        expected = extract_findrisc_score(self.processed["findrisc_original"])

        pd.testing.assert_series_equal(
            self.processed["findrisc_score"].astype("Int64"), expected, check_names=False
        )
        self.assertEqual(self.processed["findrisc_original"].notna().sum(), expected.notna().sum())

    def test_findrisc_summary_categories_and_high_risk_count(self):
        expected_counts = {
            "Alto": 20,
            "Leve/moderado": 18,
            "Muito alto": 15,
            "Moderado": 11,
            "Baixo risco": 10,
        }

        self.assertEqual(self.processed["findrisc_score"].notna().sum(), 74)
        self.assertEqual(self.processed["findrisc_score"].isna().sum(), 1)
        self.assertEqual(self.processed["findrisc_score"].min(), 2)
        self.assertEqual(self.processed["findrisc_score"].max(), 24)
        self.assertEqual(
            self.processed["findrisc_categoria"].value_counts().to_dict(), expected_counts
        )
        self.assertEqual(int(self.processed["findrisc_alto"].eq(True).sum()), 35)

    def test_original_label_divergences_are_identified(self):
        labels = (
            self.processed["findrisc_original"]
            .astype("string")
            .str.extract(r"\((.*?)\)", expand=False)
            .map(normalize_label)
        )
        strict_mapping = {
            "baixo risco": "Baixo risco",
            "leve/moderado": "Leve/moderado",
            "risco moderado": "Moderado",
            "moderado": "Moderado",
            "alto risco": "Alto",
            "muito alto risco": "Muito alto",
        }
        clinical_mapping = {**strict_mapping, "muito baixo risco": "Baixo risco"}
        strict_category = labels.map(strict_mapping)
        clinical_category = labels.map(clinical_mapping)
        labeled = labels.notna()

        strict_divergence = labeled & (
            strict_category.isna()
            | strict_category.ne(self.processed["findrisc_categoria"]).fillna(False)
        )
        clinical_divergence = labeled & clinical_category.ne(
            self.processed["findrisc_categoria"]
        ).fillna(False)

        self.assertEqual(int(labeled.sum()), 9)
        self.assertEqual(int(strict_category.isna().sum() - labels.isna().sum()), 1)
        self.assertEqual(int(strict_divergence.sum()), 3)
        self.assertEqual(int(clinical_divergence.sum()), 2)

    def test_executed_notebook_presents_complete_findrisc_validation(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        output_text = "\n".join(
            output.get("text", "")
            for cell in notebook.cells
            if cell.cell_type == "code"
            for output in cell.get("outputs", [])
            if output.get("output_type") == "stream"
        )

        for expected in [
            "Resumo de validação do FINDRISC",
            "N com FINDRISC válido: 74",
            "N sem FINDRISC: 1",
            "Mínimo: 2",
            "Máximo: 24",
            "FINDRISC ≥15: 35",
            "Rótulos originais presentes: 9",
            "Divergências estritas: 3",
            "Divergências clínicas: 2",
            "Rótulos não padronizados: 1",
        ]:
            self.assertIn(expected, output_text)


if __name__ == "__main__":
    unittest.main()

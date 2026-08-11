import hashlib
import re
import unittest
from pathlib import Path

import matplotlib.image as mpimg
import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "04_findrisc_analysis.ipynb"
FIGURES = [
    ROOT / "outputs" / "figures" / "findrisc_histogram_density.png",
    ROOT / "outputs" / "figures" / "findrisc_boxplot.png",
    ROOT / "outputs" / "figures" / "figure_2_findrisc_categories.png",
]
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class FindriscEdaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [path for path in [NOTEBOOK_PATH, *FIGURES] if not path.exists()]
        if missing:
            raise AssertionError(f"Artefatos da EDA de FINDRISC ausentes: {missing}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.processed = pd.read_csv(PROCESSED_PATH)

    def test_findrisc_descriptive_statistics(self):
        score = self.processed["findrisc_score"].dropna()

        self.assertEqual(len(score), 74)
        self.assertEqual(self.processed["findrisc_score"].isna().sum(), 1)
        self.assertAlmostEqual(score.mean(), 13.7567567568)
        self.assertEqual(score.mode().tolist(), [9])
        self.assertAlmostEqual(score.std(), 6.2544467706)
        self.assertEqual(score.median(), 14)
        self.assertEqual(score.quantile(0.25), 9)
        self.assertEqual(score.quantile(0.75), 19)
        self.assertEqual(score.min(), 2)
        self.assertEqual(score.max(), 24)

    def test_categories_and_high_findrisc_use_valid_denominator(self):
        expected_counts = {
            "Alto": 20,
            "Leve/moderado": 18,
            "Muito alto": 15,
            "Moderado": 11,
            "Baixo risco": 10,
        }

        self.assertEqual(self.processed["findrisc_categoria"].value_counts().to_dict(), expected_counts)
        high = self.processed["findrisc_alto"].astype("boolean").dropna()
        self.assertEqual(int(high.sum()), 35)
        self.assertAlmostEqual(100 * high.mean(), 47.2972972973)

    def test_extremes_and_instrument_range_are_assessed_without_exclusion(self):
        score = self.processed["findrisc_score"].dropna()
        q1, q3 = score.quantile([0.25, 0.75])
        iqr = q3 - q1
        outliers = ~score.between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)

        self.assertEqual(int(outliers.sum()), 0)
        self.assertTrue(score.between(0, 26).all())
        self.assertEqual(len(score), 74)

    def test_figures_are_high_resolution_and_nonempty(self):
        for figure_path in FIGURES:
            with self.subTest(figure=figure_path.name):
                image = mpimg.imread(figure_path)
                self.assertGreaterEqual(image.shape[0], 1000)
                self.assertGreaterEqual(image.shape[1], 1800)
                self.assertGreater(figure_path.stat().st_size, 10_000)

    def test_notebook_is_executed_and_answers_scientific_questions(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
        self.assertTrue(all(cell.execution_count is not None for cell in code_cells))
        self.assertFalse(
            any(output.get("output_type") == "error" for cell in code_cells for output in cell.get("outputs", []))
        )
        output_text = "\n".join(
            output.get("text", "")
            for cell in code_cells
            for output in cell.get("outputs", [])
            if output.get("output_type") == "stream"
        )
        for expected in [
            "FINDRISC válido: 74",
            "FINDRISC ausente: 1",
            "Categoria mais frequente: Alto — 20/74 (27,03%)",
            "FINDRISC ≥15: 35/74 (47,30%; IC95% de Wilson: 36,34%–58,52%)",
            "Extremos pelo critério de 1,5×IQR: 0",
            "Valores fora da faixa 0–26: 0",
            "Nenhum valor foi excluído.",
        ]:
            self.assertIn(expected, output_text)

        text_outputs = [output_text]
        text_outputs.extend(
            str(output.get("data", {}).get("text/plain", ""))
            for cell in code_cells
            for output in cell.get("outputs", [])
            if output.get("output_type") in {"display_data", "execute_result"}
        )
        self.assertIsNone(re.search(r"\bP\d{3}\b", "\n".join(text_outputs)))

    def test_artifacts_contain_no_patient_names_and_raw_is_unchanged(self):
        names = [name.casefold() for name in self.raw["nome"].dropna().str.strip() if name]
        notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8").casefold()

        self.assertFalse(any(name in notebook_text for name in names))
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

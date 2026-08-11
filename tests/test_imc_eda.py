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
NOTEBOOK_PATH = ROOT / "notebooks" / "03_imc_analysis.ipynb"
FIGURES = [
    ROOT / "outputs" / "figures" / "imc_histogram_density.png",
    ROOT / "outputs" / "figures" / "imc_boxplot.png",
    ROOT / "outputs" / "figures" / "imc_qqplot.png",
    ROOT / "outputs" / "figures" / "figure_1_imc_categories.png",
]
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class ImcEdaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [path for path in [NOTEBOOK_PATH, *FIGURES] if not path.exists()]
        if missing:
            raise AssertionError(f"Artefatos da EDA de IMC ausentes: {missing}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.processed = pd.read_csv(PROCESSED_PATH)

    def test_imc_descriptive_statistics(self):
        imc = self.processed["imc"].dropna()

        self.assertEqual(len(imc), 73)
        self.assertEqual(self.processed["imc"].isna().sum(), 2)
        self.assertAlmostEqual(imc.mean(), 28.7216438356)
        self.assertEqual(imc.mode().tolist(), [29])
        self.assertAlmostEqual(imc.std(), 5.5039922414)
        self.assertEqual(imc.median(), 27.94)
        self.assertEqual(imc.quantile(0.25), 24.62)
        self.assertEqual(imc.quantile(0.75), 32.3)
        self.assertEqual(imc.min(), 17.5)
        self.assertEqual(imc.max(), 41.1)

    def test_prevalence_uses_only_valid_imc(self):
        imc = self.processed["imc"].dropna()

        self.assertEqual(int(imc.ge(25).sum()), 52)
        self.assertAlmostEqual(100 * imc.ge(25).mean(), 71.2328767123)
        self.assertEqual(int(imc.ge(30).sum()), 26)
        self.assertAlmostEqual(100 * imc.ge(30).mean(), 35.6164383562)

    def test_extremes_are_assessed_without_exclusion(self):
        imc = self.processed["imc"].dropna()
        q1, q3 = imc.quantile([0.25, 0.75])
        iqr = q3 - q1
        outliers = ~imc.between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)

        self.assertEqual(int(outliers.sum()), 0)
        self.assertTrue(imc.between(10, 80).all())
        self.assertEqual(len(imc), 73)

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
            "IMC válido: 73",
            "IMC ausente: 2",
            "Excesso de peso (IMC ≥25): 52/73 (71,23%)",
            "Obesidade (IMC ≥30): 26/73 (35,62%)",
            "Extremos pelo critério de 1,5×IQR: 0",
            "Valores biologicamente implausíveis: 0",
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

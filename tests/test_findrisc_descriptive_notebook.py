import hashlib
import re
import unittest
from pathlib import Path

import nbformat
import pandas as pd

from src.variables import count_autoimmune_diagnoses


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "09_findrisc_descriptive_statistics.ipynb"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class FindriscDescriptiveNotebookTests(unittest.TestCase):
    def test_notebook_is_executed_and_reports_requested_statistics(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]

        self.assertTrue(code_cells)
        self.assertTrue(all(cell.execution_count is not None for cell in code_cells))
        self.assertFalse(
            any(
                output.get("output_type") == "error"
                for cell in code_cells
                for output in cell.get("outputs", [])
            )
        )

        output_text = "\n".join(
            output.get("text", "")
            for cell in code_cells
            for output in cell.get("outputs", [])
            if output.get("output_type") == "stream"
        )
        for expected in [
            "Pacientes no dataset: 75",
            "Pacientes com doença autoimune explícita: 69",
            "FINDRISC válido no grupo autoimune: 68",
            "FINDRISC ausente no grupo autoimune: 1",
            "Média: 13,65 pontos",
            "Moda: 9 pontos",
            "Mediana: 13,50 pontos",
            "Desvio-padrão: 6,19 pontos",
            "P25: 9,00 pontos",
            "P75: 19,00 pontos",
        ]:
            self.assertIn(expected, output_text)

        source = "\n".join(cell.source for cell in code_cells)
        self.assertIn("count_autoimmune_diagnoses", source)
        self.assertIn("n_diagnosticos_autoimunes.ge(1)", source)
        self.assertIn("descriptive_numeric", source)

    def test_statistics_use_only_patients_with_explicit_autoimmune_disease(self):
        dataframe = pd.read_csv(PROCESSED_PATH)
        n_diagnosticos_autoimunes = count_autoimmune_diagnoses(
            dataframe["diagnostico_padronizado"]
        )
        eligible = n_diagnosticos_autoimunes.ge(1).fillna(False)
        findrisc = dataframe.loc[eligible, "findrisc_score"].dropna()

        self.assertEqual(len(dataframe), 75)
        self.assertEqual(int(eligible.sum()), 69)
        self.assertEqual(len(findrisc), 68)
        self.assertAlmostEqual(findrisc.mean(), 13.6470588235)
        self.assertEqual(findrisc.mode().tolist(), [9])
        self.assertAlmostEqual(findrisc.median(), 13.50)
        self.assertAlmostEqual(findrisc.std(ddof=1), 6.1928333782)
        self.assertAlmostEqual(findrisc.quantile(0.25), 9.00)
        self.assertAlmostEqual(findrisc.quantile(0.75), 19.00)

    def test_notebook_is_private_and_raw_is_unchanged(self):
        raw = pd.read_csv(RAW_PATH, dtype="string")
        names = [name.casefold() for name in raw["nome"].dropna().str.strip() if name]
        serialized = NOTEBOOK_PATH.read_text(encoding="utf-8").casefold()

        self.assertFalse(any(name in serialized for name in names))
        self.assertIsNone(re.search(r"\bP\d{3}\b", serialized))
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

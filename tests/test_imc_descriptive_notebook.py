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
NOTEBOOK_PATH = ROOT / "notebooks" / "08_imc_descriptive_statistics.ipynb"
README_PATH = ROOT / "README.md"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class ImcDescriptiveNotebookTests(unittest.TestCase):
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
            "IMC válido no grupo autoimune: 67",
            "IMC ausente no grupo autoimune: 2",
            "Média: 28,72 kg/m²",
            "Moda: 29,00 kg/m²",
            "Mediana: 28,50 kg/m²",
            "Desvio-padrão: 5,64 kg/m²",
            "P25: 24,50 kg/m²",
            "P75: 32,35 kg/m²",
        ]:
            self.assertIn(expected, output_text)

        source = "\n".join(cell.source for cell in code_cells)
        self.assertIn("count_autoimmune_diagnoses", source)
        self.assertIn("n_diagnosticos_autoimunes.ge(1)", source)

    def test_notebook_has_text_cell_with_observed_autoimmune_diseases(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        markdown = "\n".join(
            cell.source for cell in notebook.cells if cell.cell_type == "markdown"
        )

        self.assertIn("Doenças autoimunes presentes", markdown)
        for diagnosis in [
            "Arterite temporal",
            "Artrite reumatoide",
            "Espondiloartrite",
            "Lúpus eritematoso",
            "Síndrome antifosfolipídica (SAF)",
        ]:
            self.assertRegex(markdown, rf"(?m)^- {re.escape(diagnosis)}$")
        self.assertIn("Doença de BC", markdown)
        self.assertIn("classificação incerta", markdown)

    def test_artifacts_are_private_and_raw_is_unchanged(self):
        raw = pd.read_csv(RAW_PATH, dtype="string")
        names = [name.casefold() for name in raw["nome"].dropna().str.strip() if name]
        serialized = "\n".join(
            [
                NOTEBOOK_PATH.read_text(encoding="utf-8"),
                README_PATH.read_text(encoding="utf-8"),
            ]
        ).casefold()

        self.assertFalse(any(name in serialized for name in names))
        self.assertIsNone(re.search(r"\bP\d{3}\b", NOTEBOOK_PATH.read_text(encoding="utf-8")))
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)

    def test_statistics_use_only_patients_with_explicit_autoimmune_disease(self):
        dataframe = pd.read_csv(PROCESSED_PATH)
        n_diagnosticos_autoimunes = count_autoimmune_diagnoses(
            dataframe["diagnostico_padronizado"]
        )
        eligible = n_diagnosticos_autoimunes.ge(1).fillna(False)
        imc = dataframe.loc[eligible, "imc"].dropna()

        self.assertEqual(len(dataframe), 75)
        self.assertEqual(int(eligible.sum()), 69)
        self.assertEqual(len(imc), 67)
        self.assertAlmostEqual(imc.mean(), 28.7156716418)
        self.assertEqual(imc.mode().tolist(), [29])
        self.assertAlmostEqual(imc.median(), 28.50)
        self.assertAlmostEqual(imc.std(ddof=1), 5.6441761951)
        self.assertAlmostEqual(imc.quantile(0.25), 24.50)
        self.assertAlmostEqual(imc.quantile(0.75), 32.35)


if __name__ == "__main__":
    unittest.main()

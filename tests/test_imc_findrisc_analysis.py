import hashlib
import re
import unittest
from pathlib import Path

import matplotlib.image as mpimg
import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "05_imc_findrisc_analysis.ipynb"
TABLE_PATH = ROOT / "outputs" / "tables" / "table_3_imc_findrisc.csv"
FIGURE_PATH = ROOT / "outputs" / "figures" / "figure_3_imc_findrisc.png"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"
STRUCTURAL_LIMITATION = (
    "O IMC é um dos componentes utilizados na construção do FINDRISC. Portanto, parte da associação "
    "observada é esperada pelo próprio desenho matemático do escore."
)


class ImcFindriscAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [path for path in [NOTEBOOK_PATH, TABLE_PATH, FIGURE_PATH] if not path.exists()]
        if missing:
            raise AssertionError(f"Artefatos da análise IMC × FINDRISC ausentes: {missing}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.table = pd.read_csv(TABLE_PATH)

    def test_table_contains_complete_reproducible_main_result(self):
        self.assertEqual(
            self.table.columns.tolist(),
            [
                "n",
                "rho_spearman",
                "ic95_inferior",
                "ic95_superior",
                "p_valor",
                "metodo_ic",
                "bootstrap",
                "random_state",
            ],
        )
        self.assertEqual(len(self.table), 1)
        result = self.table.iloc[0]
        self.assertEqual(result["n"], 72)
        self.assertAlmostEqual(result["rho_spearman"], 0.7044568459379132)
        self.assertAlmostEqual(result["ic95_inferior"], 0.5613847929036577)
        self.assertAlmostEqual(result["ic95_superior"], 0.8077108647206857)
        self.assertAlmostEqual(result["p_valor"], 5.026909868083026e-12)
        self.assertEqual(result["metodo_ic"], "Bootstrap percentil pareado")
        self.assertEqual(result["bootstrap"], 10_000)
        self.assertEqual(result["random_state"], 42)

    def test_figure_is_high_resolution_and_nonempty(self):
        image = mpimg.imread(FIGURE_PATH)

        self.assertGreaterEqual(image.shape[0], 1500)
        self.assertGreaterEqual(image.shape[1], 2000)
        self.assertGreater(FIGURE_PATH.stat().st_size, 10_000)

    def test_notebook_is_executed_and_reports_required_result(self):
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
            "ANÁLISE PRINCIPAL",
            "N da análise principal: 72",
            "rho de Spearman: 0,704",
            "IC95% bootstrap: 0,561 a 0,808",
            "p-valor: 5,027e-12",
            "Bootstrap: 10.000 reamostragens; seed = 42",
            "Maiores valores de IMC estiveram associados a maiores escores FINDRISC.",
            STRUCTURAL_LIMITATION,
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

    def test_notebook_documents_structural_limitation_and_noncausal_interpretation(self):
        notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn(STRUCTURAL_LIMITATION, notebook_text)
        self.assertNotIn("IMC causa", notebook_text)

    def test_outputs_contain_no_patient_names_and_raw_is_unchanged(self):
        names = [name.casefold() for name in self.raw["nome"].dropna().str.strip() if name]
        serialized = (NOTEBOOK_PATH.read_text(encoding="utf-8") + TABLE_PATH.read_text(encoding="utf-8")).casefold()

        self.assertFalse(any(name in serialized for name in names))
        self.assertIsNone(re.search(r"\bP\d{3}\b", TABLE_PATH.read_text(encoding="utf-8")))
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

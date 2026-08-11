import hashlib
import re
import unittest
from pathlib import Path

import nbformat
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "07_tables_and_figures.ipynb"
FIGURES = [
    ROOT / "outputs" / "figures" / "figure_1_imc_categories.png",
    ROOT / "outputs" / "figures" / "figure_2_findrisc_categories.png",
    ROOT / "outputs" / "figures" / "figure_3_imc_findrisc.png",
    ROOT / "outputs" / "figures" / "figure_4_metabolic_profile.png",
]
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class FinalFiguresTests(unittest.TestCase):
    def test_all_final_figures_are_valid_high_resolution_png_files(self):
        missing = [path for path in FIGURES if not path.exists()]
        self.assertFalse(missing, f"Figuras finais ausentes: {missing}")

        for path in FIGURES:
            with self.subTest(figure=path.name):
                self.assertGreater(path.stat().st_size, 10_000)
                with Image.open(path) as image:
                    self.assertEqual(image.format, "PNG")
                    self.assertGreaterEqual(image.width, 1800)
                    self.assertGreaterEqual(image.height, 1200)
                    self.assertAlmostEqual(image.info["dpi"][0], 300, delta=1)
                    self.assertAlmostEqual(image.info["dpi"][1], 300, delta=1)
                    image.verify()

    def test_notebook_uses_reusable_plot_functions_and_persisted_main_result(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        code = "\n".join(
            cell.source for cell in notebook.cells if cell.cell_type == "code"
        )

        for function_name in [
            "plot_imc_categories",
            "plot_findrisc_categories",
            "plot_imc_findrisc",
            "plot_metabolic_profile",
            "save_figure",
        ]:
            self.assertRegex(code, rf"\b{function_name}\(")
        for forbidden in ["spearmanr(", "spearman_with_bootstrap_ci(", "plt.subplots"]:
            self.assertNotIn(forbidden, code)
        self.assertIn("main_result['rho_spearman']", code)
        self.assertIn("main_result['ic95_inferior']", code)
        self.assertIn("main_result['ic95_superior']", code)

    def test_notebook_is_executed_and_documents_all_outputs(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
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
            "Figura 1 gerada: distribuição das categorias de IMC",
            "Figura 2 gerada: distribuição das categorias FINDRISC",
            "Figura 3 gerada: IMC × FINDRISC; N = 72; rho = 0,704; IC95% 0,561 a 0,808",
            "Figura 4 gerada: perfil metabólico geral",
            "Quatro figuras finais exportadas em PNG a 300 DPI.",
        ]:
            self.assertIn(expected, output_text)

    def test_notebook_and_outputs_preserve_privacy_and_raw_integrity(self):
        raw = pd.read_csv(RAW_PATH, dtype="string")
        names = [name.casefold() for name in raw["nome"].dropna().str.strip() if name]
        notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8").casefold()

        self.assertFalse(any(name in notebook_text for name in names))
        self.assertIsNone(re.search(r"\bP\d{3}\b", notebook_text))
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

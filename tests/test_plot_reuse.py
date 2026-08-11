import unittest
from pathlib import Path

import matplotlib.image as mpimg
import nbformat


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))
REFACTORED_FIGURES = [
    ROOT / "outputs" / "figures" / "missing_data.png",
    ROOT / "outputs" / "figures" / "data_cleaning_flow.png",
    ROOT / "outputs" / "figures" / "population_variable_availability.png",
]


class PlotReuseTests(unittest.TestCase):
    def test_notebooks_do_not_recreate_plot_layout_or_style(self):
        forbidden = ["plt.subplots", ".plot.bar(", ".plot.barh(", "plt.rcParams.update"]

        for path in NOTEBOOKS:
            notebook = nbformat.read(path, as_version=4)
            code = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code")
            with self.subTest(notebook=path.name):
                self.assertFalse(any(token in code for token in forbidden))

    def test_refactored_notebook_figures_are_high_resolution(self):
        missing = [path for path in REFACTORED_FIGURES if not path.exists()]
        if missing:
            raise AssertionError(f"Figuras reutilizáveis ainda não geradas: {missing}")

        for path in REFACTORED_FIGURES:
            with self.subTest(figure=path.name):
                image = mpimg.imread(path)
                self.assertGreaterEqual(image.shape[0], 1000)
                self.assertGreaterEqual(image.shape[1], 1800)
                self.assertGreater(path.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()

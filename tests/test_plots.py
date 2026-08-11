import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

from src.plots import (
    plot_findrisc_boxplot,
    plot_findrisc_categories,
    plot_findrisc_distribution,
    plot_imc_boxplot,
    plot_imc_categories,
    plot_imc_distribution,
    plot_imc_findrisc,
    plot_metabolic_profile,
    plot_missing_data,
    plot_qq,
    plot_selection_flow,
    plot_variable_availability,
    save_figure,
)


class PlotTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_imc_distribution_contains_histogram_and_density(self):
        figure, axis = plot_imc_distribution(pd.Series([20, 22, 24, 25, 27, 30, 32, None]))

        self.assertGreater(len(axis.patches), 0)
        self.assertGreater(len(axis.lines), 0)
        self.assertEqual(axis.get_xlabel(), "IMC (kg/m²)")
        self.assertIsNotNone(figure)

    def test_imc_boxplot_and_qq_plot_have_expected_labels(self):
        values = pd.Series([20, 22, 24, 25, 27, 30, 32])

        _, box_axis = plot_imc_boxplot(values)
        _, qq_axis = plot_qq(values, title="Q-Q plot do IMC")

        self.assertEqual(box_axis.get_xlabel(), "Pacientes com IMC válido")
        self.assertEqual(box_axis.get_ylabel(), "IMC (kg/m²)")
        self.assertEqual(qq_axis.get_title(), "Q-Q plot do IMC")

    def test_category_plot_uses_valid_denominator_and_all_categories(self):
        categories = pd.Series(["Peso normal", "Sobrepeso", "Sobrepeso", None])
        order = ["Baixo peso", "Peso normal", "Sobrepeso"]

        _, axis = plot_imc_categories(categories, order=order)

        self.assertEqual(len(axis.patches), 3)
        annotations = [text.get_text() for text in axis.texts]
        self.assertIn("2 (66,7%)", annotations)

    def test_save_figure_creates_nonempty_file(self):
        figure, _ = plot_imc_boxplot(pd.Series([20, 25, 30]))

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "figure.png"
            save_figure(figure, output)

            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)
            with Image.open(output) as image:
                dpi = image.info["dpi"]
            self.assertAlmostEqual(dpi[0], 300, delta=1)
            self.assertAlmostEqual(dpi[1], 300, delta=1)

    def test_findrisc_distribution_contains_histogram_and_density(self):
        values = pd.Series([2, 5, 7, 9, 11, 14, 15, 18, 21, 24, None])

        figure, axis = plot_findrisc_distribution(values)

        self.assertGreater(len(axis.patches), 0)
        self.assertGreater(len(axis.lines), 0)
        self.assertEqual(axis.get_xlabel(), "FINDRISC (pontos)")
        self.assertIsNotNone(figure)

    def test_findrisc_boxplot_is_vertical_and_labels_both_axes(self):
        _, axis = plot_findrisc_boxplot(pd.Series([2, 7, 12, 15, 20, 24]))

        self.assertEqual(axis.get_xlabel(), "Pacientes com FINDRISC válido")
        self.assertEqual(axis.get_ylabel(), "FINDRISC (pontos)")
        self.assertEqual(axis.get_xticks().tolist(), [])

    def test_findrisc_category_plot_uses_valid_denominator(self):
        categories = pd.Series(["Baixo risco", "Alto", "Alto", None])
        order = ["Baixo risco", "Leve/moderado", "Moderado", "Alto", "Muito alto"]

        _, axis = plot_findrisc_categories(categories, order=order)

        self.assertEqual(len(axis.patches), 5)
        annotations = [text.get_text() for text in axis.texts]
        self.assertIn("2 (66,7%)", annotations)

    def test_imc_findrisc_plot_has_scatter_trend_labels_and_statistics(self):
        imc = pd.Series([20, 22, 25, 28, 30, 32, 35, None])
        findrisc = pd.Series([5, 7, 9, 12, 15, 18, 21, 24])

        figure, axis = plot_imc_findrisc(
            imc,
            findrisc,
            rho=0.70,
            ic95_inferior=0.50,
            ic95_superior=0.82,
        )

        self.assertGreater(len(axis.collections), 0)
        self.assertGreater(len(axis.lines), 0)
        self.assertEqual(axis.get_xlabel(), "IMC (kg/m²)")
        self.assertEqual(axis.get_ylabel(), "FINDRISC (pontos)")
        annotation = "\n".join(text.get_text() for text in axis.texts)
        self.assertIn("rho de Spearman = 0,70", annotation)
        self.assertIn("IC95%: 0,50 a 0,82", annotation)
        self.assertIn("N = 7", annotation)
        self.assertIsNotNone(figure)

    def test_missing_data_plot_has_title_axes_and_percentage_unit(self):
        summary = pd.DataFrame(
            {
                "variavel": ["completa", "parcial", "vazia", "nome", "Cod", "patient_id"],
                "percentual_ausente": [0.0, 25.0, 100.0, 0.0, 0.0, 0.0],
            }
        )

        figure, axis = plot_missing_data(summary)

        self.assertEqual(len(axis.patches), 3)
        self.assertTrue(axis.get_title())
        self.assertEqual(axis.get_xlabel(), "Dados ausentes (%)")
        self.assertEqual(axis.get_ylabel(), "Variável")
        labels = {tick.get_text() for tick in axis.get_yticklabels()}
        self.assertTrue({"nome", "Cod", "patient_id"}.isdisjoint(labels))
        self.assertIsNotNone(figure)

    def test_metabolic_profile_uses_valid_denominator_for_each_indicator(self):
        figure, axis = plot_metabolic_profile(
            excesso_peso=pd.Series([True, False, pd.NA], dtype="boolean"),
            obesidade=pd.Series([True, False, False], dtype="boolean"),
            findrisc_alto=pd.Series([True, True, False, pd.NA], dtype="boolean"),
        )

        self.assertEqual(len(axis.patches), 3)
        self.assertTrue(axis.get_title())
        self.assertEqual(axis.get_xlabel(), "Indicador metabólico")
        self.assertEqual(axis.get_ylabel(), "Prevalência (%)")
        annotations = [text.get_text() for text in axis.texts]
        self.assertIn("1/2 (50,0%)", annotations)
        self.assertIn("1/3 (33,3%)", annotations)
        self.assertIn("2/3 (66,7%)", annotations)
        self.assertIsNotNone(figure)

    def test_selection_and_availability_plots_are_fully_labeled(self):
        _, flow_axis = plot_selection_flow(
            pd.Series({"Linhas brutas": 100, "Pacientes válidos": 75, "Processados": 75})
        )
        _, availability_axis = plot_variable_availability(
            pd.Series({"IMC": 97.3, "FINDRISC": 98.7})
        )

        self.assertTrue(flow_axis.get_title())
        self.assertEqual(flow_axis.get_xlabel(), "Etapa")
        self.assertEqual(flow_axis.get_ylabel(), "Número de registros")
        self.assertTrue(availability_axis.get_title())
        self.assertEqual(availability_axis.get_xlabel(), "Observações válidas (%)")
        self.assertEqual(availability_axis.get_ylabel(), "Variável")


if __name__ == "__main__":
    unittest.main()

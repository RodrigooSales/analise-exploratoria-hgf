import hashlib
import re
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import pandas as pd

from src.plots import (
    plot_findrisc_categories,
    plot_imc_categories,
    plot_imc_findrisc,
    plot_metabolic_profile,
    save_figure,
)
from src.statistics import descriptive_numeric, spearman_with_bootstrap_ci


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"
IMC_ORDER = [
    "Baixo peso",
    "Peso normal",
    "Sobrepeso",
    "Obesidade grau I",
    "Obesidade grau II",
    "Obesidade grau III",
]
FINDRISC_ORDER = ["Baixo risco", "Leve/moderado", "Moderado", "Alto", "Muito alto"]


def _rendered_notebook_text(name: str) -> str:
    notebook = nbformat.read(ROOT / "notebooks" / name, as_version=4)
    chunks = []
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream":
                chunks.append(str(output.get("text", "")))
            plain_text = output.get("data", {}).get("text/plain")
            if plain_text:
                chunks.append(str(plain_text))
    return "\n".join(chunks)


def _sha256(path: Path) -> bytes:
    return hashlib.sha256(path.read_bytes()).digest()


class ScientificConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(PROCESSED_PATH)
        for column in ["excesso_peso", "obesidade", "findrisc_alto"]:
            cls.data[column] = cls.data[column].astype("boolean")
        cls.imc_summary = descriptive_numeric(cls.data["imc"])
        cls.findrisc_summary = descriptive_numeric(cls.data["findrisc_score"])
        cls.main_result = spearman_with_bootstrap_ci(
            cls.data["imc"], cls.data["findrisc_score"]
        )
        cls.table_1 = pd.read_csv(TABLES_DIR / "table_1_population.csv")
        cls.table_2 = pd.read_csv(TABLES_DIR / "table_2_metabolic_profile.csv").set_index(
            "variavel"
        )
        cls.table_3 = pd.read_csv(TABLES_DIR / "table_3_imc_findrisc.csv").iloc[0]

    def tearDown(self):
        plt.close("all")

    def test_sample_sizes_are_identical_across_dataset_notebooks_and_tables(self):
        self.assertEqual(len(self.data), 75)
        self.assertEqual(self.imc_summary["n_valido"], 73)
        self.assertEqual(self.findrisc_summary["n_valido"], 74)
        self.assertEqual(self.main_result["n"], 72)

        imc_table_1 = self.table_1[self.table_1["variavel"].eq("IMC (kg/m²)")].iloc[0]
        findrisc_table_1 = self.table_1[
            self.table_1["variavel"].eq("FINDRISC (pontos)")
        ].iloc[0]
        self.assertEqual(int(imc_table_1["n_valido"]), 73)
        self.assertEqual(int(findrisc_table_1["n_valido"]), 74)
        self.assertEqual(int(self.table_2.loc["IMC (kg/m²)", "n_valido"]), 73)
        self.assertEqual(int(self.table_2.loc["FINDRISC (pontos)", "n_valido"]), 74)
        self.assertEqual(int(self.table_3["n"]), 72)

        expected_by_notebook = {
            "00_data_audit.ipynb": ["N de pacientes válidos: 75"],
            "01_data_cleaning.ipynb": [
                "Pacientes válidos: 75",
                "N com IMC válido: 73",
                "N com FINDRISC válido: 74",
            ],
            "02_population_description.ipynb": ["Amostra descrita: 75 pacientes"],
            "03_imc_analysis.ipynb": ["Registros carregados: 75", "IMC válido: 73"],
            "04_findrisc_analysis.ipynb": [
                "Registros no dataset analítico: 75",
                "FINDRISC válido: 74",
            ],
            "05_imc_findrisc_analysis.ipynb": [
                "Amostra analítica disponível: 75 pacientes",
                "IMC válido: 73",
                "FINDRISC válido: 74",
                "N da análise principal: 72",
            ],
            "06_secondary_analysis.ipynb": [
                "Amostra disponível: 75 pacientes",
                "Todos os pacientes: N = 72",
            ],
            "07_tables_and_figures.ipynb": [
                "Dataset processado: 75 pacientes",
                "Tabela 3 validada: N = 72",
                "Figura 3 gerada: IMC × FINDRISC; N = 72",
            ],
        }
        for notebook_name, expected_strings in expected_by_notebook.items():
            rendered = _rendered_notebook_text(notebook_name)
            for expected in expected_strings:
                with self.subTest(notebook=notebook_name, expected=expected):
                    self.assertIn(expected, rendered)

    def test_numeric_summaries_match_dataset_tables_and_eda_notebooks(self):
        expected = {
            "IMC (kg/m²)": {
                "summary": self.imc_summary,
                "media": 28.72164383561644,
                "moda": "29",
                "desvio_padrao": 5.503992241425196,
                "mediana": 27.94,
            },
            "FINDRISC (pontos)": {
                "summary": self.findrisc_summary,
                "media": 13.756756756756756,
                "moda": "9",
                "desvio_padrao": 6.254446770614924,
                "mediana": 14.0,
            },
        }
        for label, values in expected.items():
            summary = values["summary"]
            self.assertAlmostEqual(summary["media"], values["media"])
            self.assertEqual(summary["moda"], values["moda"])
            self.assertAlmostEqual(summary["desvio_padrao"], values["desvio_padrao"])
            self.assertAlmostEqual(summary["mediana"], values["mediana"])

            table_1_row = self.table_1[self.table_1["variavel"].eq(label)].iloc[0]
            table_2_row = self.table_2.loc[label]
            for row in [table_1_row, table_2_row]:
                self.assertAlmostEqual(float(row["media"]), round(summary["media"], 2))
                self.assertAlmostEqual(float(row["moda"]), float(summary["moda"]))
                self.assertAlmostEqual(
                    float(row["desvio_padrao"]), round(summary["desvio_padrao"], 2)
                )
                self.assertAlmostEqual(float(row["mediana"]), summary["mediana"])

        imc_notebook = _rendered_notebook_text("03_imc_analysis.ipynb")
        findrisc_notebook = _rendered_notebook_text("04_findrisc_analysis.ipynb")
        self.assertRegex(
            imc_notebook,
            r"0\s+73\s+2\s+28\.72\s+29\s+5\.5\s+27\.94\s+24\.62\s+32\.3",
        )
        self.assertRegex(
            findrisc_notebook,
            r"0\s+74\s+1\s+13\.756757\s+9\s+6\.254447\s+14\.0\s+9\.0\s+19\.0",
        )

    def test_prevalences_match_dataset_tables_notebooks_and_figures(self):
        expected = {
            "Excesso de peso (IMC ≥ 25 kg/m²)": ("excesso_peso", 73, 52, 71.23),
            "Obesidade (IMC ≥ 30 kg/m²)": ("obesidade", 73, 26, 35.62),
            "FINDRISC ≥ 15 pontos": ("findrisc_alto", 74, 35, 47.30),
        }
        for label, (column, denominator, count, percentage) in expected.items():
            valid = self.data[column].dropna()
            self.assertEqual(len(valid), denominator)
            self.assertEqual(int(valid.sum()), count)
            self.assertAlmostEqual(100 * valid.mean(), percentage, places=2)
            row = self.table_2.loc[label]
            self.assertEqual(int(row["n_valido"]), denominator)
            self.assertEqual(int(row["n"]), count)
            self.assertAlmostEqual(float(row["percentual"]), percentage)

        imc_notebook = _rendered_notebook_text("03_imc_analysis.ipynb")
        findrisc_notebook = _rendered_notebook_text("04_findrisc_analysis.ipynb")
        self.assertIn("Excesso de peso (IMC ≥25): 52/73 (71,23%)", imc_notebook)
        self.assertIn("Obesidade (IMC ≥30): 26/73 (35,62%)", imc_notebook)
        self.assertIn("FINDRISC ≥15: 35/74 (47,30%", findrisc_notebook)

        figure_4, axis_4 = plot_metabolic_profile(
            self.data["excesso_peso"], self.data["obesidade"], self.data["findrisc_alto"]
        )
        annotations = {text.get_text() for text in axis_4.texts}
        self.assertEqual(
            annotations,
            {"52/73 (71,2%)", "26/73 (35,6%)", "35/74 (47,3%)"},
        )
        self.assertIsNotNone(figure_4)

    def test_main_association_matches_table_notebooks_and_sensitivity_analysis(self):
        mappings = {
            "n": "n",
            "rho": "rho_spearman",
            "ic95_inferior": "ic95_inferior",
            "ic95_superior": "ic95_superior",
            "p": "p_valor",
            "bootstrap": "bootstrap",
            "random_state": "random_state",
        }
        for result_key, table_key in mappings.items():
            self.assertAlmostEqual(
                float(self.main_result[result_key]), float(self.table_3[table_key])
            )

        sensitivity = pd.read_csv(TABLES_DIR / "sensitivity_analysis_results.csv").iloc[0]
        for table_key, sensitivity_key in [
            ("n", "n"),
            ("rho_spearman", "rho"),
            ("ic95_inferior", "ic95_inferior"),
            ("ic95_superior", "ic95_superior"),
            ("p_valor", "p_valor"),
        ]:
            self.assertAlmostEqual(float(self.table_3[table_key]), float(sensitivity[sensitivity_key]))

        for notebook_name in [
            "05_imc_findrisc_analysis.ipynb",
            "06_secondary_analysis.ipynb",
            "07_tables_and_figures.ipynb",
        ]:
            rendered = _rendered_notebook_text(notebook_name)
            for expected in [
                "rho = 0,704" if notebook_name != "05_imc_findrisc_analysis.ipynb" else "rho de Spearman: 0,704",
                "IC95% 0,561 a 0,808" if notebook_name != "05_imc_findrisc_analysis.ipynb" else "IC95% bootstrap: 0,561 a 0,808",
                "p = 5,027e-12" if notebook_name != "05_imc_findrisc_analysis.ipynb" else "p-valor: 5,027e-12",
            ]:
                with self.subTest(notebook=notebook_name, expected=expected):
                    self.assertIn(expected, rendered)

        figure_3, axis_3 = plot_imc_findrisc(
            self.data["imc"],
            self.data["findrisc_score"],
            rho=self.table_3["rho_spearman"],
            ic95_inferior=self.table_3["ic95_inferior"],
            ic95_superior=self.table_3["ic95_superior"],
        )
        annotation = "\n".join(text.get_text() for text in axis_3.texts)
        self.assertIn("rho de Spearman = 0,70", annotation)
        self.assertIn("IC95%: 0,56 a 0,81", annotation)
        self.assertIn("N = 72", annotation)
        self.assertIsNotNone(figure_3)

    def test_grouped_secondary_counts_sum_to_valid_outcome_counts(self):
        descriptive = pd.read_csv(TABLES_DIR / "secondary_analysis_descriptive.csv")
        expected_n = {"IMC": 73, "FINDRISC": 74}
        grouped = descriptive.groupby(["exposicao", "desfecho"])["n_valido"].sum()
        for (_, outcome), observed in grouped.items():
            self.assertEqual(int(observed), expected_n[outcome])

    def test_final_pngs_are_exactly_reproducible_from_canonical_results(self):
        figures = []
        figure_1, axis_1 = plot_imc_categories(
            self.data["imc_categoria"], order=IMC_ORDER
        )
        figures.append((figure_1, axis_1, "figure_1_imc_categories.png"))
        figure_2, axis_2 = plot_findrisc_categories(
            self.data["findrisc_categoria"], order=FINDRISC_ORDER
        )
        figures.append((figure_2, axis_2, "figure_2_findrisc_categories.png"))
        figure_3, axis_3 = plot_imc_findrisc(
            self.data["imc"],
            self.data["findrisc_score"],
            rho=self.table_3["rho_spearman"],
            ic95_inferior=self.table_3["ic95_inferior"],
            ic95_superior=self.table_3["ic95_superior"],
        )
        figures.append((figure_3, axis_3, "figure_3_imc_findrisc.png"))
        figure_4, axis_4 = plot_metabolic_profile(
            self.data["excesso_peso"], self.data["obesidade"], self.data["findrisc_alto"]
        )
        figures.append((figure_4, axis_4, "figure_4_metabolic_profile.png"))

        self.assertEqual(
            {text.get_text() for text in axis_1.texts},
            {"3 (4,1%)", "18 (24,7%)", "26 (35,6%)", "15 (20,5%)", "9 (12,3%)", "2 (2,7%)"},
        )
        self.assertEqual(
            {text.get_text() for text in axis_2.texts},
            {"10 (13,5%)", "18 (24,3%)", "11 (14,9%)", "20 (27,0%)", "15 (20,3%)"},
        )

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            for figure, _, name in figures:
                reproduced = output_dir / name
                save_figure(figure, reproduced)
                self.assertEqual(_sha256(reproduced), _sha256(FIGURES_DIR / name))


if __name__ == "__main__":
    unittest.main()

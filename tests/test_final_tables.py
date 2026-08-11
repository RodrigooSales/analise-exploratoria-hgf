import hashlib
import re
import unittest
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "07_tables_and_figures.ipynb"
TABLE_1_PATH = ROOT / "outputs" / "tables" / "table_1_population.csv"
TABLE_2_PATH = ROOT / "outputs" / "tables" / "table_2_metabolic_profile.csv"
TABLE_3_PATH = ROOT / "outputs" / "tables" / "table_3_imc_findrisc.csv"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"
TABLE_1_TITLE = "Características sociodemográficas e clínicas dos pacientes com doenças autoimunes"
TABLE_2_TITLE = "Perfil antropométrico e risco metabólico dos pacientes com doenças autoimunes"
TABLE_3_TITLE = "Associação entre índice de massa corporal e escore FINDRISC"


class FinalTablesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        artifacts = [NOTEBOOK_PATH, TABLE_1_PATH, TABLE_2_PATH, TABLE_3_PATH]
        missing = [path for path in artifacts if not path.exists()]
        if missing:
            raise AssertionError(f"Tabelas científicas finais ausentes: {missing}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.table_1 = pd.read_csv(TABLE_1_PATH)
        cls.table_2 = pd.read_csv(TABLE_2_PATH)
        cls.table_3 = pd.read_csv(TABLE_3_PATH)

    def test_table_1_is_preserved_as_population_source(self):
        self.assertEqual(len(self.table_1), 64)
        required = {
            "Estado civil",
            "Escolaridade",
            "Renda mensal familiar",
            "Ocupação",
            "Diagnóstico",
            "IMC (kg/m²)",
            "FINDRISC (pontos)",
        }
        self.assertTrue(required.issubset(set(self.table_1["variavel"])))

    def test_table_2_has_required_schema_and_rows(self):
        self.assertEqual(
            self.table_2.columns.tolist(),
            [
                "variavel",
                "n_valido",
                "media",
                "moda",
                "desvio_padrao",
                "mediana",
                "p25",
                "p75",
                "n",
                "percentual",
            ],
        )
        self.assertEqual(
            self.table_2["variavel"].tolist(),
            [
                "IMC (kg/m²)",
                "Excesso de peso (IMC ≥ 25 kg/m²)",
                "Obesidade (IMC ≥ 30 kg/m²)",
                "FINDRISC (pontos)",
                "FINDRISC ≥ 15 pontos",
            ],
        )

    def test_table_2_numeric_results_are_derived_correctly(self):
        table = self.table_2.set_index("variavel")
        imc = table.loc["IMC (kg/m²)"]
        findrisc = table.loc["FINDRISC (pontos)"]

        self.assertEqual(imc["n_valido"], 73)
        self.assertAlmostEqual(imc["media"], 28.72)
        self.assertEqual(imc["moda"], 29)
        self.assertAlmostEqual(imc["desvio_padrao"], 5.50)
        self.assertAlmostEqual(imc["mediana"], 27.94)
        self.assertAlmostEqual(imc["p25"], 24.62)
        self.assertAlmostEqual(imc["p75"], 32.30)

        self.assertEqual(findrisc["n_valido"], 74)
        self.assertAlmostEqual(findrisc["media"], 13.76)
        self.assertEqual(findrisc["moda"], 9)
        self.assertAlmostEqual(findrisc["desvio_padrao"], 6.25)
        self.assertEqual(findrisc["mediana"], 14)
        self.assertEqual(findrisc["p25"], 9)
        self.assertEqual(findrisc["p75"], 19)

    def test_table_2_prevalences_have_no_inappropriate_numeric_statistics(self):
        table = self.table_2.set_index("variavel")
        expected = {
            "Excesso de peso (IMC ≥ 25 kg/m²)": (73, 52, 71.23),
            "Obesidade (IMC ≥ 30 kg/m²)": (73, 26, 35.62),
            "FINDRISC ≥ 15 pontos": (74, 35, 47.30),
        }
        numeric_columns = ["media", "moda", "desvio_padrao", "mediana", "p25", "p75"]

        for variable, (n_valid, count, percentage) in expected.items():
            with self.subTest(variable=variable):
                row = table.loc[variable]
                self.assertEqual(row["n_valido"], n_valid)
                self.assertEqual(row["n"], count)
                self.assertAlmostEqual(row["percentual"], percentage)
                self.assertTrue(row[numeric_columns].isna().all())

        quantitative = table.loc[["IMC (kg/m²)", "FINDRISC (pontos)"]]
        self.assertTrue(quantitative[["n", "percentual"]].isna().all().all())

    def test_table_3_preserves_complete_main_analysis(self):
        self.assertEqual(len(self.table_3), 1)
        result = self.table_3.iloc[0]

        self.assertEqual(result["n"], 72)
        self.assertAlmostEqual(result["rho_spearman"], 0.7044568459379132)
        self.assertAlmostEqual(result["ic95_inferior"], 0.5613847929036577)
        self.assertAlmostEqual(result["ic95_superior"], 0.8077108647206857)
        self.assertAlmostEqual(result["p_valor"], 5.026909868083026e-12)

    def test_notebook_is_executed_contains_titles_and_does_not_recalculate_spearman(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
        notebook_source = "\n".join(cell.source for cell in notebook.cells)
        self.assertTrue(all(cell.execution_count is not None for cell in code_cells))
        self.assertFalse(
            any(output.get("output_type") == "error" for cell in code_cells for output in cell.get("outputs", []))
        )
        for title in [TABLE_1_TITLE, TABLE_2_TITLE, TABLE_3_TITLE]:
            self.assertIn(title, notebook_source)
        self.assertNotIn("spearmanr(", notebook_source)
        self.assertNotIn("spearman_with_bootstrap_ci(", notebook_source)

        output_text = "\n".join(
            output.get("text", "")
            for cell in code_cells
            for output in cell.get("outputs", [])
            if output.get("output_type") == "stream"
        )
        for expected in [
            "Tabela 1 validada: 64 linhas",
            "Tabela 2 gerada: 5 linhas",
            "Tabela 3 validada: N = 72; rho = 0,704; IC95% 0,561 a 0,808; p = 5,027e-12",
            "Nenhum resultado inferencial foi recalculado neste notebook.",
        ]:
            self.assertIn(expected, output_text)

    def test_tables_are_private_and_raw_is_unchanged(self):
        names = [name.casefold() for name in self.raw["nome"].dropna().str.strip() if name]
        serialized = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [NOTEBOOK_PATH, TABLE_1_PATH, TABLE_2_PATH, TABLE_3_PATH]
        ).casefold()

        self.assertFalse(any(name in serialized for name in names))
        for path in [TABLE_1_PATH, TABLE_2_PATH, TABLE_3_PATH]:
            self.assertIsNone(re.search(r"\bP\d{3}\b", path.read_text(encoding="utf-8")))
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

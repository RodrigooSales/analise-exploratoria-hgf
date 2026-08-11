import hashlib
import unittest
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "02_population_description.ipynb"
TABLE_PATH = ROOT / "outputs" / "tables" / "table_1_population.csv"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class PopulationDescriptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [path for path in [NOTEBOOK_PATH, TABLE_PATH] if not path.exists()]
        if missing:
            raise AssertionError(f"Artefatos da população ausentes: {missing}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.processed = pd.read_csv(PROCESSED_PATH)
        cls.table = pd.read_csv(TABLE_PATH)

    def test_table_schema_and_required_variables(self):
        self.assertEqual(
            self.table.columns.tolist(),
            [
                "secao",
                "variavel",
                "categoria",
                "n_valido",
                "n_ausente",
                "n",
                "percentual",
                "media",
                "moda",
                "desvio_padrao",
                "mediana",
                "p25",
                "p75",
                "minimo",
                "maximo",
                "observacoes",
            ],
        )
        required = {
            "Estado civil",
            "Escolaridade",
            "Renda mensal familiar",
            "Ocupação",
            "Diagnóstico",
            "Tempo de doença",
            "Uso de corticoide",
            "Uso de imunobiológico",
            "Comorbidades/medicamentos",
            "Tabagismo",
            "Etilismo",
            "Atividade física",
            "IMC (kg/m²)",
            "Circunferência abdominal (cm)",
            "Circunferência cervical (cm)",
            "FINDRISC (pontos)",
        }
        self.assertTrue(required.issubset(set(self.table["variavel"])))

    def test_numeric_statistics_are_complete(self):
        numeric = self.table[self.table["categoria"].eq("Resumo quantitativo")].set_index("variavel")
        imc = numeric.loc["IMC (kg/m²)"]

        self.assertEqual(len(numeric), 4)
        self.assertEqual(imc["n_valido"], 73)
        self.assertEqual(imc["n_ausente"], 2)
        self.assertAlmostEqual(imc["media"], 28.72, places=2)
        self.assertEqual(str(imc["moda"]), "29")
        self.assertAlmostEqual(imc["desvio_padrao"], 5.5, places=2)
        self.assertAlmostEqual(imc["mediana"], 27.94, places=2)
        self.assertAlmostEqual(imc["p25"], 24.62, places=2)
        self.assertAlmostEqual(imc["p75"], 32.3, places=2)
        self.assertEqual(imc["minimo"], 17.5)
        self.assertEqual(imc["maximo"], 41.1)

    def test_categorical_percentages_use_variable_valid_denominator(self):
        categorical = self.table[self.table["categoria"].ne("Resumo quantitativo")]

        for variable, rows in categorical.groupby("variavel"):
            with self.subTest(variable=variable):
                self.assertEqual(int(rows["n"].sum()), int(rows["n_valido"].iloc[0]))
                self.assertAlmostEqual(float(rows["percentual"].sum()), 100, delta=0.05)

        immunobiologic = categorical[categorical["variavel"].eq("Uso de imunobiológico")]
        self.assertEqual(immunobiologic["n_valido"].unique().tolist(), [63])
        self.assertEqual(immunobiologic["n_ausente"].unique().tolist(), [12])

    def test_rare_occupations_are_grouped_for_privacy(self):
        occupation = self.table[self.table["variavel"].eq("Ocupação")]
        rare_group = occupation[occupation["categoria"].eq("Outras ocupações")]

        self.assertEqual(len(rare_group), 1)
        self.assertGreater(int(rare_group["n"].iloc[0]), 0)
        self.assertTrue(occupation.loc[occupation["categoria"].ne("Outras ocupações"), "n"].ge(3).all())

    def test_table_contains_no_patient_identifiers(self):
        names = [name.casefold() for name in self.raw["nome"].dropna().str.strip() if name]
        serialized = TABLE_PATH.read_text(encoding="utf-8").casefold()

        self.assertFalse(any(name in serialized for name in names))
        self.assertFalse(self.table.astype("string").apply(lambda col: col.str.fullmatch(r"P\d{3}")).any().any())

    def test_notebook_is_executed_and_documents_limitations(self):
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
            "Amostra descrita: 75 pacientes",
            "Percentuais categóricos calculados com denominador válido por variável.",
            "Tempo de doença não resumido quantitativamente: campo sem unidade padronizada.",
            "Nenhum teste inferencial foi realizado.",
        ]:
            self.assertIn(expected, output_text)

    def test_raw_dataset_is_unchanged(self):
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

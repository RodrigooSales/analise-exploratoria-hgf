import hashlib
import re
import unittest
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "06_secondary_analysis.ipynb"
RESULTS_PATH = ROOT / "outputs" / "tables" / "secondary_analysis_results.csv"
DESCRIPTIVE_PATH = ROOT / "outputs" / "tables" / "secondary_analysis_descriptive.csv"
DECISIONS_PATH = ROOT / "outputs" / "tables" / "secondary_analysis_decisions.csv"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class SecondaryAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        artifacts = [NOTEBOOK_PATH, RESULTS_PATH, DESCRIPTIVE_PATH, DECISIONS_PATH]
        missing = [path for path in artifacts if not path.exists()]
        if missing:
            raise AssertionError(f"Artefatos das análises secundárias ausentes: {missing}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.results = pd.read_csv(RESULTS_PATH)
        cls.descriptive = pd.read_csv(DESCRIPTIVE_PATH)
        cls.decisions = pd.read_csv(DECISIONS_PATH)

    def test_only_four_prespecified_tests_are_run(self):
        expected = {
            ("Corticoide", "IMC"),
            ("Corticoide", "FINDRISC"),
            ("Atividade física atual", "IMC"),
            ("Atividade física atual", "FINDRISC"),
        }

        self.assertEqual(len(self.results), 4)
        self.assertEqual(set(zip(self.results["exposicao"], self.results["desfecho"])), expected)
        self.assertTrue(self.results["analise"].eq("ANÁLISE EXPLORATÓRIA SECUNDÁRIA").all())
        self.assertTrue(self.results["teste"].eq("Mann–Whitney bilateral").all())
        self.assertTrue(self.results["tamanho_efeito"].eq("Correlação bisserial de postos").all())
        self.assertTrue(self.results["bootstrap"].eq(10_000).all())
        self.assertTrue(self.results["random_state"].eq(42).all())

    def test_results_include_n_effect_ci_raw_and_holm_pvalues(self):
        corticoid_imc = self.results.set_index(["exposicao", "desfecho"]).loc[("Corticoide", "IMC")]
        activity_findrisc = self.results.set_index(["exposicao", "desfecho"]).loc[
            ("Atividade física atual", "FINDRISC")
        ]

        self.assertEqual(corticoid_imc["n_total"], 73)
        self.assertEqual(corticoid_imc["n_referencia"], 44)
        self.assertEqual(corticoid_imc["n_comparacao"], 29)
        self.assertAlmostEqual(corticoid_imc["efeito"], 0.1206896551724137)
        self.assertAlmostEqual(corticoid_imc["ic95_inferior"], -0.1614420062695925)
        self.assertAlmostEqual(corticoid_imc["ic95_superior"], 0.3950039184952976)
        self.assertAlmostEqual(corticoid_imc["p_valor"], 0.38842853710797454)

        self.assertEqual(activity_findrisc["n_total"], 74)
        self.assertEqual(activity_findrisc["n_referencia"], 42)
        self.assertEqual(activity_findrisc["n_comparacao"], 32)
        self.assertAlmostEqual(activity_findrisc["efeito"], -0.2566964285714286)
        self.assertAlmostEqual(activity_findrisc["ic95_inferior"], -0.5141369047619048)
        self.assertAlmostEqual(activity_findrisc["ic95_superior"], 0.0074590773809521)
        self.assertAlmostEqual(activity_findrisc["p_valor"], 0.05997429166999789)
        self.assertAlmostEqual(activity_findrisc["p_ajustado_holm"], 0.2398971666799915)

    def test_descriptive_table_reports_both_groups_before_each_test(self):
        self.assertEqual(len(self.descriptive), 8)
        counts = self.descriptive.groupby(["exposicao", "desfecho"])["grupo"].nunique()
        self.assertTrue(counts.eq(2).all())
        required = {
            "n_valido",
            "n_ausente_no_grupo",
            "media",
            "desvio_padrao",
            "mediana",
            "p25",
            "p75",
            "minimo",
            "maximo",
        }
        self.assertTrue(required.issubset(self.descriptive.columns))

    def test_discarded_analyses_and_reasons_are_documented(self):
        decisions = self.decisions.set_index("variavel")

        self.assertEqual(decisions.loc["Corticoide", "status"], "Realizada")
        self.assertEqual(decisions.loc["Atividade física", "status"], "Realizada")
        for variable in [
            "Imunobiológico",
            "Tabagismo",
            "Etilismo",
            "Renda",
            "Escolaridade",
            "Tempo de doença",
        ]:
            self.assertEqual(decisions.loc[variable, "status"], "Não realizada")
            self.assertTrue(bool(decisions.loc[variable, "justificativa"]))

    def test_notebook_is_executed_and_documents_method_and_limitations(self):
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
            "ANÁLISE EXPLORATÓRIA SECUNDÁRIA — Corticoide × IMC",
            "ANÁLISE EXPLORATÓRIA SECUNDÁRIA — Corticoide × FINDRISC",
            "ANÁLISE EXPLORATÓRIA SECUNDÁRIA — Atividade física atual × IMC",
            "ANÁLISE EXPLORATÓRIA SECUNDÁRIA — Atividade física atual × FINDRISC",
            "Teste: Mann–Whitney bilateral",
            "Tamanho de efeito: correlação bisserial de postos",
            "Ajuste de multiplicidade: método de Holm para 4 testes.",
            "A atividade física integra o cálculo do FINDRISC",
            "Nenhuma interpretação causal foi realizada.",
        ]:
            self.assertIn(expected, output_text)

    def test_outputs_are_aggregate_private_and_raw_is_unchanged(self):
        names = [name.casefold() for name in self.raw["nome"].dropna().str.strip() if name]
        serialized = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [NOTEBOOK_PATH, RESULTS_PATH, DESCRIPTIVE_PATH, DECISIONS_PATH]
        ).casefold()

        self.assertFalse(any(name in serialized for name in names))
        self.assertIsNone(re.search(r"\bP\d{3}\b", RESULTS_PATH.read_text(encoding="utf-8")))
        self.assertIsNone(re.search(r"\bP\d{3}\b", DESCRIPTIVE_PATH.read_text(encoding="utf-8")))
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

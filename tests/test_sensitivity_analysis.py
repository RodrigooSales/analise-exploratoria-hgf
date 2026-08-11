import hashlib
import re
import unittest
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "06_secondary_analysis.ipynb"
RESULTS_PATH = ROOT / "outputs" / "tables" / "sensitivity_analysis_results.csv"
OUTLIER_PATH = ROOT / "outputs" / "tables" / "sensitivity_outlier_audit.csv"
RULE_PATH = ROOT / "outputs" / "tables" / "sensitivity_diagnosis_rule.csv"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class SensitivityAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        artifacts = [NOTEBOOK_PATH, RESULTS_PATH, OUTLIER_PATH, RULE_PATH]
        missing = [path for path in artifacts if not path.exists()]
        if missing:
            raise AssertionError(f"Artefatos da sensibilidade ausentes: {missing}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.results = pd.read_csv(RESULTS_PATH)
        cls.outliers = pd.read_csv(OUTLIER_PATH)
        cls.rule = pd.read_csv(RULE_PATH)

    def test_main_and_single_autoimmune_diagnosis_results_are_compared(self):
        results = self.results.set_index("cenario")
        main = results.loc["Todos os pacientes com pares válidos"]
        single = results.loc["Apenas um diagnóstico autoimune"]

        self.assertEqual(len(results), 2)
        self.assertEqual(main["n_elegivel"], 75)
        self.assertEqual(main["n"], 72)
        self.assertAlmostEqual(main["rho"], 0.7044568459379132)
        self.assertAlmostEqual(main["ic95_inferior"], 0.5613847929036577)
        self.assertAlmostEqual(main["ic95_superior"], 0.8077108647206857)
        self.assertAlmostEqual(main["p_valor"], 5.026909868083026e-12)

        self.assertEqual(single["n_elegivel"], 68)
        self.assertEqual(single["n"], 65)
        self.assertAlmostEqual(single["rho"], 0.7635960582356662)
        self.assertAlmostEqual(single["ic95_inferior"], 0.6433892514872337)
        self.assertAlmostEqual(single["ic95_superior"], 0.8431783830270378)
        self.assertAlmostEqual(single["p_valor"], 1.395473962759173e-13)
        self.assertTrue(results["bootstrap"].eq(10_000).all())
        self.assertTrue(results["random_state"].eq(42).all())

    def test_diagnosis_rule_is_explicit_and_population_counts_are_documented(self):
        autoimmune = set(self.rule.loc[self.rule["classificacao"].eq("Autoimune"), "termo"])

        self.assertEqual(
            autoimmune,
            {
                "Arterite temporal",
                "Artrite reumatoide",
                "Espondiloartrite",
                "Lúpus eritematoso",
                "Síndrome antifosfolipídica (SAF)",
            },
        )
        self.assertIn("Doença de BC", set(self.rule.loc[self.rule["classificacao"].eq("Incerto"), "termo"]))
        self.assertEqual(self.results.loc[1, "n_elegivel"], 68)

    def test_extremes_are_audited_and_no_valid_value_is_excluded(self):
        expected = {
            ("IMC", "Mínimo"): 17.5,
            ("IMC", "Máximo"): 41.1,
            ("FINDRISC", "Mínimo"): 2.0,
            ("FINDRISC", "Máximo"): 24.0,
        }

        self.assertEqual(len(self.outliers), 4)
        for key, value in expected.items():
            row = self.outliers.set_index(["variavel", "extremo"]).loc[key]
            self.assertEqual(row["valor"], value)
            self.assertTrue(row["presente_no_bruto"])
            self.assertTrue(row["transformacao_consistente"])
            self.assertTrue(row["faixa_plausivel"])
            self.assertFalse(row["outlier_iqr"])
            self.assertEqual(row["classificacao"], "Valor extremo verdadeiro")
            self.assertFalse(row["excluido"])

    def test_notebook_reports_stability_and_does_not_select_by_pvalue(self):
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
            "ANÁLISE DE SENSIBILIDADE — DIAGNÓSTICOS MÚLTIPLOS",
            "Todos os pacientes: N = 72; rho = 0,704; IC95% 0,561 a 0,808; p = 5,027e-12",
            "Um diagnóstico autoimune: N = 65; rho = 0,764; IC95% 0,643 a 0,843; p = 1,395e-13",
            "Diferença absoluta entre os rhos: 0,059",
            "A conclusão principal permaneceu aproximadamente estável.",
            "Nenhum valor foi excluído após a investigação de extremos.",
            "O cenário de sensibilidade não foi escolhido por apresentar menor p-valor.",
        ]:
            self.assertIn(expected, output_text)

    def test_outputs_are_private_and_raw_is_unchanged(self):
        names = [name.casefold() for name in self.raw["nome"].dropna().str.strip() if name]
        serialized = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [NOTEBOOK_PATH, RESULTS_PATH, OUTLIER_PATH, RULE_PATH]
        ).casefold()

        self.assertFalse(any(name in serialized for name in names))
        self.assertIsNone(re.search(r"\bP\d{3}\b", RESULTS_PATH.read_text(encoding="utf-8")))
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

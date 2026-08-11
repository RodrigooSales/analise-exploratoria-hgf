import hashlib
import unittest
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
NOTEBOOK_PATH = ROOT / "notebooks" / "01_data_cleaning.ipynb"
MAPPING_PATH = ROOT / "outputs" / "tables" / "diagnosis_mapping.csv"
DISTRIBUTION_PATH = ROOT / "outputs" / "tables" / "diagnosis_distribution.csv"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"


class DiagnosisPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [path for path in [MAPPING_PATH, DISTRIBUTION_PATH] if not path.exists()]
        if missing:
            raise AssertionError(f"Outputs de diagnóstico ausentes: {missing}")
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.processed = pd.read_csv(PROCESSED_PATH)
        cls.mapping = pd.read_csv(MAPPING_PATH)
        cls.distribution = pd.read_csv(DISTRIBUTION_PATH)

    def test_mapping_is_explicit_and_covers_every_valid_patient(self):
        self.assertEqual(
            self.mapping.columns.tolist(),
            [
                "diagnostico_original",
                "diagnostico_normalizado",
                "diagnostico_padronizado",
                "n_registros",
            ],
        )
        self.assertEqual(int(self.mapping["n_registros"].sum()), 75)
        self.assertEqual(len(self.mapping), 15)
        self.assertTrue(self.mapping["diagnostico_padronizado"].notna().all())

    def test_distribution_reports_n_and_percentage(self):
        expected_counts = {
            "Lúpus eritematoso": 26,
            "Artrite reumatoide": 23,
            "Espondiloartrite": 14,
            "Lúpus eritematoso, Fibromialgia": 2,
            "Doença de BC": 2,
            "Osteoporose, Arterite temporal, Artrose": 1,
            "Artrite reumatoide, Artrose, Fibromialgia, Lúpus eritematoso": 1,
            "Artrite reumatoide, Artrose": 1,
            "Artrose": 1,
            "Fibromialgia, Artrose, Osteoporose": 1,
            "Osteoporose": 1,
            "Síndrome antifosfolipídica (SAF)": 1,
            "Em descoberta": 1,
        }

        self.assertEqual(self.distribution.columns.tolist(), ["diagnostico", "n", "percentual"])
        self.assertEqual(
            self.distribution.set_index("diagnostico")["n"].to_dict(), expected_counts
        )
        self.assertEqual(int(self.distribution["n"].sum()), 75)
        self.assertAlmostEqual(float(self.distribution["percentual"].sum()), 100, delta=0.05)

    def test_multiple_diagnoses_are_preserved(self):
        original_multiple = self.processed["diagnostico_original"].astype("string").str.contains(
            r",|\se\s", case=False, regex=True, na=False
        )
        standardized_multiple = self.processed["diagnostico_padronizado"].astype("string").str.contains(
            ",", regex=False, na=False
        )

        self.assertEqual(int(original_multiple.sum()), 6)
        self.assertEqual(int(standardized_multiple.sum()), 6)
        self.assertTrue(self.processed.loc[original_multiple, "diagnostico_padronizado"].notna().all())

    def test_diagnosis_outputs_contain_no_patient_names(self):
        names = [name.casefold() for name in self.raw["nome"].dropna().str.strip() if name]
        output_text = (
            MAPPING_PATH.read_text(encoding="utf-8")
            + DISTRIBUTION_PATH.read_text(encoding="utf-8")
        ).casefold()

        self.assertFalse(any(name in output_text for name in names))

    def test_notebook_documents_descriptive_single_cohort_use(self):
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        output_text = "\n".join(
            output.get("text", "")
            for cell in notebook.cells
            if cell.cell_type == "code"
            for output in cell.get("outputs", [])
            if output.get("output_type") == "stream"
        )

        for expected in [
            "Distribuição diagnóstica descritiva",
            "Diagnósticos válidos: 75",
            "Categorias padronizadas: 13",
            "Registros com diagnósticos múltiplos preservados: 6",
            "Coorte analítica única: 75 pacientes",
            "Sem testes comparativos entre diagnósticos.",
        ]:
            self.assertIn(expected, output_text)

    def test_raw_dataset_is_unchanged(self):
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()

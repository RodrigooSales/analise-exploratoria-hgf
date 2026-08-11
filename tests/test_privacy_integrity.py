import hashlib
import json
import re
import unittest
import unicodedata
from pathlib import Path

import nbformat
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "sociodemografico.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "pacientes_clean.csv"
RAW_SHA256 = "a895b5340c856d2cd1772c8e115ed5efc20f409d3aef5ecba14da23d44da9bf4"
DIRECT_IDENTIFIER_COLUMNS = {
    "cod",
    "codigo",
    "nome",
    "cpf",
    "rg",
    "cns",
    "cartao_sus",
    "telefone",
    "celular",
    "email",
    "endereco",
    "data_nascimento",
}
CPF_PATTERN = re.compile(r"(?<!\d)\d{3}[.\s-]?\d{3}[.\s-]?\d{3}[-\s]?\d{2}(?!\d)")
EMAIL_PATTERN = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
FORMATTED_PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?55\s*)?\(?[1-9]\d\)?[\s.-]+(?:9\d{4}|[2-5]\d{3})[\s.-]?\d{4}(?!\d)"
)
UNFORMATTED_PHONE_PATTERN = re.compile(r"(?<!\d)(?:55)?[1-9]\d9\d{8}(?!\d)")
PATIENT_ID_PATTERN = re.compile(r"(?i)\bP\d{3}\b")
TEXT_MIME_TYPES = {"text/plain", "text/html", "text/markdown", "application/json"}


def _normalize_column(column: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(column))
    ascii_text = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.casefold()).strip("_")


def _contains_direct_contact(text: str) -> bool:
    return any(
        pattern.search(text)
        for pattern in [
            CPF_PATTERN,
            EMAIL_PATTERN,
            FORMATTED_PHONE_PATTERN,
            UNFORMATTED_PHONE_PATTERN,
        ]
    )


def _notebook_text(notebook) -> tuple[str, str]:
    source = []
    rendered = []
    for cell in notebook.cells:
        source.append(cell.source)
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream":
                rendered.append(str(output.get("text", "")))
            for mime_type, value in output.get("data", {}).items():
                if mime_type not in TEXT_MIME_TYPES:
                    continue
                rendered.append(
                    json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                )
    return "\n".join(source), "\n".join(rendered)


class PrivacyIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(RAW_PATH, dtype="string")
        cls.processed = pd.read_csv(PROCESSED_PATH, dtype="string")
        cls.patient_names = {
            value.strip().casefold()
            for value in cls.raw["nome"].dropna()
            if value.strip()
        }

    def assertContainsNoPatientName(self, text: str, scope: str):
        normalized = text.casefold()
        self.assertFalse(
            any(name in normalized for name in self.patient_names),
            f"Nome de paciente detectado em {scope}.",
        )

    def test_processed_dataset_is_pseudonymized_and_patient_id_is_valid(self):
        normalized_columns = {_normalize_column(column) for column in self.processed.columns}
        processed_paths = sorted(
            path for path in (ROOT / "data" / "processed").rglob("*") if path.is_file()
        )

        self.assertEqual(processed_paths, [PROCESSED_PATH])
        self.assertIn("patient_id", self.processed.columns)
        self.assertTrue(self.processed["patient_id"].notna().all())
        self.assertTrue(self.processed["patient_id"].is_unique)
        self.assertTrue(self.processed["patient_id"].str.fullmatch(r"P\d{3}").all())
        self.assertTrue((normalized_columns - {"patient_id"}).isdisjoint(DIRECT_IDENTIFIER_COLUMNS))
        serialized = self.processed.to_csv(index=False)
        self.assertContainsNoPatientName(serialized, "data/processed")
        self.assertFalse(_contains_direct_contact(serialized))

    def test_output_tables_have_no_direct_identifier_columns_or_values(self):
        table_paths = sorted((ROOT / "outputs" / "tables").glob("*.csv"))
        self.assertTrue(table_paths)

        for path in table_paths:
            with self.subTest(table=path.name):
                table = pd.read_csv(path, dtype="string")
                normalized_columns = {_normalize_column(column) for column in table.columns}
                self.assertTrue(normalized_columns.isdisjoint(DIRECT_IDENTIFIER_COLUMNS))
                serialized = path.read_text(encoding="utf-8")
                self.assertContainsNoPatientName(serialized, str(path.relative_to(ROOT)))
                self.assertFalse(_contains_direct_contact(serialized))
                self.assertIsNone(PATIENT_ID_PATTERN.search(serialized))

    def test_every_output_file_is_covered_by_the_privacy_audit(self):
        output_files = {
            path for path in (ROOT / "outputs").rglob("*") if path.is_file()
        }
        audited_files = set((ROOT / "outputs" / "tables").glob("*.csv")) | set(
            (ROOT / "outputs" / "figures").glob("*.png")
        )

        self.assertEqual(output_files, audited_files)

    def test_executed_notebooks_have_no_identifiers_in_source_or_rendered_outputs(self):
        notebook_paths = sorted((ROOT / "notebooks").glob("*.ipynb"))
        self.assertEqual(len(notebook_paths), 8)

        for path in notebook_paths:
            with self.subTest(notebook=path.name):
                notebook = nbformat.read(path, as_version=4)
                code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
                self.assertTrue(all(cell.execution_count is not None for cell in code_cells))
                self.assertFalse(
                    any(
                        output.get("output_type") == "error"
                        for cell in code_cells
                        for output in cell.get("outputs", [])
                    )
                )
                source, rendered = _notebook_text(notebook)
                self.assertContainsNoPatientName(source, f"fonte de {path.name}")
                self.assertContainsNoPatientName(rendered, f"outputs de {path.name}")
                self.assertFalse(_contains_direct_contact(rendered))
                self.assertIsNone(PATIENT_ID_PATTERN.search(rendered))

    def test_figures_open_and_have_no_sensitive_metadata(self):
        figure_paths = sorted((ROOT / "outputs" / "figures").glob("*.png"))
        self.assertTrue(figure_paths)

        for path in figure_paths:
            with self.subTest(figure=path.name):
                with Image.open(path) as image:
                    metadata = " ".join(str(value) for value in image.info.values())
                    self.assertContainsNoPatientName(metadata, str(path.relative_to(ROOT)))
                    self.assertFalse(_contains_direct_contact(metadata))
                    self.assertIsNone(PATIENT_ID_PATTERN.search(metadata))
                    image.verify()

    def test_project_logs_have_no_direct_identifiers(self):
        log_paths = [
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and path.suffix.casefold() in {".log", ".out", ".err"}
            and ".venv" not in path.parts
            and ".git" not in path.parts
        ]

        for path in log_paths:
            with self.subTest(log=str(path.relative_to(ROOT))):
                text = path.read_text(encoding="utf-8", errors="replace")
                self.assertContainsNoPatientName(text, str(path.relative_to(ROOT)))
                self.assertFalse(_contains_direct_contact(text))
                self.assertIsNone(PATIENT_ID_PATTERN.search(text))

    def test_raw_file_integrity_is_preserved(self):
        self.assertEqual(hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(), RAW_SHA256)

    def test_detectors_recognize_synthetic_direct_identifiers(self):
        for synthetic_value in [
            "123.456.789-00",
            "(85) 91234-5678",
            "85912345678",
            "pessoa@example.org",
        ]:
            with self.subTest(identifier_type=synthetic_value[-3:]):
                self.assertTrue(_contains_direct_contact(synthetic_value))
        self.assertIsNotNone(PATIENT_ID_PATTERN.search("P001"))


if __name__ == "__main__":
    unittest.main()

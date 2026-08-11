import unittest

import pandas as pd

from src.cleaning import (
    anonymize_patients,
    clean_numeric_column,
    clean_text_column,
    create_patient_id,
    identify_empty_records,
    remove_empty_records,
)


class CleaningTests(unittest.TestCase):
    def test_clean_text_column_removes_extra_whitespace_and_preserves_missing(self):
        original = pd.Series(
            ["  Ensino   médio  ", "Não", "   ", None, pd.NA],
            name="escolaridade",
            dtype="string",
        )

        cleaned = clean_text_column(original)

        self.assertEqual(cleaned.iloc[0], "Ensino médio")
        self.assertEqual(cleaned.iloc[1], "Não")
        self.assertTrue(cleaned.iloc[2:].isna().all())
        self.assertEqual(cleaned.name, original.name)
        self.assertEqual(original.iloc[0], "  Ensino   médio  ")

    def test_clean_numeric_column_handles_decimal_separators_safely(self):
        original = pd.Series(
            [
                "28,5",
                "27.06",
                32,
                " 38,74 ",
                "",
                None,
                "inválido",
                "1.234,56",
                "inf",
                "-inf",
            ],
            name="imc",
        )

        cleaned = clean_numeric_column(original)

        expected = [28.5, 27.06, 32.0, 38.74]
        self.assertEqual(cleaned.iloc[:4].tolist(), expected)
        self.assertTrue(cleaned.iloc[4:].isna().all())
        self.assertEqual(cleaned.name, original.name)

    def test_identify_empty_records_uses_patient_column(self):
        frame = pd.DataFrame(
            {
                "nome": ["Pessoa A", "  ", None, pd.NA],
                "Cod": [1, 2, 3, 4],
                "valor_padrao": [False, False, False, False],
            }
        )

        empty = identify_empty_records(frame, patient_column="nome")

        self.assertEqual(empty.tolist(), [False, True, True, True])

    def test_identify_empty_records_can_evaluate_all_columns(self):
        frame = pd.DataFrame({"a": [None, "", "x"], "b": [pd.NA, "  ", None]})

        empty = identify_empty_records(frame, patient_column=None)

        self.assertEqual(empty.tolist(), [True, True, False])

    def test_remove_empty_records_returns_copy_without_resetting_index(self):
        frame = pd.DataFrame(
            {"nome": ["Pessoa A", None, " Pessoa B "], "valor": [1, 2, 3]},
            index=[4, 7, 9],
        )

        result = remove_empty_records(frame, patient_column="nome")
        result.loc[4, "valor"] = 99

        self.assertEqual(result.index.tolist(), [4, 9])
        self.assertEqual(frame.loc[4, "valor"], 1)

    def test_create_patient_id_is_sequential_and_preserves_index(self):
        frame = pd.DataFrame({"valor": [10, 20]}, index=[5, 8])

        patient_id = create_patient_id(frame)

        self.assertEqual(patient_id.tolist(), ["P001", "P002"])
        self.assertEqual(patient_id.index.tolist(), [5, 8])
        self.assertEqual(patient_id.name, "patient_id")

    def test_anonymize_patients_drops_name_without_mutating_input(self):
        frame = pd.DataFrame({"nome": ["Pessoa A", "Pessoa B"], "imc": [25.0, 30.0]})

        anonymized = anonymize_patients(frame, name_column="nome")

        self.assertEqual(anonymized.columns.tolist(), ["patient_id", "imc"])
        self.assertEqual(anonymized["patient_id"].tolist(), ["P001", "P002"])
        self.assertNotIn("nome", anonymized.columns)
        self.assertIn("nome", frame.columns)

    def test_anonymize_patients_rejects_nominal_id_column(self):
        frame = pd.DataFrame({"nome": ["Pessoa A"]})

        with self.assertRaises(ValueError):
            anonymize_patients(frame, name_column="nome", id_column="nome")


if __name__ == "__main__":
    unittest.main()

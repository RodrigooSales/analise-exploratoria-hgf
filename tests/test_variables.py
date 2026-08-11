import unittest

import pandas as pd

from src.variables import (
    AUTOIMMUNE_DIAGNOSES,
    classificar_findrisc,
    classificar_imc,
    count_autoimmune_diagnoses,
    create_atividade_fisica_atual,
    create_excesso_peso,
    create_findrisc_alto,
    create_obesidade,
    extract_findrisc_score,
)


class VariableTests(unittest.TestCase):
    def test_classificar_imc_respects_all_clinical_boundaries(self):
        cases = {
            18.49: "Baixo peso",
            18.5: "Peso normal",
            24.99: "Peso normal",
            25: "Sobrepeso",
            29.99: "Sobrepeso",
            30: "Obesidade grau I",
            34.99: "Obesidade grau I",
            35: "Obesidade grau II",
            39.99: "Obesidade grau II",
            40: "Obesidade grau III",
        }

        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(classificar_imc(value), expected)
        self.assertTrue(pd.isna(classificar_imc(None)))
        self.assertTrue(pd.isna(classificar_imc(pd.NA)))

    def test_classificar_findrisc_respects_all_score_boundaries(self):
        cases = {
            6: "Baixo risco",
            7: "Leve/moderado",
            11: "Leve/moderado",
            12: "Moderado",
            14: "Moderado",
            15: "Alto",
            20: "Alto",
            21: "Muito alto",
        }

        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(classificar_findrisc(value), expected)
        self.assertTrue(pd.isna(classificar_findrisc(float("nan"))))

    def test_extract_findrisc_score_uses_only_leading_integer(self):
        original = pd.Series(
            [
                "23 (Muito Alto Risco)",
                "16 (Risco Moderado)",
                "17 (Alto Risco)",
                " 7 ",
                None,
                "",
                "inválido",
                "12,5",
                "texto 15",
            ]
        )

        score = extract_findrisc_score(original)

        self.assertEqual(score.dtype, pd.Int64Dtype())
        self.assertEqual(score.iloc[:4].tolist(), [23, 16, 17, 7])
        self.assertTrue(score.iloc[4:].isna().all())

    def test_create_excesso_peso_preserves_missing(self):
        result = create_excesso_peso(pd.Series([24.99, 25, None, "inválido"]))

        self.assertEqual(result.dtype, pd.BooleanDtype())
        self.assertEqual(result.iloc[:2].tolist(), [False, True])
        self.assertTrue(result.iloc[2:].isna().all())

    def test_create_obesidade_preserves_missing(self):
        result = create_obesidade(pd.Series([29.99, 30, pd.NA]))

        self.assertEqual(result.iloc[:2].tolist(), [False, True])
        self.assertTrue(pd.isna(result.iloc[2]))

    def test_create_findrisc_alto_preserves_missing(self):
        result = create_findrisc_alto(pd.Series([14, 15, float("nan")]))

        self.assertEqual(result.iloc[:2].tolist(), [False, True])
        self.assertTrue(pd.isna(result.iloc[2]))

    def test_create_atividade_fisica_atual_uses_explicit_current_status(self):
        original = pd.Series(
            [
                "Não",
                " Atualmente não ",
                "Parou há 1 ano",
                "Sim",
                "Caminhada 3x por semana",
                None,
                " ",
            ]
        )

        result = create_atividade_fisica_atual(original)

        self.assertEqual(result.dtype, pd.BooleanDtype())
        self.assertEqual(result.iloc[:5].tolist(), [False, False, False, True, True])
        self.assertTrue(result.iloc[5:].isna().all())

    def test_count_autoimmune_diagnoses_uses_explicit_terms(self):
        diagnoses = pd.Series(
            [
                "Lúpus eritematoso",
                "Lúpus eritematoso, Fibromialgia",
                "Artrite reumatoide, Artrose, Lúpus eritematoso",
                "Osteoporose, Arterite temporal, Artrose",
                "Doença de BC",
                None,
            ]
        )

        result = count_autoimmune_diagnoses(diagnoses)

        self.assertEqual(result.dtype, pd.Int64Dtype())
        self.assertEqual(result.iloc[:5].tolist(), [1, 1, 2, 1, 0])
        self.assertTrue(pd.isna(result.iloc[5]))
        self.assertEqual(
            AUTOIMMUNE_DIAGNOSES,
            frozenset(
                {
                    "Arterite temporal",
                    "Artrite reumatoide",
                    "Espondiloartrite",
                    "Lúpus eritematoso",
                    "Síndrome antifosfolipídica (SAF)",
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()

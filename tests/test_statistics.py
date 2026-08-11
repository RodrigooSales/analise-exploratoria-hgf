import unittest

import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

from src.statistics import (
    RANDOM_STATE,
    descriptive_categorical,
    descriptive_numeric,
    mann_whitney_with_bootstrap_ci,
    missing_summary,
    proportion_with_ci,
    spearman_with_bootstrap_ci,
)


class StatisticsTests(unittest.TestCase):
    def test_descriptive_numeric_uses_only_valid_values(self):
        result = descriptive_numeric(pd.Series([1, 2, 2, 4, None]))

        self.assertEqual(result["n_valido"], 4)
        self.assertEqual(result["n_ausente"], 1)
        self.assertEqual(result["media"], 2.25)
        self.assertEqual(result["moda"], "2")
        self.assertAlmostEqual(result["desvio_padrao"], 1.258305739, places=8)
        self.assertEqual(result["mediana"], 2)
        self.assertEqual(result["p25"], 1.75)
        self.assertEqual(result["p75"], 2.5)
        self.assertEqual(result["minimo"], 1)
        self.assertEqual(result["maximo"], 4)

    def test_descriptive_numeric_reports_multiple_modes(self):
        result = descriptive_numeric(pd.Series([1, 1, 2, 2, 3, None]))

        self.assertEqual(result["moda"], "1; 2")
        self.assertIn("multimodal", result["observacoes"].casefold())

    def test_descriptive_numeric_marks_unique_mode_as_uninformative(self):
        result = descriptive_numeric(pd.Series([1, 2, 3, None]))

        self.assertTrue(pd.isna(result["moda"]))
        self.assertIn("não informativa", result["observacoes"].casefold())

    def test_descriptive_categorical_uses_valid_denominator(self):
        result = descriptive_categorical(pd.Series(["Sim", "Não", "Não", None, " "]))

        self.assertEqual(result["n_valido"].unique().tolist(), [3])
        self.assertEqual(result["n_ausente"].unique().tolist(), [2])
        self.assertEqual(result.set_index("categoria")["n"].to_dict(), {"Não": 2, "Sim": 1})
        self.assertAlmostEqual(result["percentual"].sum(), 100, places=1)

    def test_descriptive_categorical_groups_rare_values_without_losing_missing(self):
        result = descriptive_categorical(
            pd.Series(["A", "A", "A", "B", "B", "C", None]),
            min_count=3,
            other_label="Outras categorias",
        )

        self.assertEqual(
            result.set_index("categoria")["n"].to_dict(),
            {"A": 3, "Outras categorias": 3},
        )
        self.assertEqual(result["n_valido"].unique().tolist(), [6])
        self.assertEqual(result["n_ausente"].unique().tolist(), [1])

    def test_proportion_with_ci_uses_valid_denominator_and_wilson_interval(self):
        indicator = pd.Series([True] * 35 + [False] * 39 + [pd.NA], dtype="boolean")

        result = proportion_with_ci(indicator)

        self.assertEqual(result["n_valido"], 74)
        self.assertEqual(result["n_ausente"], 1)
        self.assertEqual(result["n"], 35)
        self.assertAlmostEqual(result["percentual"], 47.2972972973)
        self.assertAlmostEqual(result["ic95_inferior"], 36.3387069434)
        self.assertAlmostEqual(result["ic95_superior"], 58.5226432345)
        self.assertEqual(result["metodo_ic"], "Wilson")

    def test_proportion_with_ci_rejects_series_without_valid_values(self):
        with self.assertRaisesRegex(ValueError, "valor válido"):
            proportion_with_ci(pd.Series([pd.NA, None], dtype="boolean"))

    def test_missing_summary_reports_each_variable_without_imputation(self):
        data = pd.DataFrame(
            {
                "completo": [1, 2, 3, 4],
                "parcial": [1, None, 3, None],
                "vazio": [None, None, None, None],
            }
        )

        result = missing_summary(data)

        self.assertEqual(
            result.columns.tolist(),
            ["variavel", "n_valido", "n_ausente", "percentual_ausente"],
        )
        self.assertEqual(result["variavel"].tolist(), data.columns.tolist())
        self.assertEqual(result["n_valido"].tolist(), [4, 2, 0])
        self.assertEqual(result["n_ausente"].tolist(), [0, 2, 4])
        self.assertEqual(result["percentual_ausente"].tolist(), [0.0, 50.0, 100.0])

    def test_missing_summary_handles_dataframe_without_rows(self):
        result = missing_summary(pd.DataFrame(columns=["a", "b"]))

        self.assertEqual(result["n_valido"].tolist(), [0, 0])
        self.assertEqual(result["n_ausente"].tolist(), [0, 0])
        self.assertTrue(result["percentual_ausente"].isna().all())

    def test_spearman_bootstrap_uses_complete_pairs_and_is_reproducible(self):
        x = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, None])
        y = pd.Series([2, 1, 4, 3, 7, 5, None, 8, 9])
        complete = pd.concat([x, y], axis=1).dropna()
        expected = spearmanr(complete.iloc[:, 0], complete.iloc[:, 1])

        first = spearman_with_bootstrap_ci(x, y, n_bootstrap=5_000)
        second = spearman_with_bootstrap_ci(x, y, n_bootstrap=5_000)

        self.assertEqual(RANDOM_STATE, 42)
        self.assertEqual(first, second)
        self.assertEqual(first["n"], 7)
        self.assertAlmostEqual(first["rho"], expected.statistic)
        self.assertAlmostEqual(first["p"], expected.pvalue)
        self.assertLessEqual(first["ic95_inferior"], first["rho"])
        self.assertGreaterEqual(first["ic95_superior"], first["rho"])
        self.assertEqual(first["bootstrap"], 5_000)
        self.assertEqual(first["random_state"], 42)

    def test_spearman_bootstrap_defaults_to_ten_thousand_resamples(self):
        result = spearman_with_bootstrap_ci(
            pd.Series(range(12)),
            pd.Series([0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 11]),
        )

        self.assertEqual(result["bootstrap"], 10_000)

    def test_spearman_bootstrap_rejects_invalid_inputs(self):
        with self.assertRaisesRegex(ValueError, "5.000"):
            spearman_with_bootstrap_ci(pd.Series([1, 2, 3]), pd.Series([1, 2, 3]), n_bootstrap=4_999)
        with self.assertRaisesRegex(ValueError, "constante"):
            spearman_with_bootstrap_ci(pd.Series([1, 1, 1]), pd.Series([1, 2, 3]), n_bootstrap=5_000)

    def test_mann_whitney_returns_rank_biserial_ci_and_is_reproducible(self):
        reference = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, None])
        comparison = pd.Series([4, 5, 6, 7, 8, 9, 10, 11, None])
        expected = mannwhitneyu(comparison.dropna(), reference.dropna(), alternative="two-sided")

        first = mann_whitney_with_bootstrap_ci(
            reference,
            comparison,
            n_bootstrap=5_000,
        )
        second = mann_whitney_with_bootstrap_ci(
            reference,
            comparison,
            n_bootstrap=5_000,
        )

        self.assertEqual(first, second)
        self.assertEqual(first["n_referencia"], 8)
        self.assertEqual(first["n_comparacao"], 8)
        self.assertAlmostEqual(first["u"], expected.statistic)
        self.assertAlmostEqual(first["p"], expected.pvalue)
        self.assertAlmostEqual(first["correlacao_bisserial_postos"], 0.609375)
        self.assertLessEqual(first["ic95_inferior"], first["correlacao_bisserial_postos"])
        self.assertGreaterEqual(first["ic95_superior"], first["correlacao_bisserial_postos"])
        self.assertEqual(first["bootstrap"], 5_000)
        self.assertEqual(first["random_state"], 42)

    def test_mann_whitney_rejects_insufficient_samples_and_small_bootstrap(self):
        with self.assertRaisesRegex(ValueError, "5.000"):
            mann_whitney_with_bootstrap_ci(
                pd.Series([1, 2, 3]),
                pd.Series([4, 5, 6]),
                n_bootstrap=4_999,
            )
        with self.assertRaisesRegex(ValueError, "dois valores"):
            mann_whitney_with_bootstrap_ci(
                pd.Series([1, None]),
                pd.Series([2, 3]),
                n_bootstrap=5_000,
            )


if __name__ == "__main__":
    unittest.main()

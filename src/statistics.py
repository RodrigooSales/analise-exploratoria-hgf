"""Estatísticas descritivas reutilizáveis para a análise exploratória."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, rankdata, spearmanr
from statsmodels.stats.proportion import proportion_confint

from src.cleaning import clean_text_column

RANDOM_STATE = 42


def _format_numeric(value: float) -> str:
    return f"{float(value):g}"


def descriptive_numeric(series: pd.Series) -> dict[str, object]:
    """Resume uma variável quantitativa usando somente valores numéricos válidos.

    A moda inclui todos os valores empatados. Quando cada valor ocorre uma única
    vez, ela é marcada como não informativa em vez de selecionar um valor arbitrário.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    numeric = numeric.mask(numeric.isin([np.inf, -np.inf]))
    valid = numeric.dropna()
    n_valid = int(valid.size)
    observations = []

    if n_valid == 0:
        mode = pd.NA
        observations.append("Sem valores numéricos válidos.")
    else:
        counts = valid.value_counts()
        mode_frequency = int(counts.max())
        if mode_frequency == 1:
            mode = pd.NA
            observations.append("Moda não informativa: todos os valores são únicos.")
        else:
            modes = sorted(counts[counts.eq(mode_frequency)].index.tolist())
            mode = "; ".join(_format_numeric(value) for value in modes)
            if len(modes) > 1:
                observations.append(f"Distribuição multimodal ({len(modes)} modas).")

    return {
        "n_valido": n_valid,
        "n_ausente": int(len(series) - n_valid),
        "media": float(valid.mean()) if n_valid else np.nan,
        "moda": mode,
        "desvio_padrao": float(valid.std(ddof=1)) if n_valid > 1 else np.nan,
        "mediana": float(valid.median()) if n_valid else np.nan,
        "p25": float(valid.quantile(0.25)) if n_valid else np.nan,
        "p75": float(valid.quantile(0.75)) if n_valid else np.nan,
        "minimo": float(valid.min()) if n_valid else np.nan,
        "maximo": float(valid.max()) if n_valid else np.nan,
        "observacoes": " ".join(observations),
    }


def descriptive_categorical(
    series: pd.Series,
    *,
    min_count: int = 1,
    other_label: str | None = None,
    case_sensitive: bool = True,
) -> pd.DataFrame:
    """Calcula ``n (%)`` usando observações válidas como denominador.

    Categorias raras podem ser reunidas em ``other_label`` por meio de
    ``min_count``. Valores ausentes nunca são incorporados ao grupo residual.
    """
    if min_count < 1:
        raise ValueError("min_count deve ser pelo menos 1.")
    if min_count > 1 and not other_label:
        raise ValueError("other_label é obrigatório quando categorias raras são agrupadas.")

    cleaned = clean_text_column(series)
    if case_sensitive:
        categorical = cleaned
    else:
        keys = cleaned.str.casefold()
        representatives = (
            pd.DataFrame({"key": keys, "value": cleaned})
            .dropna()
            .drop_duplicates("key")
            .set_index("key")["value"]
        )
        categorical = keys.map(representatives).astype("string")

    n_valid = int(categorical.notna().sum())
    n_missing = int(len(categorical) - n_valid)
    if min_count > 1:
        counts = categorical.value_counts()
        rare_categories = counts[counts.lt(min_count)].index
        categorical = categorical.mask(categorical.isin(rare_categories), other_label)

    counts = categorical.value_counts(dropna=True)
    result = counts.rename_axis("categoria").reset_index(name="n")
    result["percentual"] = (100 * result["n"] / n_valid).round(2) if n_valid else np.nan
    result["n_valido"] = n_valid
    result["n_ausente"] = n_missing
    return result[["categoria", "n", "percentual", "n_valido", "n_ausente"]]


def missing_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Resume dados ausentes de cada variável sem modificar ou imputar valores."""
    n_rows = len(data)
    n_missing = data.isna().sum()
    result = pd.DataFrame(
        {
            "variavel": data.columns,
            "n_valido": n_rows - n_missing.to_numpy(),
            "n_ausente": n_missing.to_numpy(),
            "percentual_ausente": (
                100 * n_missing.to_numpy() / n_rows if n_rows else np.nan
            ),
        }
    )
    return result


def spearman_with_bootstrap_ci(
    x: pd.Series,
    y: pd.Series,
    *,
    n_bootstrap: int = 10_000,
    random_state: int = RANDOM_STATE,
) -> dict[str, float | int]:
    """Calcula Spearman e IC95% percentil por bootstrap pareado.

    As séries são alinhadas pelo índice e somente pares numéricos finitos são
    analisados. O retorno contém ``n``, ``rho``, limites do ``ic95``, ``p``,
    número de reamostragens ``bootstrap`` e a semente ``random_state``.
    """
    if n_bootstrap < 5_000:
        raise ValueError("O bootstrap requer pelo menos 5.000 reamostragens.")

    paired = pd.DataFrame(
        {
            "x": pd.to_numeric(x, errors="coerce"),
            "y": pd.to_numeric(y, errors="coerce"),
        }
    ).replace([np.inf, -np.inf], np.nan).dropna()
    if len(paired) < 3:
        raise ValueError("A correlação requer pelo menos três pares válidos.")
    if paired["x"].nunique() < 2 or paired["y"].nunique() < 2:
        raise ValueError("A correlação de Spearman não é definida para variável constante.")

    x_values = paired["x"].to_numpy(dtype=float)
    y_values = paired["y"].to_numpy(dtype=float)
    observed = spearmanr(x_values, y_values)

    rng = np.random.default_rng(random_state)
    bootstrap_rhos = np.empty(n_bootstrap, dtype=float)
    completed = 0
    attempts = 0
    maximum_attempts = n_bootstrap * 100
    while completed < n_bootstrap:
        batch_size = min(n_bootstrap - completed, 10_000)
        indices = rng.integers(0, len(paired), size=(batch_size, len(paired)))
        x_ranks = rankdata(x_values[indices], axis=1)
        y_ranks = rankdata(y_values[indices], axis=1)
        x_centered = x_ranks - x_ranks.mean(axis=1, keepdims=True)
        y_centered = y_ranks - y_ranks.mean(axis=1, keepdims=True)
        denominator = np.sqrt(
            np.square(x_centered).sum(axis=1) * np.square(y_centered).sum(axis=1)
        )
        valid = denominator > 0
        correlations = (
            (x_centered[valid] * y_centered[valid]).sum(axis=1) / denominator[valid]
        )
        accepted = min(len(correlations), n_bootstrap - completed)
        bootstrap_rhos[completed : completed + accepted] = correlations[:accepted]
        completed += accepted
        attempts += batch_size
        if attempts >= maximum_attempts and completed < n_bootstrap:
            raise RuntimeError("Não foi possível obter reamostragens bootstrap válidas.")

    lower, upper = np.percentile(bootstrap_rhos, [2.5, 97.5])
    return {
        "n": int(len(paired)),
        "rho": float(observed.statistic),
        "ic95_inferior": float(lower),
        "ic95_superior": float(upper),
        "p": float(observed.pvalue),
        "bootstrap": int(n_bootstrap),
        "random_state": int(random_state),
    }


def mann_whitney_with_bootstrap_ci(
    reference: pd.Series,
    comparison: pd.Series,
    *,
    n_bootstrap: int = 10_000,
    random_state: int = RANDOM_STATE,
) -> dict[str, float | int]:
    """Compara dois grupos independentes e estima IC95% do efeito por bootstrap.

    O teste de Mann–Whitney é bilateral e usa aproximação assintótica com correção
    para empates. O tamanho de efeito é a correlação bisserial de postos orientada
    como ``comparison - reference``; valores positivos indicam postos maiores no
    grupo de comparação. Ausências e valores infinitos são removidos separadamente.
    """
    if n_bootstrap < 5_000:
        raise ValueError("O bootstrap requer pelo menos 5.000 reamostragens.")

    reference_values = (
        pd.to_numeric(reference, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .to_numpy(dtype=float)
    )
    comparison_values = (
        pd.to_numeric(comparison, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .to_numpy(dtype=float)
    )
    if len(reference_values) < 2 or len(comparison_values) < 2:
        raise ValueError("Cada grupo deve possuir pelo menos dois valores válidos.")

    observed = mannwhitneyu(
        comparison_values,
        reference_values,
        alternative="two-sided",
        method="asymptotic",
    )
    denominator = len(comparison_values) * len(reference_values)
    effect = 2 * float(observed.statistic) / denominator - 1

    rng = np.random.default_rng(random_state)
    bootstrap_effects = np.empty(n_bootstrap, dtype=float)
    completed = 0
    while completed < n_bootstrap:
        batch_size = min(n_bootstrap - completed, 10_000)
        comparison_indices = rng.integers(
            0,
            len(comparison_values),
            size=(batch_size, len(comparison_values)),
        )
        reference_indices = rng.integers(
            0,
            len(reference_values),
            size=(batch_size, len(reference_values)),
        )
        combined = np.concatenate(
            [comparison_values[comparison_indices], reference_values[reference_indices]],
            axis=1,
        )
        ranks = rankdata(combined, axis=1)
        rank_sum = ranks[:, : len(comparison_values)].sum(axis=1)
        u_bootstrap = rank_sum - len(comparison_values) * (len(comparison_values) + 1) / 2
        bootstrap_effects[completed : completed + batch_size] = 2 * u_bootstrap / denominator - 1
        completed += batch_size

    lower, upper = np.percentile(bootstrap_effects, [2.5, 97.5])
    return {
        "n_referencia": int(len(reference_values)),
        "n_comparacao": int(len(comparison_values)),
        "u": float(observed.statistic),
        "correlacao_bisserial_postos": float(effect),
        "ic95_inferior": float(lower),
        "ic95_superior": float(upper),
        "p": float(observed.pvalue),
        "bootstrap": int(n_bootstrap),
        "random_state": int(random_state),
    }


def proportion_with_ci(
    indicator: pd.Series,
    *,
    confidence: float = 0.95,
) -> dict[str, object]:
    """Calcula proporção e intervalo de Wilson usando apenas valores válidos.

    O indicador deve representar o desfecho com ``True``/``False`` e pode conter
    ausências. Nenhuma ausência é convertida para ``False``.
    """
    if not 0 < confidence < 1:
        raise ValueError("confidence deve estar entre 0 e 1.")

    valid = indicator.astype("boolean").dropna()
    n_valid = int(valid.size)
    if n_valid == 0:
        raise ValueError("A proporção requer pelo menos um valor válido.")

    successes = int(valid.sum())
    lower, upper = proportion_confint(
        successes,
        n_valid,
        alpha=1 - confidence,
        method="wilson",
    )
    return {
        "n_valido": n_valid,
        "n_ausente": int(len(indicator) - n_valid),
        "n": successes,
        "proporcao": successes / n_valid,
        "percentual": 100 * successes / n_valid,
        "ic95_inferior": 100 * float(lower),
        "ic95_superior": 100 * float(upper),
        "metodo_ic": "Wilson",
    }

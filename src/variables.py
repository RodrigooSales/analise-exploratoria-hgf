"""Classificações clínicas e indicadores derivados de IMC e FINDRISC."""

from __future__ import annotations

import pandas as pd

from src.cleaning import clean_numeric_column, clean_text_column

AUTOIMMUNE_DIAGNOSES = frozenset(
    {
        "Arterite temporal",
        "Artrite reumatoide",
        "Espondiloartrite",
        "Lúpus eritematoso",
        "Síndrome antifosfolipídica (SAF)",
    }
)


def extract_findrisc_score(series: pd.Series) -> pd.Series:
    """Extrai a pontuação inteira no início de um campo FINDRISC textual.

    Texto entre parênteses é ignorado. Ausências, conteúdo sem pontuação inicial
    e valores não inteiros permanecem ausentes.
    """
    extracted = (
        series.astype("string")
        .str.extract(r"^\s*([+-]?\d+(?:[.,]\d+)?)", expand=False)
    )
    numeric = clean_numeric_column(extracted)
    non_integer = numeric.notna() & numeric.mod(1).ne(0)
    return numeric.mask(non_integer, pd.NA).astype("Int64").rename("findrisc_score")


def classificar_imc(imc: float | None) -> object:
    """Classifica um valor de IMC conforme os limites clínicos do projeto."""
    if pd.isna(imc):
        return pd.NA
    if imc < 18.5:
        return "Baixo peso"
    if imc < 25:
        return "Peso normal"
    if imc < 30:
        return "Sobrepeso"
    if imc < 35:
        return "Obesidade grau I"
    if imc < 40:
        return "Obesidade grau II"
    return "Obesidade grau III"


def classificar_findrisc(score: float | None) -> object:
    """Classifica uma pontuação FINDRISC usando somente o escore numérico."""
    if pd.isna(score):
        return pd.NA
    if score < 7:
        return "Baixo risco"
    if score <= 11:
        return "Leve/moderado"
    if score <= 14:
        return "Moderado"
    if score <= 20:
        return "Alto"
    return "Muito alto"


def _create_threshold_indicator(
    series: pd.Series,
    threshold: float,
    name: str,
) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    indicator = pd.Series(pd.NA, index=series.index, name=name, dtype="boolean")
    valid = numeric.notna()
    indicator.loc[valid] = numeric.loc[valid].ge(threshold)
    return indicator


def create_excesso_peso(imc: pd.Series) -> pd.Series:
    """Cria indicador anulável de excesso de peso, definido por IMC ≥ 25."""
    return _create_threshold_indicator(imc, threshold=25, name="excesso_peso")


def create_obesidade(imc: pd.Series) -> pd.Series:
    """Cria indicador anulável de obesidade, definido por IMC ≥ 30."""
    return _create_threshold_indicator(imc, threshold=30, name="obesidade")


def create_findrisc_alto(findrisc_score: pd.Series) -> pd.Series:
    """Cria indicador anulável de FINDRISC elevado, definido por escore ≥ 15."""
    return _create_threshold_indicator(findrisc_score, threshold=15, name="findrisc_alto")


def create_atividade_fisica_atual(series: pd.Series) -> pd.Series:
    """Classifica relato textual em atividade física atual, preservando ausências.

    ``Não``, ``Atualmente não`` e relatos iniciados por ``Parou`` representam
    ausência atual. Demais relatos válidos descrevem atividade atual.
    """
    cleaned = clean_text_column(series)
    normalized = cleaned.str.casefold()
    inactive = (
        normalized.eq("não")
        | normalized.str.startswith("atualmente não", na=False)
        | normalized.str.startswith("parou", na=False)
    )
    result = pd.Series(pd.NA, index=series.index, dtype="boolean", name="atividade_fisica_atual")
    valid = cleaned.notna()
    result.loc[valid] = ~inactive.loc[valid]
    return result


def count_autoimmune_diagnoses(series: pd.Series) -> pd.Series:
    """Conta diagnósticos autoimunes explícitos em um campo padronizado.

    Os componentes são separados por vírgula e comparados exatamente com
    ``AUTOIMMUNE_DIAGNOSES``. Termos ausentes permanecem ausentes; diagnósticos
    incertos não são inferidos como autoimunes.
    """
    cleaned = clean_text_column(series)
    result = pd.Series(pd.NA, index=series.index, dtype="Int64", name="n_diagnosticos_autoimunes")
    valid = cleaned.notna()
    result.loc[valid] = cleaned.loc[valid].str.split(",").map(
        lambda diagnoses: sum(
            diagnosis.strip() in AUTOIMMUNE_DIAGNOSES for diagnosis in diagnoses
        )
    )
    return result

"""Funções reutilizáveis para limpeza e anonimização do banco clínico."""

from __future__ import annotations

import numpy as np
import pandas as pd


def clean_text_column(series: pd.Series) -> pd.Series:
    """Limpa espaços de uma coluna textual sem substituir ausências.

    Espaços nas extremidades e sequências internas de espaços são removidos.
    Strings vazias após a limpeza são convertidas para ``pd.NA``.
    """
    cleaned = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return cleaned.mask(cleaned.eq(""), pd.NA)


def clean_numeric_column(series: pd.Series) -> pd.Series:
    """Converte uma coluna para número, aceitando vírgula ou ponto decimal.

    Ausências e valores não conversíveis permanecem ausentes. Formatos ambíguos,
    como números com separadores de milhar e decimal simultâneos, não são
    interpretados automaticamente.
    """
    cleaned = clean_text_column(series).str.replace(",", ".", regex=False)
    numeric = pd.to_numeric(cleaned, errors="coerce")
    return numeric.mask(numeric.isin([np.inf, -np.inf]), pd.NA)


def identify_empty_records(
    frame: pd.DataFrame,
    patient_column: str | None = "nome",
) -> pd.Series:
    """Identifica registros vazios sem modificar o DataFrame.

    Quando ``patient_column`` é informado, um registro é vazio se essa coluna
    estiver ausente ou contiver apenas espaços. Com ``None``, todas as colunas
    são avaliadas e somente linhas sem qualquer valor são marcadas.
    """
    if patient_column is not None:
        if patient_column not in frame.columns:
            raise KeyError(f"Coluna de paciente ausente: {patient_column}")
        empty = clean_text_column(frame[patient_column]).isna()
    else:
        has_value = frame.apply(lambda series: clean_text_column(series).notna()).any(axis=1)
        empty = ~has_value

    empty.name = "is_empty_record"
    return empty


def remove_empty_records(
    frame: pd.DataFrame,
    patient_column: str | None = "nome",
) -> pd.DataFrame:
    """Retorna uma cópia do DataFrame sem registros identificados como vazios."""
    empty_records = identify_empty_records(frame, patient_column=patient_column)
    return frame.loc[~empty_records].copy()


def create_patient_id(
    frame: pd.DataFrame,
    prefix: str = "P",
    width: int = 3,
    column_name: str = "patient_id",
) -> pd.Series:
    """Cria identificadores sequenciais anônimos preservando o índice original."""
    if width < 1:
        raise ValueError("A largura do identificador deve ser positiva.")

    effective_width = max(width, len(str(len(frame))))
    identifiers = [f"{prefix}{number:0{effective_width}d}" for number in range(1, len(frame) + 1)]
    return pd.Series(identifiers, index=frame.index, name=column_name, dtype="string")


def anonymize_patients(
    frame: pd.DataFrame,
    name_column: str = "nome",
    id_column: str = "patient_id",
    prefix: str = "P",
    width: int = 3,
) -> pd.DataFrame:
    """Substitui a coluna nominal por identificadores internos em uma cópia.

    A função não remove registros vazios. Essa etapa deve ocorrer antes, por meio
    de :func:`remove_empty_records`, para que somente pacientes válidos recebam ID.
    """
    if name_column not in frame.columns:
        raise KeyError(f"Coluna nominal ausente: {name_column}")
    if id_column == name_column:
        raise ValueError("A coluna de identificação interna deve diferir da coluna nominal.")
    if id_column in frame.columns and id_column != name_column:
        raise ValueError(f"A coluna de identificador já existe: {id_column}")

    anonymized = frame.drop(columns=[name_column]).copy()
    patient_id = create_patient_id(
        anonymized,
        prefix=prefix,
        width=width,
        column_name=id_column,
    )
    anonymized.insert(0, id_column, patient_id)
    return anonymized

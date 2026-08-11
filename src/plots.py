"""Funções reutilizáveis para visualizações científicas do projeto."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MaxNLocator
from scipy import stats


def _valid_numeric(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        raise ValueError("A figura requer pelo menos um valor numérico válido.")
    return numeric


def _annotate_bars(axis, bars, labels: list[str]) -> None:
    for bar, label in zip(bars, labels):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            label,
            ha="center",
            va="bottom",
            fontsize=9,
        )


def plot_imc_distribution(series: pd.Series):
    """Cria histograma do IMC com densidade estimada no eixo de probabilidade."""
    imc = _valid_numeric(series)
    figure, axis = plt.subplots(figsize=(8, 5))
    sns.histplot(imc, bins="auto", stat="density", kde=True, color="#4C78A8", ax=axis)
    axis.set(
        title="Distribuição do índice de massa corporal",
        xlabel="IMC (kg/m²)",
        ylabel="Densidade",
    )
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    return figure, axis


def plot_imc_boxplot(series: pd.Series):
    """Cria boxplot vertical do IMC sem remover valores extremos."""
    imc = _valid_numeric(series)
    figure, axis = plt.subplots(figsize=(6.5, 6))
    axis.boxplot(
        imc.to_numpy(),
        orientation="vertical",
        patch_artist=True,
        boxprops={"facecolor": "#72B7B2"},
    )
    axis.set(
        title="Dispersão e possíveis valores extremos do IMC",
        xlabel="Pacientes com IMC válido",
        ylabel="IMC (kg/m²)",
    )
    axis.set_xticks([])
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    return figure, axis


def plot_qq(series: pd.Series, *, title: str = "Q-Q plot"):
    """Cria Q-Q plot de uma variável numérica contra a distribuição normal."""
    values = _valid_numeric(series)
    figure, axis = plt.subplots(figsize=(6.5, 6))
    stats.probplot(values, dist="norm", plot=axis)
    axis.set(
        title=title,
        xlabel="Quantis teóricos da distribuição normal",
        ylabel="Quantis observados",
    )
    axis.grid(alpha=0.2)
    figure.tight_layout()
    return figure, axis


def plot_imc_categories(series: pd.Series, *, order: list[str]):
    """Cria gráfico de barras das categorias de IMC com ``n`` e percentual válido."""
    categories = series.astype("string").dropna()
    if categories.empty:
        raise ValueError("A figura requer pelo menos uma categoria de IMC válida.")

    counts = categories.value_counts().reindex(order, fill_value=0)
    percentages = 100 * counts / len(categories)
    figure, axis = plt.subplots(figsize=(10, 6))
    bars = axis.bar(counts.index, counts.values, color="#4C78A8")
    axis.set(
        title="Distribuição das categorias de IMC",
        xlabel="Categoria de IMC",
        ylabel="Número de pacientes",
    )
    axis.tick_params(axis="x", rotation=25)
    axis.grid(axis="y", alpha=0.2)

    for bar, count, percentage in zip(bars, counts, percentages):
        label = f"{int(count)} ({percentage:.1f}%)".replace(".", ",")
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            label,
            ha="center",
            va="bottom",
            fontsize=9,
        )

    figure.tight_layout()
    return figure, axis


def plot_findrisc_distribution(series: pd.Series):
    """Cria histograma do FINDRISC com densidade estimada para apoio visual."""
    score = _valid_numeric(series)
    bins = range(int(score.min()), int(score.max()) + 2)
    figure, axis = plt.subplots(figsize=(8, 5))
    sns.histplot(
        score,
        bins=bins,
        stat="density",
        kde=True,
        color="#F58518",
        ax=axis,
    )
    axis.set(
        title="Distribuição do escore FINDRISC",
        xlabel="FINDRISC (pontos)",
        ylabel="Densidade",
    )
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    return figure, axis


def plot_findrisc_boxplot(series: pd.Series):
    """Cria boxplot vertical do FINDRISC sem remover valores extremos."""
    score = _valid_numeric(series)
    figure, axis = plt.subplots(figsize=(6.5, 6))
    axis.boxplot(
        score.to_numpy(),
        orientation="vertical",
        patch_artist=True,
        boxprops={"facecolor": "#ECA82C"},
    )
    axis.set(
        title="Dispersão e possíveis valores extremos do FINDRISC",
        xlabel="Pacientes com FINDRISC válido",
        ylabel="FINDRISC (pontos)",
    )
    axis.set_xticks([])
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    return figure, axis


def plot_findrisc_categories(series: pd.Series, *, order: list[str]):
    """Cria gráfico das categorias FINDRISC com ``n`` e percentual válido."""
    categories = series.astype("string").dropna()
    if categories.empty:
        raise ValueError("A figura requer pelo menos uma categoria FINDRISC válida.")

    counts = categories.value_counts().reindex(order, fill_value=0)
    percentages = 100 * counts / len(categories)
    figure, axis = plt.subplots(figsize=(10, 6))
    bars = axis.bar(counts.index, counts.values, color="#F58518")
    axis.set(
        title="Distribuição das categorias FINDRISC",
        xlabel="Categoria FINDRISC",
        ylabel="Número de pacientes",
    )
    axis.tick_params(axis="x", rotation=20)
    axis.grid(axis="y", alpha=0.2)

    for bar, count, percentage in zip(bars, counts, percentages):
        label = f"{int(count)} ({percentage:.1f}%)".replace(".", ",")
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            label,
            ha="center",
            va="bottom",
            fontsize=9,
        )

    figure.tight_layout()
    return figure, axis


def plot_imc_findrisc(
    imc: pd.Series,
    findrisc: pd.Series,
    *,
    rho: float,
    ic95_inferior: float,
    ic95_superior: float,
):
    """Cria scatter plot IMC × FINDRISC com tendência visual e estatísticas."""
    paired = pd.DataFrame(
        {
            "imc": pd.to_numeric(imc, errors="coerce"),
            "findrisc": pd.to_numeric(findrisc, errors="coerce"),
        }
    ).replace([np.inf, -np.inf], np.nan).dropna()
    if paired.empty:
        raise ValueError("A figura requer pelo menos um par IMC–FINDRISC válido.")

    figure, axis = plt.subplots(figsize=(8, 6))
    sns.regplot(
        data=paired,
        x="imc",
        y="findrisc",
        lowess=True,
        ci=None,
        scatter_kws={"alpha": 0.7, "s": 52, "color": "#4C78A8", "edgecolor": "white"},
        line_kws={"color": "#D1495B", "linewidth": 2, "label": "Tendência LOWESS"},
        ax=axis,
    )
    annotation = (
        f"rho de Spearman = {rho:.2f}\n"
        f"IC95%: {ic95_inferior:.2f} a {ic95_superior:.2f}\n"
        f"N = {len(paired)}"
    ).replace(".", ",")
    axis.text(
        0.03,
        0.97,
        annotation,
        transform=axis.transAxes,
        ha="left",
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9, "edgecolor": "0.8"},
    )
    axis.set(
        title="Associação entre IMC e escore FINDRISC",
        xlabel="IMC (kg/m²)",
        ylabel="FINDRISC (pontos)",
    )
    axis.yaxis.set_major_locator(MaxNLocator(integer=True))
    axis.grid(alpha=0.2)
    axis.legend(frameon=False, loc="lower right")
    figure.tight_layout()
    return figure, axis


def plot_missing_data(summary: pd.DataFrame):
    """Cria gráfico de missing por variável sem exibir campos identificadores."""
    required = {"variavel", "percentual_ausente"}
    if not required.issubset(summary.columns):
        raise ValueError("O resumo deve conter variavel e percentual_ausente.")

    plot_data = summary.loc[:, ["variavel", "percentual_ausente"]].copy()
    protected = {"cod", "nome", "patient_id"}
    variable_keys = plot_data["variavel"].astype("string").str.strip().str.casefold()
    plot_data = plot_data.loc[~variable_keys.isin(protected)].copy()
    plot_data["percentual_ausente"] = pd.to_numeric(
        plot_data["percentual_ausente"], errors="coerce"
    )
    if plot_data.empty or plot_data["percentual_ausente"].isna().any():
        raise ValueError("O gráfico requer percentuais de ausência válidos.")
    if not plot_data["percentual_ausente"].between(0, 100).all():
        raise ValueError("Percentuais de ausência devem estar entre 0 e 100.")

    plot_data = plot_data.sort_values("percentual_ausente", ascending=False)
    height = max(4.5, 0.28 * len(plot_data))
    figure, axis = plt.subplots(figsize=(10, height))
    axis.barh(plot_data["variavel"], plot_data["percentual_ausente"], color="#4C78A8")
    axis.invert_yaxis()
    axis.set(
        title="Percentual de dados ausentes entre pacientes válidos",
        xlabel="Dados ausentes (%)",
        ylabel="Variável",
        xlim=(0, 100),
    )
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    return figure, axis


def plot_metabolic_profile(
    excesso_peso: pd.Series,
    obesidade: pd.Series,
    findrisc_alto: pd.Series,
):
    """Compara prevalências metabólicas usando o denominador válido de cada indicador."""
    indicators = [
        ("Excesso de peso\n(IMC ≥ 25 kg/m²)", excesso_peso),
        ("Obesidade\n(IMC ≥ 30 kg/m²)", obesidade),
        ("FINDRISC elevado\n(≥ 15 pontos)", findrisc_alto),
    ]
    counts = []
    denominators = []
    for label, series in indicators:
        valid = series.astype("boolean").dropna()
        if valid.empty:
            raise ValueError(f"O indicador {label} não possui valores válidos.")
        counts.append(int(valid.sum()))
        denominators.append(int(valid.size))

    percentages = [100 * count / denominator for count, denominator in zip(counts, denominators)]
    figure, axis = plt.subplots(figsize=(9, 6))
    bars = axis.bar(
        [label for label, _ in indicators],
        percentages,
        color=["#4C78A8", "#E45756", "#F58518"],
    )
    axis.set(
        title="Perfil geral de risco metabólico",
        xlabel="Indicador metabólico",
        ylabel="Prevalência (%)",
        ylim=(0, 105),
    )
    axis.grid(axis="y", alpha=0.2)
    labels = [
        f"{count}/{denominator} ({percentage:.1f}%)".replace(".", ",")
        for count, denominator, percentage in zip(counts, denominators, percentages)
    ]
    _annotate_bars(axis, bars, labels)
    figure.tight_layout()
    return figure, axis


def plot_selection_flow(counts: pd.Series):
    """Cria gráfico do fluxo agregado de seleção e limpeza de registros."""
    values = _valid_numeric(counts)
    figure, axis = plt.subplots(figsize=(7, 4))
    colors = sns.color_palette("Blues", n_colors=len(values) + 2)[2:]
    bars = axis.bar(values.index.astype(str), values.to_numpy(), color=colors)
    axis.set(
        title="Fluxo de seleção e limpeza",
        xlabel="Etapa",
        ylabel="Número de registros",
    )
    axis.tick_params(axis="x", rotation=0)
    axis.yaxis.set_major_locator(MaxNLocator(integer=True))
    axis.grid(axis="y", alpha=0.2)
    _annotate_bars(axis, bars, [str(int(value)) for value in values])
    figure.tight_layout()
    return figure, axis


def plot_variable_availability(availability: pd.Series):
    """Cria gráfico horizontal da disponibilidade percentual de variáveis."""
    values = _valid_numeric(availability).sort_values()
    if not values.between(0, 100).all():
        raise ValueError("Percentuais de disponibilidade devem estar entre 0 e 100.")

    figure, axis = plt.subplots(figsize=(9, 6))
    axis.barh(values.index.astype(str), values.to_numpy(), color="#4C78A8")
    axis.set(
        title="Disponibilidade das variáveis de caracterização",
        xlabel="Observações válidas (%)",
        ylabel="Variável",
        xlim=(0, 100),
    )
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    return figure, axis


def save_figure(figure, path: str | Path, *, dpi: int = 300) -> None:
    """Exporta uma figura em alta resolução, criando o diretório de destino."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight")

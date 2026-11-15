import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from .analysis import format_itemset

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "sequential_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)

DIVERGING = LinearSegmentedColormap.from_list(
    "diverging_red_blue", ["#b3312f", "#e34948", "#f2a5a4", "#f0efec", "#9ec5f4", "#3987e5", "#184f95"]
)


def apply_theme() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.titlecolor": TEXT_PRIMARY,
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
            "text.color": TEXT_PRIMARY,
            "font.size": 10,
            "legend.frameon": False,
            "figure.dpi": 110,
        }
    )


def _wrap(label: str, width: int) -> str:
    return "\n".join(textwrap.wrap(label, width=width))


def _hbar(ax: plt.Axes, labels: list[str], values: np.ndarray, color: str, fmt: str) -> None:
    positions = np.arange(len(labels))[::-1]
    ax.barh(positions, values, color=color, height=0.7, edgecolor=SURFACE, linewidth=2)
    ax.set_yticks(positions, labels)
    ax.grid(axis="y", visible=False)
    for y, value in zip(positions, values):
        ax.text(value, y, f" {value:{fmt}}", va="center", fontsize=8.5, color=TEXT_SECONDARY)
    ax.margins(x=0.12)


def plot_item_support(support: pd.Series, top_n: int = 20) -> Figure:
    data = support.head(top_n)
    fig, ax = plt.subplots(figsize=(9, 0.32 * len(data) + 1.2))
    _hbar(ax, list(data.index), data.to_numpy(), SERIES[0], ".1%")
    ax.set_title(f"Top {len(data)} items by support")
    ax.set_xlabel("Support")
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    fig.tight_layout()
    return fig


def plot_itemset_lengths(summary: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.bar(summary["length"].astype(str), summary["count"], color=SERIES[0], width=0.6, edgecolor=SURFACE, linewidth=2)
    for x, count in enumerate(summary["count"]):
        ax.text(x, count, f"{count:,}", ha="center", va="bottom", fontsize=9, color=TEXT_SECONDARY)
    ax.set_title("Frequent itemsets by length")
    ax.set_xlabel("Itemset length")
    ax.set_ylabel("Count")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


def plot_churn_rate_by_feature(rates: pd.DataFrame, baseline: float, ncols: int = 3) -> Figure:
    features = rates["feature"].unique()
    nrows = int(np.ceil(len(features) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 2.8 * nrows), squeeze=False)
    for ax, feature in zip(axes.flat, features):
        subset = rates[rates["feature"] == feature].sort_values("churn_rate")
        colors = [SERIES[1] if rate > baseline else SERIES[0] for rate in subset["churn_rate"]]
        ax.barh([_wrap(str(v), 18) for v in subset["value"]], subset["churn_rate"], color=colors, height=0.65)
        ax.axvline(baseline, color=TEXT_SECONDARY, linewidth=1, linestyle="--")
        ax.set_title(feature, fontsize=11)
        ax.set_xlim(0, min(1.0, rates["churn_rate"].max() * 1.15))
        ax.xaxis.set_major_formatter(PercentFormatter(1.0))
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", labelsize=8.5)
    for ax in axes.flat[len(features):]:
        ax.set_visible(False)
    fig.suptitle(
        f"Churn rate by feature (dashed line = overall {baseline:.1%}; orange = above overall)",
        x=0.01, ha="left", fontsize=12, color=TEXT_PRIMARY,
    )
    fig.tight_layout()
    return fig


def plot_rules_scatter(rules: pd.DataFrame, title: str = "Association rules: support vs confidence") -> Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    order = rules.sort_values("lift")
    points = ax.scatter(
        order["support"], order["confidence"], c=order["lift"], cmap=SEQUENTIAL,
        s=18 + 10 * order["antecedent_len"], alpha=0.85, edgecolors=SURFACE, linewidths=0.6,
    )
    colorbar = fig.colorbar(points, ax=ax, pad=0.02)
    colorbar.set_label("Lift")
    colorbar.outline.set_visible(False)
    ax.set_title(title)
    ax.set_xlabel("Support")
    ax.set_ylabel("Confidence")
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    fig.tight_layout()
    return fig


def plot_top_rules(rules: pd.DataFrame, metric: str = "lift", top_n: int = 15, title: str | None = None,
                   color: str = SERIES[0], show_consequent: bool = True) -> Figure:
    data = rules.nlargest(top_n, metric)
    labels = [
        _wrap(format_itemset(a) + (f"  →  {format_itemset(c)}" if show_consequent else ""), 70)
        for a, c in zip(data["antecedents"], data["consequents"])
    ]
    fig, ax = plt.subplots(figsize=(11, 0.5 * len(data) + 1.3))
    _hbar(ax, labels, data[metric].to_numpy(), color, ".2f")
    ax.set_title(title or f"Top {len(data)} rules by {metric}")
    ax.set_xlabel(metric.capitalize())
    ax.tick_params(axis="y", labelsize=8.5)
    fig.tight_layout()
    return fig


def plot_rule_network(rules: pd.DataFrame, top_n: int = 30, title: str = "Item association network") -> Figure:
    data = rules[rules["consequents"].map(len) == 1].nlargest(top_n, "lift")
    graph = nx.DiGraph()
    for row in data.itertuples():
        (target,) = row.consequents
        for source in row.antecedents:
            weight = max(row.lift, graph.edges[source, target]["lift"] if graph.has_edge(source, target) else 0)
            graph.add_edge(source, target, lift=weight)

    degree = dict(graph.in_degree())
    inner = sorted(node for node in graph.nodes if degree[node])
    outer = sorted(node for node in graph.nodes if not degree[node])
    layout = {node: position * (0.45 if degree[node] and len(inner) > 1 else 1.0)
              for node, position in nx.shell_layout(graph, nlist=[inner, outer]).items()}
    lifts = np.array([graph.edges[edge]["lift"] for edge in graph.edges])
    sizes = [220 + 160 * degree[node] for node in graph.nodes]
    colors = [SERIES[1] if degree[node] else SERIES[0] for node in graph.nodes]

    fig, ax = plt.subplots(figsize=(13, 10))
    nx.draw_networkx_edges(
        graph, layout, ax=ax, edge_color=lifts, edge_cmap=SEQUENTIAL, width=1.8, arrows=True,
        arrowsize=12, node_size=sizes, connectionstyle="arc3,rad=0.08",
    )
    nx.draw_networkx_nodes(graph, layout, node_size=sizes, node_color=colors, ax=ax, edgecolors=SURFACE, linewidths=2)
    for node, (x, y) in layout.items():
        push = 1.0 if degree[node] else 1.12
        ax.text(x * push, y * push + (0.06 if degree[node] else 0.0), _wrap(node, 24), ha="center", va="center",
                fontsize=8.5, color=TEXT_PRIMARY,
                bbox={"boxstyle": "round,pad=0.15", "facecolor": SURFACE, "edgecolor": "none", "alpha": 0.85})
    mappable = plt.cm.ScalarMappable(cmap=SEQUENTIAL, norm=plt.Normalize(lifts.min(), lifts.max()))
    colorbar = fig.colorbar(mappable, ax=ax, shrink=0.6, pad=0.01)
    colorbar.set_label("Edge lift")
    colorbar.outline.set_visible(False)
    ax.set_title(f"{title} (top {len(data)} rules by lift; orange = consequent, blue = antecedent only)")
    ax.axis("off")
    ax.margins(0.08)
    fig.tight_layout()
    return fig


def plot_lift_matrix(lift: pd.DataFrame, title: str = "Pairwise lift between items") -> Figure:
    values = lift.to_numpy()
    spread = max(np.nanmax(values) - 1, 1 - np.nanmin(values), 0.1)
    fig, ax = plt.subplots(figsize=(11, 9.5))
    image = ax.imshow(values, cmap=DIVERGING, norm=TwoSlopeNorm(vmin=1 - min(spread, 1), vcenter=1, vmax=1 + spread))
    ax.set_xticks(range(len(lift.columns)), lift.columns, rotation=50, ha="right", fontsize=8.5)
    ax.set_yticks(range(len(lift.index)), lift.index, fontsize=8.5)
    ax.grid(False)
    for (row, col), value in np.ndenumerate(values):
        if not np.isnan(value):
            ax.text(col, row, f"{value:.2f}", ha="center", va="center", fontsize=7,
                    color=SURFACE if abs(value - 1) > spread * 0.55 else TEXT_PRIMARY)
    colorbar = fig.colorbar(image, ax=ax, pad=0.02, shrink=0.8)
    colorbar.set_label("Lift (1 = independent; blue = co-occur more, red = less)")
    colorbar.outline.set_visible(False)
    ax.set_title(f"{title} (blank = same attribute)")
    fig.tight_layout()
    return fig


def plot_support_sensitivity(sensitivity: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for column, color in zip(("itemsets", "rules"), SERIES):
        ax.plot(sensitivity["min_support"], sensitivity[column], color=color, linewidth=2, marker="o",
                markersize=6, markeredgecolor=SURFACE, label=column.capitalize())
        last = sensitivity.iloc[0]
        ax.annotate(column.capitalize(), (last["min_support"], last[column]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=9, color=TEXT_SECONDARY)
    ax.set_yscale("log")
    ax.set_title("Pattern count vs minimum support")
    ax.set_xlabel("Minimum support")
    ax.set_ylabel("Count (log scale)")
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def save_figure(fig: Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path

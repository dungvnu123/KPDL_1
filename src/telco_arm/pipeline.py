from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import analysis, visualization
from .apriori import apriori
from .config import Settings, TargetParams
from .data_loader import load_dataset
from .preprocessing import build_transactions, discretize, one_hot_encode, usage_items
from .rules import generate_rules, mine_target_rules

PROFILE_COLUMNS = (
    "Contract",
    "InternetService",
    "PaymentMethod",
    "TechSupport",
    "OnlineSecurity",
    "PaperlessBilling",
    "SeniorCitizen",
    "Dependents",
    "TenureGroup",
)

SERVICE_ITEMS = (
    "PhoneService=Yes",
    "MultipleLines=Yes",
    "InternetService=DSL",
    "InternetService=Fiber optic",
    "OnlineSecurity=Yes",
    "OnlineBackup=Yes",
    "DeviceProtection=Yes",
    "TechSupport=Yes",
    "StreamingTV=Yes",
    "StreamingMovies=Yes",
    "Contract=Month-to-month",
    "Contract=One year",
    "Contract=Two year",
    "PaperlessBilling=Yes",
    "PaymentMethod=Electronic check",
    "Churn=Yes",
)


@dataclass
class PipelineResult:
    customers: pd.DataFrame
    transactions: list[frozenset[str]]
    onehot: pd.DataFrame
    itemsets: pd.DataFrame
    service_rules: pd.DataFrame
    churn_rules: pd.DataFrame
    retention_rules: pd.DataFrame

    @property
    def churn_rate(self) -> float:
        return float((self.customers["Churn"] == "Yes").mean())


def _mine_target(onehot: pd.DataFrame, params: TargetParams, settings: Settings) -> pd.DataFrame:
    return mine_target_rules(
        onehot,
        target=params.target,
        min_support=params.min_support,
        min_confidence=params.min_confidence,
        min_lift=params.min_lift,
        max_len=params.max_len,
        exclude=tuple(item for item in settings.target_items if item != params.target),
        min_improvement=params.min_improvement,
    )


def run(settings: Settings | None = None) -> PipelineResult:
    settings = settings or Settings()
    customers = load_dataset(settings.paths.raw_data, settings.features)
    transactions = build_transactions(customers, settings.features)
    onehot = one_hot_encode(transactions)

    behavior = usage_items(onehot, settings.features, exclude=settings.target_items)
    itemsets = apriori(behavior, settings.mining.min_support, settings.mining.max_len)
    service_rules = generate_rules(itemsets, settings.mining.min_confidence, settings.mining.min_lift)

    return PipelineResult(
        customers=customers.assign(TenureGroup=discretize(customers, settings.features)["TenureGroup"]),
        transactions=transactions,
        onehot=onehot,
        itemsets=itemsets,
        service_rules=service_rules,
        churn_rules=_mine_target(onehot, settings.churn, settings),
        retention_rules=_mine_target(onehot, settings.retention, settings),
    )


def export_tables(result: PipelineResult, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    tables = {
        "item_support.csv": analysis.item_support(result.onehot).rename_axis("item").reset_index(),
        "frequent_itemsets.csv": analysis.readable_itemsets(result.itemsets),
        "service_rules.csv": analysis.readable_rules(result.service_rules),
        "churn_rules.csv": analysis.readable_rules(result.churn_rules),
        "retention_rules.csv": analysis.readable_rules(result.retention_rules),
        "churn_rule_coverage.csv": analysis.rule_coverage(result.churn_rules, result.onehot, "Churn=Yes"),
        "churn_rate_by_feature.csv": analysis.churn_rate_by(result.customers, PROFILE_COLUMNS),
    }
    paths = []
    for name, table in tables.items():
        path = directory / name
        table.to_csv(path, index=False, encoding="utf-8-sig")
        paths.append(path)
    return paths


def export_figures(result: PipelineResult, directory: Path) -> list[Path]:
    visualization.apply_theme()
    figures = {
        "01_item_support.png": visualization.plot_item_support(analysis.item_support(result.onehot)),
        "02_itemset_lengths.png": visualization.plot_itemset_lengths(analysis.itemset_length_summary(result.itemsets)),
        "03_churn_rate_by_feature.png": visualization.plot_churn_rate_by_feature(
            analysis.churn_rate_by(result.customers, PROFILE_COLUMNS), result.churn_rate
        ),
        "04_service_rules_scatter.png": visualization.plot_rules_scatter(result.service_rules),
        "05_service_lift_matrix.png": visualization.plot_lift_matrix(
            analysis.pairwise_lift(result.onehot, SERVICE_ITEMS), title="Service co-usage lift"
        ),
        "06_service_rule_network.png": visualization.plot_rule_network(
            result.service_rules[result.service_rules["antecedent_len"] <= 2], title="Service usage network"
        ),
        "07_churn_top_rules.png": visualization.plot_top_rules(
            result.churn_rules, title="Top churn rules by lift (→ Churn=Yes)",
            color=visualization.SERIES[1], show_consequent=False,
        ),
        "08_churn_rules_scatter.png": visualization.plot_rules_scatter(
            result.churn_rules, title="Churn rules: support vs confidence"
        ),
        "09_churn_rule_network.png": visualization.plot_rule_network(
            result.churn_rules[result.churn_rules["antecedent_len"] <= 2], title="Churn driver network"
        ),
        "10_retention_top_rules.png": visualization.plot_top_rules(
            result.retention_rules, title="Top retention rules by lift (→ Churn=No)", show_consequent=False,
        ),
    }
    return [visualization.save_figure(fig, directory / name) for name, fig in figures.items()]

"""Count-based answers to the six business questions (rates are on the cleaned data)."""

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

from .analysis import format_itemset, format_rule, readable_rules
from .apriori import apriori
from .config import Settings
from .preprocessing import usage_items


@dataclass
class QuestionAnswers:
    bundles: pd.DataFrame
    probabilities: pd.DataFrame
    churn: pd.DataFrame
    retention: pd.DataFrame
    demographics: pd.DataFrame
    upgrade_rules: pd.DataFrame
    recommendations: pd.DataFrame

    def tables(self) -> dict[str, pd.DataFrame]:
        return {
            "q1_service_bundles.csv": self.bundles,
            "q2_service_probabilities.csv": self.probabilities,
            "q3_churn_patterns.csv": self.churn,
            "q4_retention_patterns.csv": self.retention,
            "q5_demographic_bundles.csv": self.demographics,
            "q6_upgrade_rules.csv": self.upgrade_rules,
            "q6_customer_recommendations.csv": self.recommendations,
        }


def _count(onehot: pd.DataFrame, items: frozenset[str]) -> int:
    return int(onehot[sorted(items)].all(axis=1).sum())


def service_bundles(itemsets: pd.DataFrame, onehot: pd.DataFrame) -> pd.DataFrame:
    table = itemsets.loc[itemsets["length"] >= 2].copy()
    table["customers"] = [_count(onehot, items) for items in table["itemsets"]]
    table["itemsets"] = table["itemsets"].map(format_itemset)
    return table.sort_values(
        ["support", "length", "itemsets"], ascending=[False, True, True], ignore_index=True
    )[["itemsets", "length", "customers", "support"]]


def service_probabilities(services: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    columns = ["service_a", "service_b", "a_customers", "b_customers", "both_customers",
               "support", "confidence", "baseline_b", "lift", "is_prerequisite", "passes_thresholds"]
    rows = []
    n = len(services)
    if not n:
        return pd.DataFrame(columns=columns)
    counts = services.sum()
    for a in services:
        if not counts[a]:
            continue
        for b in services:
            if a.split("=", 1)[0] == b.split("=", 1)[0] or not counts[b]:
                continue
            both = int((services[a] & services[b]).sum())
            support, confidence, baseline = both / n, both / counts[a], counts[b] / n
            lift = confidence / baseline
            prerequisite = a == "MultipleLines=Yes" and b == "PhoneService=Yes"
            passes = (support >= settings.mining.min_support and confidence >= settings.mining.min_confidence
                      and lift >= settings.mining.min_lift)
            rows.append((a, b, int(counts[a]), int(counts[b]), both, support, confidence,
                         baseline, lift, prerequisite, passes))
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["lift", "confidence", "service_a", "service_b"], ascending=[False, False, True, True], ignore_index=True
    )


def counted_rules(rules: pd.DataFrame, onehot: pd.DataFrame) -> pd.DataFrame:
    """Retain exact rates and denominators; rounding is only for display."""
    table = readable_rules(rules, decimals=12)
    table["matched_customers"] = [_count(onehot, a) for a in rules["antecedents"]]
    table["target_customers"] = [_count(onehot, a | c)
                                 for a, c in zip(rules["antecedents"], rules["consequents"])]
    return table


def demographic_bundles(onehot: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    """Demographic antecedents only; positive service bundles only on the right."""
    columns = ["demographics", "bundle", "demographic_len", "bundle_len", "group_customers",
               "bundle_customers", "support", "confidence", "baseline_bundle", "lift"]
    params = settings.questions
    if onehot.empty:
        return pd.DataFrame(columns=columns)
    services = usage_items(onehot, settings.features)
    candidates = apriori(services, params.demographic_support, params.max_bundle_len)
    # Basic phone access is reported in Q1. Here focus on differentiated bundles.
    bundles = [items for items in candidates["itemsets"]
               if len(items) >= 2 and "PhoneService=Yes" not in items]
    service_masks = {b: onehot[sorted(b)].all(axis=1).to_numpy() for b in bundles}
    demo_items = [item for item in onehot if item.split("=", 1)[0] in settings.features.demographic_columns]
    rows = []
    n = len(onehot)
    for size in range(1, params.max_demographic_len + 1):
        for group in combinations(demo_items, size):
            if len({item.split("=", 1)[0] for item in group}) != size:
                continue
            matched = onehot[list(group)].all(axis=1).to_numpy()
            group_count = int(matched.sum())
            if group_count < params.min_group_customers or not group_count:
                continue
            for bundle, bundle_mask in service_masks.items():
                joint = int((matched & bundle_mask).sum())
                support, confidence = joint / n, joint / group_count
                if support < params.demographic_support or confidence < params.demographic_confidence:
                    continue
                baseline = float(bundle_mask.mean())
                rows.append((format_itemset(group), format_itemset(bundle), size, len(bundle), group_count,
                             joint, support, confidence, baseline, confidence / baseline))
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["demographics", "confidence", "lift", "bundle"], ascending=[True, False, False, True], ignore_index=True
    )


def recommend_upgrades(
    service_rules: pd.DataFrame, onehot: pd.DataFrame, customers: pd.DataFrame, settings: Settings,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply service rules to retained records; never use outcome/profile items as predictors."""
    rule_columns = ["rule_id", "rule", "antecedents", "consequents", "antecedent_len", "support",
                    "confidence", "lift", "leverage", "conviction", "matched_customers",
                    "target_customers", "eligible_customers", "selected_customers"]
    rec_columns = [settings.features.id_column, "rank", "recommended_service", "matched_services", "rule_id",
                   "rule", "support", "confidence", "lift"]
    addons = {f"{column}=Yes" for column in settings.features.addon_columns}
    services = set(usage_items(onehot, settings.features).columns)
    candidates = service_rules.loc[
        service_rules["antecedents"].map(lambda a: bool(a) and a <= services)
        & service_rules["consequents"].map(lambda c: len(c) == 1 and c <= addons)
    ].copy()
    # Deterministic tie breaking makes the exported customer list reproducible.
    candidates["_key"] = [format_rule(a, c) for a, c in zip(candidates["antecedents"], candidates["consequents"])]
    candidates = candidates.sort_values(
        ["lift", "confidence", "support", "antecedent_len", "_key"],
        ascending=[False, False, False, True, True], ignore_index=True,
    ).drop(columns="_key")
    rule_table = counted_rules(candidates, onehot)
    rule_table.insert(0, "rule_id", [f"UP{i + 1:04d}" for i in range(len(rule_table))])
    rule_table["eligible_customers"] = 0
    rule_table["selected_customers"] = 0
    # Churn=No identifies the retained cohort for this retrospective example only.
    active = customers[settings.features.target_column].eq("No").to_numpy()
    selected: list[set[str]] = [set() for _ in range(len(customers))]
    rows = []
    for i, row in enumerate(candidates.itertuples()):
        (target,) = row.consequents
        matched = onehot[sorted(row.antecedents)].all(axis=1).to_numpy()
        missing = ~onehot[target].to_numpy()
        column = target.split("=", 1)[0]
        if column == "MultipleLines":
            prerequisite = customers["PhoneService"].eq("Yes").to_numpy()
        else:
            prerequisite = customers["InternetService"].isin(["DSL", "Fiber optic"]).to_numpy()
        eligible = np.flatnonzero(active & matched & missing & prerequisite)
        rule_table.loc[i, "eligible_customers"] = len(eligible)
        for index in eligible:
            if target in selected[index] or len(selected[index]) >= settings.questions.recommendations_per_customer:
                continue
            selected[index].add(target)
            rule_table.loc[i, "selected_customers"] += 1
            rows.append((customers.iloc[index][settings.features.id_column], len(selected[index]), target,
                         format_itemset(row.antecedents), rule_table.loc[i, "rule_id"],
                         rule_table.loc[i, "rule"], row.support, row.confidence, row.lift))
    recommendations = pd.DataFrame(rows, columns=rec_columns).sort_values(
        [settings.features.id_column, "rank"], ignore_index=True
    )
    return rule_table[rule_columns], recommendations


def answer_questions(
    customers: pd.DataFrame, onehot: pd.DataFrame, itemsets: pd.DataFrame,
    service_rules: pd.DataFrame, churn_rules: pd.DataFrame, retention_rules: pd.DataFrame, settings: Settings,
) -> QuestionAnswers:
    upgrades, recommendations = recommend_upgrades(service_rules, onehot, customers, settings)
    return QuestionAnswers(
        bundles=service_bundles(itemsets, onehot),
        probabilities=service_probabilities(usage_items(onehot, settings.features), settings),
        churn=counted_rules(churn_rules, onehot),
        retention=counted_rules(retention_rules, onehot),
        demographics=demographic_bundles(onehot, settings),
        upgrade_rules=upgrades,
        recommendations=recommendations,
    )

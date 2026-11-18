import time
from collections.abc import Iterable

import numpy as np
import pandas as pd

from .apriori import apriori
from .rules import generate_rules

METRIC_COLUMNS = ["support", "confidence", "lift", "leverage", "conviction"]


def format_itemset(items: Iterable[str]) -> str:
    return ", ".join(sorted(items))


def format_rule(antecedents: Iterable[str], consequents: Iterable[str]) -> str:
    return f"{{{format_itemset(antecedents)}}} → {{{format_itemset(consequents)}}}"


def readable_itemsets(itemsets: pd.DataFrame) -> pd.DataFrame:
    return itemsets.assign(itemsets=itemsets["itemsets"].map(format_itemset)).round({"support": 4})


def readable_rules(rules: pd.DataFrame, decimals: int = 4) -> pd.DataFrame:
    rules = rules.reset_index(drop=True)
    table = pd.DataFrame(
        {
            "rule": [format_rule(a, c) for a, c in zip(rules["antecedents"], rules["consequents"])],
            "antecedents": rules["antecedents"].map(format_itemset),
            "consequents": rules["consequents"].map(format_itemset),
            "antecedent_len": rules["antecedent_len"],
        }
    )
    return pd.concat([table, rules[METRIC_COLUMNS].round(decimals)], axis=1)


def item_support(onehot: pd.DataFrame) -> pd.Series:
    return onehot.mean().sort_values(ascending=False).rename("support")


def itemset_length_summary(itemsets: pd.DataFrame) -> pd.DataFrame:
    return (
        itemsets.groupby("length")["support"]
        .agg(count="size", max_support="max", mean_support="mean")
        .round(4)
        .reset_index()
    )


def churn_rate_by(df: pd.DataFrame, columns: Iterable[str], target: str = "Churn", positive: str = "Yes") -> pd.DataFrame:
    frames = [
        df.groupby(column, observed=True)[target]
        .agg(customers="size", churn_rate=lambda s: (s == positive).mean())
        .reset_index()
        .rename(columns={column: "value"})
        .assign(feature=column)
        for column in columns
    ]
    return pd.concat(frames, ignore_index=True)[["feature", "value", "customers", "churn_rate"]]


def rule_coverage(rules: pd.DataFrame, onehot: pd.DataFrame, target: str, top_n: int = 10) -> pd.DataFrame:
    columns = ["rule", "customers", "target_hits", "target_rate", "cumulative_recall"]
    if rules.empty or target not in onehot:
        return pd.DataFrame(columns=columns)
    target_mask = onehot[target].to_numpy(dtype=bool)
    covered = pd.Series(False, index=onehot.index)
    rows = []
    for antecedents, consequents in zip(rules["antecedents"].head(top_n), rules["consequents"].head(top_n)):
        matched = onehot[list(antecedents)].all(axis=1)
        covered |= matched
        rows.append(
            {
                "rule": format_rule(antecedents, consequents),
                "customers": int(matched.sum()),
                "target_hits": int((matched & target_mask).sum()),
                "target_rate": round(float(target_mask[matched].mean()), 4),
                "cumulative_recall": round(float((covered & target_mask).sum() / target_mask.sum()), 4),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def item_frequency_in_rules(rules: pd.DataFrame, side: str = "antecedents") -> pd.Series:
    return rules[side].explode().value_counts().rename("rule_count")


def pairwise_lift(onehot: pd.DataFrame, items: Iterable[str], separator: str = "=") -> pd.DataFrame:
    items = list(items)
    matrix = onehot[items].to_numpy(dtype=float)
    joint = matrix.T @ matrix / len(matrix)
    marginal = matrix.mean(axis=0)
    lift = joint / np.outer(marginal, marginal)
    groups = np.array([item.split(separator, 1)[0] for item in items])
    lift[groups[:, None] == groups[None, :]] = np.nan
    return pd.DataFrame(lift, index=items, columns=items)


def support_sensitivity(onehot: pd.DataFrame, supports: Iterable[float], min_confidence: float,
                        max_len: int | None = None) -> pd.DataFrame:
    rows = []
    for min_support in supports:
        start = time.perf_counter()
        itemsets = apriori(onehot, min_support, max_len)
        rules = generate_rules(itemsets, min_confidence)
        rows.append(
            {
                "min_support": min_support,
                "itemsets": len(itemsets),
                "rules": len(rules),
                "seconds": round(time.perf_counter() - start, 3),
            }
        )
    return pd.DataFrame(rows)

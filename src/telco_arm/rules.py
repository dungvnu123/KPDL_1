from itertools import combinations

import numpy as np
import pandas as pd

from .apriori import apriori

RULE_COLUMNS = [
    "antecedents",
    "consequents",
    "antecedent_support",
    "consequent_support",
    "support",
    "confidence",
    "lift",
    "leverage",
    "conviction",
    "antecedent_len",
]


def _empty_rules() -> pd.DataFrame:
    return pd.DataFrame(columns=RULE_COLUMNS).astype({
        column: "int64" if column == "antecedent_len" else "float64" for column in RULE_COLUMNS[2:]
    })


def _conviction(consequent_support: np.ndarray, confidence: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(confidence >= 1, np.inf, (1 - consequent_support) / (1 - confidence))


def _finalize(records: list[tuple], min_confidence: float, min_lift: float) -> pd.DataFrame:
    rules = pd.DataFrame(records, columns=RULE_COLUMNS[:5])
    if rules.empty:
        return _empty_rules()
    rules["confidence"] = rules["support"] / rules["antecedent_support"]
    rules["lift"] = rules["confidence"] / rules["consequent_support"]
    rules["leverage"] = rules["support"] - rules["antecedent_support"] * rules["consequent_support"]
    rules["conviction"] = _conviction(rules["consequent_support"].to_numpy(), rules["confidence"].to_numpy())
    rules["antecedent_len"] = rules["antecedents"].map(len)
    mask = (rules["confidence"] >= min_confidence) & (rules["lift"] >= min_lift)
    return rules.loc[mask, RULE_COLUMNS].sort_values(["lift", "confidence"], ascending=False, ignore_index=True)


def generate_rules(itemsets: pd.DataFrame, min_confidence: float, min_lift: float = 1.0) -> pd.DataFrame:
    support = dict(zip(itemsets["itemsets"], itemsets["support"]))
    records = [
        (antecedent, itemset - antecedent, support[antecedent], support[itemset - antecedent], itemset_support)
        for itemset, itemset_support in support.items()
        if len(itemset) > 1
        for size in range(1, len(itemset))
        for antecedent in map(frozenset, combinations(sorted(itemset), size))
    ]
    return _finalize(records, min_confidence, min_lift)


def _best_subset_confidence(confidence: dict[frozenset, float]) -> dict[frozenset, float]:
    best: dict[frozenset, float] = {}
    for antecedent in sorted(confidence, key=len):
        best[antecedent] = max(
            (max(confidence.get(antecedent - {item}, 0.0), best.get(antecedent - {item}, 0.0))
             for item in antecedent if len(antecedent) > 1),
            default=0.0,
        )
    return best


def mine_target_rules(
    onehot: pd.DataFrame,
    target: str,
    min_support: float,
    min_confidence: float,
    min_lift: float = 1.0,
    max_len: int | None = None,
    exclude: tuple[str, ...] = (),
    min_improvement: float | None = 0.0,
) -> pd.DataFrame:
    if not 0 < min_support <= 1:
        raise ValueError("min_support must be in (0, 1]")
    if max_len is not None and max_len < 2:
        return _empty_rules()
    if onehot.empty or target not in onehot:
        return _empty_rules()
    target_mask = onehot[target].to_numpy(dtype=bool)
    target_support = target_mask.mean()
    if target_support == 0 or target_support < min_support:
        return _empty_rules()
    features = onehot.drop(columns=[target, *exclude], errors="ignore")
    local_support = min_support / target_support
    local_max_len = None if max_len is None else max_len - 1
    itemsets = apriori(features.loc[target_mask], local_support, local_max_len)

    matrix = features.to_numpy(dtype=bool)
    position = {column: idx for idx, column in enumerate(features.columns)}
    consequent = frozenset([target])
    records = []
    for antecedent, local in zip(itemsets["itemsets"], itemsets["support"]):
        antecedent_support = matrix[:, [position[item] for item in antecedent]].all(axis=1).mean()
        records.append((antecedent, consequent, antecedent_support, target_support, local * target_support))

    if min_improvement is not None and records:
        confidence = {antecedent: joint / ant for antecedent, _, ant, _, joint in records}
        best = _best_subset_confidence(confidence)
        records = [r for r in records if confidence[r[0]] - best[r[0]] > min_improvement]

    return _finalize(records, min_confidence, min_lift)

from itertools import combinations

import numpy as np
import pandas as pd

Itemset = tuple[int, ...]


def _frequent_singletons(matrix: np.ndarray, min_count: int) -> dict[Itemset, np.ndarray]:
    counts = matrix.sum(axis=0)
    return {(idx,): matrix[:, idx] for idx in np.flatnonzero(counts >= min_count)}


def _generate_candidates(previous: dict[Itemset, np.ndarray]) -> list[tuple[Itemset, Itemset, int]]:
    ordered = sorted(previous)
    known = set(ordered)
    candidates = []
    for i, left in enumerate(ordered):
        for right in ordered[i + 1:]:
            if left[:-1] != right[:-1]:
                break
            candidate = left + (right[-1],)
            if all(subset in known for subset in combinations(candidate, len(candidate) - 1)):
                candidates.append((candidate, left, right[-1]))
    return candidates


def _iter_levels(matrix: np.ndarray, min_count: int, max_len: int | None):
    level = _frequent_singletons(matrix, min_count)
    size = 1
    while level:
        yield level
        if max_len is not None and size >= max_len:
            return
        next_level = {}
        for candidate, prefix, last in _generate_candidates(level):
            mask = level[prefix] & matrix[:, last]
            if mask.sum() >= min_count:
                next_level[candidate] = mask
        level = next_level
        size += 1


def apriori(onehot: pd.DataFrame, min_support: float, max_len: int | None = None) -> pd.DataFrame:
    if not 0 < min_support <= 1:
        raise ValueError("min_support must be in (0, 1]")
    if max_len is not None and max_len < 1:
        raise ValueError("max_len must be at least 1")
    if onehot.empty:
        return pd.DataFrame(columns=["support", "itemsets", "length"])
    matrix = onehot.to_numpy(dtype=bool)
    n_transactions = len(matrix)
    min_count = int(np.ceil(np.nextafter(min_support * n_transactions, -np.inf)))
    columns = onehot.columns.to_numpy()
    records = [
        (mask.sum() / n_transactions, frozenset(columns[list(itemset)]), len(itemset))
        for level in _iter_levels(matrix, min_count, max_len)
        for itemset, mask in level.items()
    ]
    itemsets = pd.DataFrame(records, columns=["support", "itemsets", "length"])
    return itemsets.sort_values(["length", "support"], ascending=[True, False], ignore_index=True)

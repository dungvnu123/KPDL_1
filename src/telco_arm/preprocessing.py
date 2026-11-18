import numpy as np
import pandas as pd

from .config import FeatureSpec

ITEM_SEPARATOR = "="


def _item(column: str, value: object) -> str:
    return f"{column}{ITEM_SEPARATOR}{value}"


def discretize(df: pd.DataFrame, spec: FeatureSpec) -> pd.DataFrame:
    binned = pd.DataFrame(index=df.index)
    binned["TenureGroup"] = pd.cut(df["tenure"], bins=spec.tenure_bins, labels=spec.tenure_labels)
    binned["MonthlyCharges"] = pd.qcut(df["MonthlyCharges"], q=len(spec.charge_labels), labels=spec.charge_labels)
    binned["TotalCharges"] = pd.qcut(df["TotalCharges"], q=len(spec.charge_labels), labels=spec.charge_labels)
    return binned.astype(str)


def build_transactions(df: pd.DataFrame, spec: FeatureSpec) -> list[frozenset[str]]:
    categorical = df[[*spec.binary_columns, *spec.categorical_columns, *spec.addon_columns, spec.target_column]]
    frame = pd.concat([categorical, discretize(df, spec)], axis=1)
    skip = set(spec.not_applicable_values)
    return [
        frozenset(_item(column, value) for column, value in row.items() if value not in skip)
        for row in frame.to_dict(orient="records")
    ]


def one_hot_encode(transactions: list[frozenset[str]]) -> pd.DataFrame:
    items = sorted(set().union(*transactions))
    position = {item: idx for idx, item in enumerate(items)}
    values = np.zeros((len(transactions), len(items)), dtype=bool)
    for row, basket in enumerate(transactions):
        values[row, [position[item] for item in basket]] = True
    return pd.DataFrame(values, columns=items)


def usage_items(onehot: pd.DataFrame, spec: FeatureSpec, exclude: tuple[str, ...] = ()) -> pd.DataFrame:
    """Only subscribed services; demographics, billing and outcomes are not services."""
    services = set(service_items(spec))
    keep = [column for column in onehot.columns if column in services and column not in exclude]
    return onehot[keep]


def service_items(spec: FeatureSpec) -> tuple[str, ...]:
    return (
        "PhoneService=Yes", "InternetService=DSL", "InternetService=Fiber optic",
        *(_item(column, "Yes") for column in spec.addon_columns),
    )

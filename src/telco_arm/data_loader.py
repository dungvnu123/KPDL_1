from pathlib import Path

import pandas as pd

from .config import FeatureSpec


def load_raw(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def clean(df: pd.DataFrame, spec: FeatureSpec) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["TotalCharges"] = pd.to_numeric(cleaned["TotalCharges"].str.strip(), errors="coerce")
    cleaned["SeniorCitizen"] = cleaned["SeniorCitizen"].map({1: "Yes", 0: "No"})
    cleaned = cleaned.dropna(subset=["TotalCharges"]).drop_duplicates(subset=spec.id_column)
    return cleaned.reset_index(drop=True)


def load_dataset(path: Path, spec: FeatureSpec) -> pd.DataFrame:
    return clean(load_raw(path), spec)

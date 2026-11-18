from pathlib import Path

import pandas as pd

from .config import FeatureSpec


def load_raw(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def clean(df: pd.DataFrame, spec: FeatureSpec) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["TotalCharges"] = pd.to_numeric(cleaned["TotalCharges"].astype(str).str.strip(), errors="coerce")
    cleaned["SeniorCitizen"] = cleaned["SeniorCitizen"].map({1: "Yes", 0: "No"})
    missing_charges = int(cleaned["TotalCharges"].isna().sum())
    cleaned = cleaned.dropna(subset=["TotalCharges"])
    duplicates = int(cleaned.duplicated(subset=spec.id_column).sum())
    cleaned = cleaned.drop_duplicates(subset=spec.id_column).reset_index(drop=True)
    cleaned.attrs["quality"] = {
        "raw_customers": len(df), "missing_total_charges_removed": missing_charges,
        "duplicate_ids_removed": duplicates, "clean_customers": len(cleaned),
    }
    return cleaned


def load_dataset(path: Path, spec: FeatureSpec) -> pd.DataFrame:
    return clean(load_raw(path), spec)

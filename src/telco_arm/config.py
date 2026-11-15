from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    raw_data: Path = PROJECT_ROOT / "data" / "raw" / "telco_customer_churn.csv"
    output_dir: Path = PROJECT_ROOT / "outputs"

    @property
    def tables_dir(self) -> Path:
        return self.output_dir / "tables"

    @property
    def figures_dir(self) -> Path:
        return self.output_dir / "figures"


@dataclass(frozen=True)
class MiningParams:
    min_support: float = 0.10
    min_confidence: float = 0.70
    min_lift: float = 1.20
    max_len: int = 4


@dataclass(frozen=True)
class TargetParams:
    target: str
    min_support: float
    min_confidence: float
    min_lift: float
    max_len: int = 5
    min_improvement: float = 0.02


@dataclass(frozen=True)
class FeatureSpec:
    id_column: str = "customerID"
    target_column: str = "Churn"
    tenure_bins: tuple[float, ...] = (-1, 12, 24, 48, 72)
    tenure_labels: tuple[str, ...] = ("0-12m", "13-24m", "25-48m", "49-72m")
    charge_labels: tuple[str, ...] = ("Low", "Medium", "High")
    binary_columns: tuple[str, ...] = (
        "gender",
        "SeniorCitizen",
        "Partner",
        "Dependents",
        "PhoneService",
        "PaperlessBilling",
    )
    categorical_columns: tuple[str, ...] = (
        "InternetService",
        "Contract",
        "PaymentMethod",
    )
    addon_columns: tuple[str, ...] = (
        "MultipleLines",
        "OnlineSecurity",
        "OnlineBackup",
        "DeviceProtection",
        "TechSupport",
        "StreamingTV",
        "StreamingMovies",
    )
    not_applicable_values: tuple[str, ...] = ("No internet service", "No phone service")


@dataclass(frozen=True)
class Settings:
    paths: Paths = field(default_factory=Paths)
    features: FeatureSpec = field(default_factory=FeatureSpec)
    mining: MiningParams = field(default_factory=MiningParams)
    churn: TargetParams = field(
        default_factory=lambda: TargetParams("Churn=Yes", min_support=0.03, min_confidence=0.55, min_lift=2.0)
    )
    retention: TargetParams = field(
        default_factory=lambda: TargetParams("Churn=No", min_support=0.10, min_confidence=0.90, min_lift=1.2)
    )

    @property
    def target_items(self) -> tuple[str, ...]:
        return self.churn.target, self.retention.target

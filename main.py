import argparse
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from telco_arm import Settings, run
from telco_arm.analysis import readable_rules
from telco_arm.pipeline import export_figures, export_tables


def parse_args() -> argparse.Namespace:
    defaults = Settings()
    parser = argparse.ArgumentParser(description="Apriori association rule mining on telco customer behaviour")
    parser.add_argument("--data", type=Path, default=defaults.paths.raw_data)
    parser.add_argument("--output", type=Path, default=defaults.paths.output_dir)
    parser.add_argument("--min-support", type=float, default=defaults.mining.min_support)
    parser.add_argument("--min-confidence", type=float, default=defaults.mining.min_confidence)
    parser.add_argument("--min-lift", type=float, default=defaults.mining.min_lift)
    parser.add_argument("--max-len", type=int, default=defaults.mining.max_len)
    parser.add_argument("--churn-support", type=float, default=defaults.churn.min_support)
    parser.add_argument("--churn-confidence", type=float, default=defaults.churn.min_confidence)
    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--top", type=int, default=10)
    return parser.parse_args()


def build_settings(args: argparse.Namespace) -> Settings:
    defaults = Settings()
    return replace(
        defaults,
        paths=replace(defaults.paths, raw_data=args.data, output_dir=args.output),
        mining=replace(
            defaults.mining,
            min_support=args.min_support,
            min_confidence=args.min_confidence,
            min_lift=args.min_lift,
            max_len=args.max_len,
        ),
        churn=replace(defaults.churn, min_support=args.churn_support, min_confidence=args.churn_confidence),
    )


def print_section(title: str, rules, top: int) -> None:
    print(f"\n{title} ({len(rules):,} rules)")
    print("-" * len(title))
    if rules.empty:
        print("No rules satisfy the thresholds.")
        return
    columns = ["rule", "support", "confidence", "lift"]
    print(readable_rules(rules.head(top))[columns].to_string(index=False, max_colwidth=110))


def main() -> None:
    args = parse_args()
    settings = build_settings(args)
    result = run(settings)

    print(f"Customers: {len(result.customers):,} | Items: {result.onehot.shape[1]} | "
          f"Churn rate: {result.churn_rate:.2%} | Frequent itemsets: {len(result.itemsets):,}")
    print_section("Service usage rules", result.service_rules, args.top)
    print_section("Churn rules (-> Churn=Yes)", result.churn_rules, args.top)
    print_section("Retention rules (-> Churn=No)", result.retention_rules, args.top)

    tables = export_tables(result, settings.paths.tables_dir)
    figures = [] if args.no_figures else export_figures(result, settings.paths.figures_dir)
    print(f"\nSaved {len(tables)} tables to {settings.paths.tables_dir}")
    if figures:
        print(f"Saved {len(figures)} figures to {settings.paths.figures_dir}")


if __name__ == "__main__":
    main()

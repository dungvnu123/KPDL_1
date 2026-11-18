import argparse
import math
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from telco_arm import Settings, run
from telco_arm.pipeline import export_figures, export_tables
from telco_arm.reporting import export_report, render_report


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
    parser.add_argument("--demographic-support", type=float, default=defaults.questions.demographic_support)
    parser.add_argument("--demographic-confidence", type=float, default=defaults.questions.demographic_confidence)
    parser.add_argument("--min-group-customers", type=int, default=defaults.questions.min_group_customers)
    parser.add_argument("--recommendations-per-customer", type=int, default=defaults.questions.recommendations_per_customer)
    args = parser.parse_args()
    for name in ("min_support", "churn_support", "demographic_support"):
        if not 0 < getattr(args, name) <= 1:
            parser.error(f"--{name.replace('_', '-')} must be in (0, 1]")
    for name in ("min_confidence", "churn_confidence", "demographic_confidence"):
        if not 0 <= getattr(args, name) <= 1:
            parser.error(f"--{name.replace('_', '-')} must be in [0, 1]")
    if not math.isfinite(args.min_lift) or args.min_lift < 0:
        parser.error("--min-lift must be finite and nonnegative")
    for name in ("max_len", "top", "min_group_customers", "recommendations_per_customer"):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be at least 1")
    return args


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
        questions=replace(
            defaults.questions,
            demographic_support=args.demographic_support,
            demographic_confidence=args.demographic_confidence,
            min_group_customers=args.min_group_customers,
            recommendations_per_customer=args.recommendations_per_customer,
        ),
    )


def main() -> None:
    matplotlib.use("Agg")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    settings = build_settings(args)
    result = run(settings)

    tables = export_tables(result, settings.paths.tables_dir)
    figures = [] if args.no_figures else export_figures(result, settings.paths.figures_dir)
    reports = export_report(result, settings.paths.output_dir, args.top)
    print(render_report(result, args.top))
    print(f"Saved report: {reports[0]}")
    print(f"Saved {len(tables)} tables to {settings.paths.tables_dir}")
    if figures:
        print(f"Saved {len(figures)} figures to {settings.paths.figures_dir}")


if __name__ == "__main__":
    main()

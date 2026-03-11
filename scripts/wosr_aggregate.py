#!/usr/bin/env python3
"""
wosr_aggregate.py
Aggregate per-year CSVs into a single country-level summary.

Reads all wosr_<COUNTRY>_<YEAR>.csv from --results-dir/<COUNTRY>/
(S3 sync is handled by the caller — this script is pure local I/O)
Computes:
  - 30-year mean LR (1995-2024)
  - 5-year mean LR (2020-2024)
  - Weighted pricing LR: 0.60 * 5yr + 0.40 * 30yr
  - One-bad-year check (any region with <5 data years gets worst-year loading)
  - Premium at 0% deductible (= pricing LR) and 50% deductible (= pricing LR / 2)

Outputs CSV to --output-dir/<COUNTRY>_summary.csv

Usage:
    python wosr_aggregate.py --country RO --results-dir /results --output-dir /summaries
    python wosr_aggregate.py --all --results-dir /results --output-dir /summaries
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SUM_INSURED = 96.0  # EUR/ha
CF = 0.3589

COUNTRIES = ["RO", "MD", "PL", "CZ", "SK", "HU", "UA"]


def load_country_results(results_dir, country):
    country_dir = Path(results_dir) / country
    if not country_dir.exists():
        return None
    dfs = []
    for csv_file in sorted(country_dir.glob("*.csv")):
        df = pd.read_csv(csv_file)
        dfs.append(df)
    if not dfs:
        return None
    return pd.concat(dfs, ignore_index=True)


def aggregate_country(df, country):
    rows = []
    for region_id, grp in df.groupby("region_id"):
        grp = grp.sort_values("year")
        n_years = len(grp)

        lr_std = grp["lr_standard_pct"].dropna()
        lr_full = grp["lr_full_pct"].dropna()

        lr_30 = lr_std.mean() if len(lr_std) > 0 else np.nan
        lr_5  = lr_std[grp["year"].isin(range(2020, 2025))].mean() if len(lr_std) > 0 else np.nan

        # One-bad-year loading for sparse data
        one_bad = 0
        if n_years < 5 or grp["region_id"].iloc[0].startswith("UA"):
            one_bad = 1
            worst_yr_lr = 100.0  # 100% loss for one hypothetical year
            lr_30 = (lr_30 * n_years + worst_yr_lr) / (n_years + 1) if not np.isnan(lr_30) else worst_yr_lr

        # Weighted pricing LR
        if np.isnan(lr_5):
            pricing_lr = lr_30
        elif np.isnan(lr_30):
            pricing_lr = lr_5
        else:
            pricing_lr = 0.60 * lr_5 + 0.40 * lr_30

        # Full package
        lr_full_mean = lr_full.mean() if len(lr_full) > 0 else np.nan

        # Premiums
        premium_std_0pct  = pricing_lr if not np.isnan(pricing_lr) else np.nan
        premium_std_50pct = pricing_lr / 2 if not np.isnan(pricing_lr) else np.nan
        premium_full_0pct = lr_full_mean if not np.isnan(lr_full_mean) else np.nan

        rows.append({
            "country": country,
            "region_id": region_id,
            "region_name": grp["region_name"].iloc[0],
            "risk_zone": grp["risk_zone"].iloc[0],
            "n_years": n_years,
            "one_bad_year_applied": one_bad,
            "lr_std_30yr_pct": round(lr_30, 2) if not np.isnan(lr_30) else None,
            "lr_std_5yr_pct":  round(lr_5, 2) if not np.isnan(lr_5) else None,
            "lr_std_pricing_pct": round(pricing_lr, 2) if not np.isnan(pricing_lr) else None,
            "lr_full_pricing_pct": round(lr_full_mean, 2) if not np.isnan(lr_full_mean) else None,
            "premium_std_0pct":   round(premium_std_0pct, 2) if not np.isnan(premium_std_0pct) else None,
            "premium_std_eur_ha": round(SUM_INSURED * premium_std_0pct / 100, 2) if not np.isnan(premium_std_0pct) else None,
            "premium_std_50pct":  round(premium_std_50pct, 2) if not np.isnan(premium_std_50pct) else None,
            "premium_full_0pct":  round(premium_full_0pct, 2) if not np.isnan(premium_full_0pct) else None,
            "premium_full_eur_ha": round(SUM_INSURED * premium_full_0pct / 100, 2) if not np.isnan(premium_full_0pct) else None,
        })

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Aggregate WOSR results.")
    parser.add_argument("--country", choices=COUNTRIES)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--results-dir", required=True, help="Local dir with per-country result CSVs")
    parser.add_argument("--output-dir", required=True, help="Local dir for summary CSV output")
    args = parser.parse_args()

    if not args.all and not args.country:
        sys.exit("Specify --country or --all")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = COUNTRIES if args.all else [args.country]

    for country in targets:
        print(f"\nAggregating {country}...")
        df = load_country_results(args.results_dir, country)
        if df is None or len(df) == 0:
            print(f"  No results found for {country}")
            continue

        print(f"  Loaded {len(df)} region-year rows ({df['year'].min()}-{df['year'].max()})")
        summary = aggregate_country(df, country)

        # Print summary
        print(f"\n  {country} Summary:")
        print(f"  {'Region':<35} {'Zone':<5} {'LR-Std%':>8} {'LR-Full%':>9} {'Prem-Std €/ha':>14}")
        print(f"  {'-'*75}")
        for _, row in summary.iterrows():
            print(f"  {row['region_name']:<35} {row['risk_zone']:<5} "
                  f"{str(row['lr_std_pricing_pct']):>8} {str(row['lr_full_pricing_pct']):>9} "
                  f"{str(row['premium_std_eur_ha']):>14}")

        national_avg = summary["lr_std_pricing_pct"].mean()
        print(f"\n  National avg Standard LR: {national_avg:.1f}%")
        print(f"  National avg Full LR:     {summary['lr_full_pricing_pct'].mean():.1f}%")

        out_path = out_dir / f"{country}_summary.csv"
        summary.to_csv(out_path, index=False)
        print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
wosr_analyze_results.py
Analyze all completed WOSR results and produce a comprehensive report.

Downloads all results from S3, runs aggregate, produces:
- Per-country summary tables
- Cross-country comparison
- Key risk statistics
- Markdown report

Usage:
    python wosr_analyze_results.py --output-dir /path/to/output
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COUNTRIES = ["RO", "MD", "PL", "HU", "CZ", "SK", "UA"]
SUM_INSURED = 96.0  # EUR/ha


def load_all_results(results_dir):
    """Load all per-year CSVs from local results dir."""
    data = {}
    for country in COUNTRIES:
        country_dir = Path(results_dir) / country
        if not country_dir.exists():
            continue
        dfs = []
        for f in sorted(country_dir.glob("*.csv")):
            dfs.append(pd.read_csv(f))
        if dfs:
            data[country] = pd.concat(dfs, ignore_index=True)
            print(f"  {country}: {len(dfs)} years, {data[country]['region_id'].nunique()} regions")
    return data


def country_summary(df, country):
    """Compute summary statistics for one country."""
    rows = []
    for region_id, grp in df.groupby("region_id"):
        grp = grp.sort_values("year")
        n = len(grp)
        lr_std = grp["lr_standard_pct"]
        lr_full = grp["lr_full_pct"]
        lr_5yr = lr_std[grp["year"].isin(range(2020, 2025))].mean()
        lr_30yr = lr_std.mean()

        one_bad = 1 if (n < 5 or region_id.startswith("UA")) else 0
        if one_bad:
            lr_30yr = (lr_30yr * n + 100.0) / (n + 1) if not np.isnan(lr_30yr) else 100.0

        pricing_lr = (0.60 * lr_5yr + 0.40 * lr_30yr) if not (np.isnan(lr_5yr) or np.isnan(lr_30yr)) else lr_30yr

        rows.append({
            "country": country,
            "region_id": region_id,
            "region_name": grp["region_name"].iloc[0],
            "risk_zone": grp["risk_zone"].iloc[0],
            "n_years": n,
            "one_bad_year": one_bad,
            "lr_30yr_pct": round(lr_30yr, 2),
            "lr_5yr_pct": round(lr_5yr, 2) if not np.isnan(lr_5yr) else None,
            "lr_pricing_pct": round(pricing_lr, 2) if not np.isnan(pricing_lr) else None,
            "lr_full_mean_pct": round(lr_full.mean(), 2),
            "lr_std_max_pct": round(lr_std.max(), 2),
            "worst_year": int(grp.loc[lr_std.idxmax(), "year"]),
            "premium_eur_ha": round(SUM_INSURED * pricing_lr / 100, 2) if not np.isnan(pricing_lr) else None,
        })
    return pd.DataFrame(rows)


def generate_report(data, output_dir):
    """Generate full markdown report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries = {}
    all_summary_rows = []
    for country, df in data.items():
        print(f"\nAnalyzing {country}...")
        summ = country_summary(df, country)
        summaries[country] = summ
        summ.to_csv(out_dir / f"{country}_summary.csv", index=False)
        all_summary_rows.append(summ)

    if not summaries:
        print("No data to report")
        return

    all_summ = pd.concat(all_summary_rows, ignore_index=True)

    lines = []
    lines.append("# WOSR Emergence Guarantee — Historical Loss Analysis Results")
    lines.append(f"\n**Generated:** 2026-03-11  |  **Period:** 1995–2024  |  **Countries:** {', '.join(summaries.keys())}\n")
    lines.append("---\n")

    # Cross-country overview
    lines.append("## Cross-Country Overview\n")
    lines.append("| Country | Regions | Years | Nat. Avg Std LR | Nat. Avg Full LR | Avg Premium €/ha |")
    lines.append("|---------|---------|-------|-----------------|------------------|-----------------|")
    for country, summ in summaries.items():
        n_regions = len(summ)
        n_years = int(data[country]["year"].nunique())
        avg_std = summ["lr_pricing_pct"].mean()
        avg_full = summ["lr_full_mean_pct"].mean()
        avg_prem = summ["premium_eur_ha"].mean()
        lines.append(f"| {country} | {n_regions} | {n_years} | {avg_std:.1f}% | {avg_full:.1f}% | €{avg_prem:.2f} |")

    # Per-country sections
    for country, summ in summaries.items():
        df = data[country]
        lines.append(f"\n---\n\n## {country} — Detailed Results\n")

        # Year-by-year
        lines.append("### Year-by-Year National Mean LR\n")
        lines.append("| Year | Std LR % | Full LR % | Worst County | Worst Std % |")
        lines.append("|------|----------|-----------|--------------|-------------|")
        for yr, g in df.groupby("year"):
            worst_idx = g["lr_standard_pct"].idxmax()
            lines.append(f"| {yr} | {g['lr_standard_pct'].mean():.2f} | {g['lr_full_pct'].mean():.2f} "
                         f"| {g.loc[worst_idx,'region_name']} | {g.loc[worst_idx,'lr_standard_pct']:.1f} |")

        # Regional summary
        lines.append(f"\n### Regional Pricing Summary (30yr weighted)\n")
        lines.append("| Region | Zone | LR Std % | LR Full % | Premium €/ha | Worst Year |")
        lines.append("|--------|------|----------|-----------|--------------|-----------|")
        for _, row in summ.sort_values("lr_pricing_pct", ascending=False).iterrows():
            lines.append(f"| {row['region_name']} | {row['risk_zone']} | "
                         f"{row['lr_pricing_pct']:.2f} | {row['lr_full_mean_pct']:.2f} | "
                         f"€{row['premium_eur_ha']:.2f} | {row['worst_year']} |")

        # Zone averages
        lines.append(f"\n### Zone Averages — {country}\n")
        for zone, zg in summ.groupby("risk_zone"):
            lines.append(f"- **{zone}**: {len(zg)} regions — Avg Std LR {zg['lr_pricing_pct'].mean():.2f}%, "
                         f"Avg Premium €{zg['premium_eur_ha'].mean():.2f}/ha")

    report_path = out_dir / "WOSR_Results_Report.md"
    report_path.write_text("\n".join(lines))
    print(f"\nReport saved: {report_path}")

    # Also save combined CSV
    all_summ.to_csv(out_dir / "all_countries_summary.csv", index=False)
    print(f"Combined summary: {out_dir}/all_countries_summary.csv")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="/home/ubuntu/wosr/results", help="Local results dir")
    parser.add_argument("--output-dir", default="/home/ubuntu/wosr/analysis", help="Output dir for reports")
    args = parser.parse_args()

    print("Loading results...")
    data = load_all_results(args.results_dir)
    if not data:
        sys.exit("No results found")
    generate_report(data, args.output_dir)


if __name__ == "__main__":
    main()

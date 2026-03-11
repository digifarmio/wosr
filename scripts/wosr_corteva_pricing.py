#!/usr/bin/env python3
"""
wosr_corteva_pricing.py
County-level WOSR Emergence Guarantee pricing model.

Input: seed sold per county (CSV with columns: region_id OR region_name, seed_kg OR ha)
Output: per-county premium estimates

Usage:
    python wosr_corteva_pricing.py --country RO [--seed-file corteva_seed_data.csv] [--output-dir pricing_output]
    python wosr_corteva_pricing.py --all [--output-dir pricing_output]

Without --seed-file: produces county pricing table (rate cards) for all counties.
With --seed-file: applies actual Corteva seed volumes to produce total premium estimates.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Constants
SUM_INSURED = 96.0      # EUR/ha (standard WOSR emergence guarantee)
SEED_KG_PER_HA = 3.5    # kg seed / ha (WOSR typical seeding rate)
BROKERAGE_LOAD = 1.30   # 30% commercial loading (expenses + brokerage + margin)

COUNTRY_NAMES = {
    "RO": "Romania",
    "MD": "Moldova",
    "PL": "Poland",
    "HU": "Hungary",
    "CZ": "Czech Republic",
    "SK": "Slovakia",
    "UA": "Ukraine",
}


def load_summary(analysis_dir, country):
    """Load pre-computed county summary CSV."""
    path = Path(analysis_dir) / f"{country}_summary.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    return df


def load_seed_file(seed_file, country):
    """Load Corteva seed sold data. Expected columns: region_id or region_name, seed_kg or ha."""
    df = pd.read_csv(seed_file)
    df.columns = [c.strip().lower() for c in df.columns]
    # Normalize column names
    if "seed_kg" in df.columns and "ha" not in df.columns:
        df["ha"] = df["seed_kg"] / SEED_KG_PER_HA
    if "region_name" in df.columns and "region_id" not in df.columns:
        df["region_id"] = None  # will merge on name
    return df


def build_pricing_table(summary_df, seed_df=None):
    """
    Build complete pricing table for a country.
    If seed_df provided, joins with seed volumes to estimate total premiums.
    """
    df = summary_df.copy()

    # Gross premium (pure technical rate × sum insured)
    df["gross_premium_eur_ha"] = (df["lr_pricing_pct"] / 100 * SUM_INSURED).round(2)

    # Indicative commercial premium (with 30% loading)
    df["commercial_premium_eur_ha"] = (df["gross_premium_eur_ha"] * BROKERAGE_LOAD).round(2)

    # 50% deductible variant (50% rebate on full package pays out)
    df["lr_50pct_deductible_pct"] = (df["lr_pricing_pct"] * 0.5).round(2)
    df["premium_50pct_eur_ha"] = (df["lr_50pct_deductible_pct"] / 100 * SUM_INSURED).round(2)

    if seed_df is not None:
        # Merge on region_id or region_name
        if "region_id" in seed_df.columns and seed_df["region_id"].notna().any():
            df = df.merge(seed_df[["region_id", "ha"]], on="region_id", how="left")
        else:
            df = df.merge(
                seed_df[["region_name", "ha"]].rename(columns={"region_name": "region_name"}),
                on="region_name", how="left"
            )
        df["ha"] = df["ha"].fillna(0)
        df["total_premium_eur"] = (df["ha"] * df["commercial_premium_eur_ha"]).round(0)
        df["sum_insured_eur"] = (df["ha"] * SUM_INSURED).round(0)

    return df


def format_markdown_table(df, country, n_years, include_volumes=False):
    """Format pricing table as markdown."""
    lines = []
    cname = COUNTRY_NAMES.get(country, country)
    lines.append(f"## {cname} ({country}) — County-Level WOSR Pricing")
    lines.append(f"\n*Based on {n_years} years of ERA5-Land historical data (1995–2024 partial)*  ")
    lines.append(f"*Sum insured: €{SUM_INSURED}/ha | Sigmoid ELF model, CF=0.3589, Marsh-calibrated*\n")

    if include_volumes:
        lines.append("| County | Zone | LR (Std) % | LR (Full) % | Rate €/ha | Comm. €/ha | 50% Ded. €/ha | Ha | Total Premium € | Worst Year |")
        lines.append("|--------|------|-----------|------------|-----------|------------|--------------|-----|----------------|-----------|")
        for _, r in df.sort_values("lr_pricing_pct", ascending=False).iterrows():
            ha_str = f"{int(r['ha']):,}" if pd.notna(r.get('ha')) and r.get('ha', 0) > 0 else "—"
            tp_str = f"€{int(r['total_premium_eur']):,}" if pd.notna(r.get('total_premium_eur')) and r.get('total_premium_eur', 0) > 0 else "—"
            lines.append(
                f"| {r['region_name']} | {r['risk_zone']} | {r['lr_pricing_pct']:.2f} | "
                f"{r['lr_full_mean_pct']:.2f} | €{r['gross_premium_eur_ha']:.2f} | "
                f"€{r['commercial_premium_eur_ha']:.2f} | €{r['premium_50pct_eur_ha']:.2f} | "
                f"{ha_str} | {tp_str} | {r['worst_year']} |"
            )
    else:
        lines.append("| County | Zone | LR (Std) % | LR (Full) % | Pure Rate €/ha | Commercial €/ha | 50% Ded. €/ha | Worst Year |")
        lines.append("|--------|------|-----------|------------|--------------|----------------|--------------|-----------|")
        for _, r in df.sort_values("lr_pricing_pct", ascending=False).iterrows():
            lines.append(
                f"| {r['region_name']} | {r['risk_zone']} | {r['lr_pricing_pct']:.2f} | "
                f"{r['lr_full_mean_pct']:.2f} | €{r['gross_premium_eur_ha']:.2f} | "
                f"€{r['commercial_premium_eur_ha']:.2f} | €{r['premium_50pct_eur_ha']:.2f} | "
                f"{r['worst_year']} |"
            )

    # Zone summary
    lines.append(f"\n### Zone Averages\n")
    lines.append("| Zone | Counties | Avg LR Std % | Avg Pure Rate €/ha | Avg Commercial €/ha |")
    lines.append("|------|----------|-------------|-------------------|---------------------|")
    for zone, zg in df.groupby("risk_zone"):
        lines.append(
            f"| {zone} | {len(zg)} | {zg['lr_pricing_pct'].mean():.2f} | "
            f"€{zg['gross_premium_eur_ha'].mean():.2f} | €{zg['commercial_premium_eur_ha'].mean():.2f} |"
        )

    # National summary
    nat_lr = df["lr_pricing_pct"].mean()
    nat_pure = df["gross_premium_eur_ha"].mean()
    nat_comm = df["commercial_premium_eur_ha"].mean()
    lines.append(f"\n**National average**: LR {nat_lr:.2f}% | Pure rate €{nat_pure:.2f}/ha | Commercial €{nat_comm:.2f}/ha")

    if include_volumes and "total_premium_eur" in df.columns:
        total_ha = df["ha"].sum()
        total_si = df["sum_insured_eur"].sum()
        total_prem = df["total_premium_eur"].sum()
        lines.append(f"**Portfolio total**: {total_ha:,.0f} ha | Sum insured €{total_si:,.0f} | Est. premium €{total_prem:,.0f}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="WOSR county-level pricing model")
    parser.add_argument("--country", help="Country code (RO, MD, PL, HU, CZ, SK)")
    parser.add_argument("--all", action="store_true", help="Process all available countries")
    parser.add_argument("--analysis-dir", default="/home/ubuntu/wosr/analysis", help="Analysis summaries dir")
    parser.add_argument("--seed-file", help="Corteva seed sold CSV (optional)")
    parser.add_argument("--output-dir", default="/home/ubuntu/wosr/pricing", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    countries = list(COUNTRY_NAMES.keys()) if args.all else [args.country]
    if not countries[0]:
        parser.error("Specify --country or --all")

    seed_df = None
    if args.seed_file:
        print(f"Loading seed data from {args.seed_file}...")
        seed_df = load_seed_file(args.seed_file, countries[0])

    all_pricing = []
    report_sections = []

    report_sections.append("# WOSR Emergence Guarantee — County-Level Pricing Model")
    report_sections.append(f"\n**Generated:** 2026-03-11 | **Model:** v1 Pilot (Marsh-calibrated ERA5-Land)  ")
    report_sections.append(f"**Sum insured:** €{SUM_INSURED}/ha | **Commercial loading:** {int((BROKERAGE_LOAD-1)*100)}% over pure technical rate  ")
    report_sections.append(f"**Intended use:** Indicative pricing for Corteva/Frontera WOSR Emergence Guarantee discussions\n")
    report_sections.append("> ⚠️ **V1 Pilot**: Romania validated against Marsh portfolio. Non-RO countries use climate analogues — treat as indicative.\n")
    report_sections.append("---\n")

    for country in countries:
        summary_df = load_summary(args.analysis_dir, country)
        if summary_df is None:
            print(f"  {country}: no summary found, skipping")
            continue

        n_years = int(summary_df["n_years"].max())
        pricing_df = build_pricing_table(summary_df, seed_df if country == countries[0] else None)
        pricing_df.to_csv(out_dir / f"{country}_county_pricing.csv", index=False)
        print(f"  {country}: {len(pricing_df)} counties, avg LR {pricing_df['lr_pricing_pct'].mean():.2f}%")

        section = format_markdown_table(pricing_df, country, n_years, include_volumes=(seed_df is not None and country == countries[0]))
        report_sections.append(section)
        report_sections.append("\n---\n")

        all_pricing.append(pricing_df)

    # Write combined report
    report_path = out_dir / "WOSR_County_Pricing_Report.md"
    report_path.write_text("\n".join(report_sections))
    print(f"\nReport: {report_path}")

    if all_pricing:
        combined = pd.concat(all_pricing, ignore_index=True)
        combined.to_csv(out_dir / "all_countries_county_pricing.csv", index=False)
        print(f"Combined CSV: {out_dir}/all_countries_county_pricing.csv")


if __name__ == "__main__":
    main()

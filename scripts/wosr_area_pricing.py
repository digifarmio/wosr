#!/usr/bin/env python3
"""
Generate Corteva Area-level WOSR pricing for Romania.

Maps Corteva sales Areas → counties using the Lumiposa corn mapping,
then aggregates county-level pricing to Area-level using WOSR sales weights.
"""

import csv
import sys
from pathlib import Path

# Corteva Area → county mapping (from "2026 Lumiposa corn.xlsx")
# Note: București excluded (no Corteva area, no farmland)
AREA_COUNTY_MAP = {
    "Area 1":  ["Ialomița", "Călărași"],
    "Area 2":  ["Buzău", "Brăila", "Galați"],
    "Area 3":  ["Iași", "Botoșani", "Neamț", "Suceava"],
    "Area 4":  ["Teleorman", "Giurgiu", "Prahova", "Argeș", "Ilfov", "Dâmbovița"],
    "Area 5":  ["Olt", "Vâlcea", "Dolj", "Mehedinți", "Gorj"],
    "Area 6":  ["Arad", "Timiș", "Caraș-Severin", "Hunedoara"],
    "Area 8":  ["Satu Mare", "Bihor", "Maramureș", "Sălaj"],
    "Area T":  ["Brașov", "Covasna", "Sibiu", "Alba", "Cluj", "Mureș", "Bistrița-Năsăud", "Harghita"],
    "Area 10": ["Tulcea", "Constanța"],
    "Area 11": ["Bacău", "Vaslui", "Vrancea"],
}

# WOSR sales per area (from "WOSR sales 2025.xlsx", units = bags)
WOSR_SALES = {
    "Area 1":  11549,
    "Area 2":  12865,
    "Area 3":  5544,
    "Area 4":  22594,
    "Area 5":  5678,
    "Area 6":  2585,
    "Area T":  2192,
    "Area 8":  2653,
    "Area 10": 7364,
    "Area 11": 4763,
}

SUM_INSURED = 96.0    # EUR/ha
LOADING = 1.30        # 30% commercial loading
SEED_RATE_KG_HA = 3.5 # kg seed per hectare
BAG_WEIGHT_KG = 10.0  # approximate bag weight (2M seeds ~ 10kg)


def load_county_pricing(csv_path):
    """Load county pricing CSV into dict keyed by region_name."""
    pricing = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["country"] == "RO":
                pricing[row["region_name"]] = row
    return pricing


def main():
    pricing_csv = Path(__file__).parent.parent / "pricing" / "RO_county_pricing.csv"
    if not pricing_csv.exists():
        print(f"ERROR: {pricing_csv} not found", file=sys.stderr)
        sys.exit(1)

    county_pricing = load_county_pricing(pricing_csv)
    output_dir = Path(__file__).parent.parent / "pricing"

    rows = []
    total_sales = sum(WOSR_SALES.values())
    total_premium = 0.0
    total_ha = 0.0

    for area in ["Area 1", "Area 2", "Area 3", "Area 4", "Area 5",
                  "Area 6", "Area T", "Area 8", "Area 10", "Area 11"]:
        counties = AREA_COUNTY_MAP[area]
        sales = WOSR_SALES[area]

        # Aggregate county-level LR (simple average across counties in area)
        lr_values = []
        lr_full_values = []
        worst_lr = 0.0
        worst_county = ""
        county_details = []

        for county_name in counties:
            cp = county_pricing.get(county_name)
            if cp:
                lr_pricing = float(cp["lr_pricing_pct"])
                lr_full = float(cp["lr_full_mean_pct"])
                lr_values.append(lr_pricing)
                lr_full_values.append(lr_full)
                prem = float(cp["commercial_premium_eur_ha"])
                county_details.append({
                    "county": county_name,
                    "lr_pricing": lr_pricing,
                    "lr_full": lr_full,
                    "premium": prem,
                    "risk_zone": cp["risk_zone"],
                    "worst_year": cp["worst_year"],
                })
                if lr_pricing > worst_lr:
                    worst_lr = lr_pricing
                    worst_county = county_name
            else:
                print(f"  WARNING: {county_name} not found in pricing", file=sys.stderr)

        if not lr_values:
            continue

        avg_lr = sum(lr_values) / len(lr_values)
        avg_lr_full = sum(lr_full_values) / len(lr_full_values)
        avg_premium = avg_lr / 100 * SUM_INSURED * LOADING

        # Estimate hectares from sales (bags → kg → ha)
        est_ha = sales * BAG_WEIGHT_KG / SEED_RATE_KG_HA
        area_total_premium = est_ha * avg_premium

        total_premium += area_total_premium
        total_ha += est_ha

        rows.append({
            "area": area,
            "counties": ", ".join(counties),
            "n_counties": len(counties),
            "wosr_sales_bags": sales,
            "est_hectares": round(est_ha),
            "avg_lr_std_pct": round(avg_lr, 2),
            "avg_lr_full_pct": round(avg_lr_full, 2),
            "avg_premium_eur_ha": round(avg_premium, 2),
            "area_total_premium_eur": round(area_total_premium),
            "worst_county": worst_county,
            "worst_county_lr_pct": round(worst_lr, 2),
            "county_details": county_details,
        })

    # Write area-level CSV
    csv_path = output_dir / "RO_area_pricing.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "area", "counties", "n_counties", "wosr_sales_bags", "est_hectares",
            "avg_lr_std_pct", "avg_lr_full_pct", "avg_premium_eur_ha",
            "area_total_premium_eur", "worst_county", "worst_county_lr_pct"
        ])
        for r in rows:
            writer.writerow([
                r["area"], r["counties"], r["n_counties"], r["wosr_sales_bags"],
                r["est_hectares"], r["avg_lr_std_pct"], r["avg_lr_full_pct"],
                r["avg_premium_eur_ha"], r["area_total_premium_eur"],
                r["worst_county"], r["worst_county_lr_pct"]
            ])

    print(f"Wrote: {csv_path}")

    # Write area-level markdown report
    md_path = output_dir / "RO_Area_Pricing_Report.md"
    with open(md_path, "w") as f:
        f.write("# WOSR Emergence Guarantee — Romania Area-Level Pricing\n\n")
        f.write("**Corteva Sales Areas mapped to county-level ERA5 35yr pricing**\n\n")
        f.write(f"- **Total WOSR sales**: {total_sales:,} bags ({round(total_ha):,} est. hectares)\n")
        f.write(f"- **Total portfolio premium**: EUR {round(total_premium):,}\n")
        f.write(f"- **Weighted avg premium**: EUR {total_premium/total_ha:.2f}/ha\n")
        f.write(f"- **Sum insured**: EUR {SUM_INSURED}/ha | **Loading**: {LOADING:.0%}\n\n")
        f.write("---\n\n")
        f.write("## Area Pricing Summary\n\n")
        f.write("| Area | Counties | WOSR Bags | Est. Ha | Avg LR Std % | Avg LR Full % | Premium EUR/ha | Area Premium EUR | Worst County (LR%) |\n")
        f.write("|------|----------|-----------|---------|-------------|--------------|---------------|-----------------|--------------------|\n")
        for r in rows:
            f.write(f"| {r['area']} | {r['n_counties']} counties | {r['wosr_sales_bags']:,} | {r['est_hectares']:,} | {r['avg_lr_std_pct']:.1f}% | {r['avg_lr_full_pct']:.1f}% | EUR {r['avg_premium_eur_ha']:.2f} | EUR {r['area_total_premium_eur']:,} | {r['worst_county']} ({r['worst_county_lr_pct']:.1f}%) |\n")

        f.write(f"\n**TOTAL** | 10 areas | {total_sales:,} | {round(total_ha):,} | — | — | EUR {total_premium/total_ha:.2f} | **EUR {round(total_premium):,}** | — |\n\n")

        f.write("---\n\n")
        f.write("## County Detail by Area\n\n")
        for r in rows:
            f.write(f"### {r['area']} — {r['counties']}\n\n")
            f.write("| County | Risk Zone | LR Std % | LR Full % | Premium EUR/ha | Worst Year |\n")
            f.write("|--------|-----------|---------|----------|---------------|------------|\n")
            for cd in r["county_details"]:
                f.write(f"| {cd['county']} | {cd['risk_zone']} | {cd['lr_pricing']:.2f}% | {cd['lr_full']:.2f}% | EUR {cd['premium']:.2f} | {cd['worst_year']} |\n")
            f.write(f"\n**Area avg**: {r['avg_lr_std_pct']:.2f}% LR | EUR {r['avg_premium_eur_ha']:.2f}/ha | {r['wosr_sales_bags']:,} bags ({r['est_hectares']:,} ha)\n\n")

        f.write("---\n\n")
        f.write("## Methodology Notes\n\n")
        f.write("- **Area→county mapping**: From Corteva Lumiposa corn sales data (`2026 Lumiposa corn.xlsx`)\n")
        f.write("- **County pricing**: ERA5-Land 35yr (1990–2024) sigmoid ELF model, Marsh-calibrated (CF=0.3589)\n")
        f.write("- **Area LR**: Simple average of constituent county LRs (equal-weighted)\n")
        f.write("- **Hectare estimate**: bags × 10 kg/bag ÷ 3.5 kg/ha seeding rate\n")
        f.write("- **Premium**: LR × EUR 96 (sum insured) × 1.30 (commercial loading)\n")
        f.write("- **București**: Excluded (no Corteva sales area, no agricultural land)\n\n")
        f.write("*Generated by DigiFarm AS, March 2026*\n")

    print(f"Wrote: {md_path}")

    # Print summary to stdout
    print("\n=== WOSR Romania — Corteva Area Pricing Summary ===\n")
    print(f"{'Area':<10} {'Bags':>8} {'Est Ha':>8} {'LR Std%':>8} {'EUR/ha':>8} {'Total EUR':>10}  Counties")
    print("-" * 90)
    for r in rows:
        counties_short = ", ".join(c[:8] for c in r["counties"].split(", ")[:3])
        if r["n_counties"] > 3:
            counties_short += f" +{r['n_counties']-3}"
        print(f"{r['area']:<10} {r['wosr_sales_bags']:>8,} {r['est_hectares']:>8,} {r['avg_lr_std_pct']:>7.1f}% {r['avg_premium_eur_ha']:>7.2f} {r['area_total_premium_eur']:>10,}  {counties_short}")
    print("-" * 90)
    print(f"{'TOTAL':<10} {total_sales:>8,} {round(total_ha):>8,} {'':>8} {total_premium/total_ha:>7.2f} {round(total_premium):>10,}")


if __name__ == "__main__":
    main()

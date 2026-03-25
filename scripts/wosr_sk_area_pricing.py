#!/usr/bin/env python3
"""
Generate Corteva Area-level WOSR pricing for Slovakia.

Maps Corteva sales Areas (8 areas, 72 districts/okresy) → kraje (8 self-governing regions)
using the district→kraj mapping, then aggregates kraj-level pricing to Area-level.

For areas spanning multiple kraje, the area LR is the simple average of the
constituent kraje LRs. Each kraj is counted once per area regardless of how many
districts from that kraj fall within the area.
"""

import csv
import sys
from pathlib import Path
from collections import OrderedDict

# ─── District → Kraj mapping ──────────────────────────────────────────────────
# Maps each Slovak district (okres) to its kraj's region_id in the pricing CSV.
DISTRICT_TO_KRAJ = {
    # Banskobystrický kraj (SK-BB)
    "Banská Štiavnica": "SK-BB",
    "Žarnovica": "SK-BB",
    "Žiar nad Hronom": "SK-BB",
    "Banská Bystrica": "SK-BB",
    "Brezno": "SK-BB",
    "Detva": "SK-BB",
    "Krupina": "SK-BB",
    "Lučenec": "SK-BB",
    "Poltár": "SK-BB",
    "Revúca": "SK-BB",
    "Rimavská Sobota": "SK-BB",
    "Veľký Krtíš": "SK-BB",
    "Zvolen": "SK-BB",
    # Bratislavský kraj (SK-BA)
    "Bratislava": "SK-BA",
    "Malacky": "SK-BA",
    "Pezinok": "SK-BA",
    "Senec": "SK-BA",
    # Košický kraj (SK-KE)
    "Michalovce": "SK-KE",
    "Sobrance": "SK-KE",
    "Trebišov": "SK-KE",
    "Gelnica": "SK-KE",
    "Košice": "SK-KE",
    "Spišská Nová Ves": "SK-KE",
    "Rožňava": "SK-KE",
    # Nitriansky kraj (SK-NI)
    "Topoľčany": "SK-NI",
    "Komárno": "SK-NI",
    "Levice": "SK-NI",
    "Nové Zámky": "SK-NI",
    "Nitra": "SK-NI",
    "Šaľa": "SK-NI",
    "Zlaté Moravce": "SK-NI",
    # Prešovský kraj (SK-PO)
    "Humenné": "SK-PO",
    "Snina": "SK-PO",
    "Vranov nad Topľou": "SK-PO",
    "Bardejov": "SK-PO",
    "Kežmarok": "SK-PO",
    "Levoča": "SK-PO",
    "Medzilaborce": "SK-PO",
    "Poprad": "SK-PO",
    "Prešov": "SK-PO",
    "Sabinov": "SK-PO",
    "Stará Ľubovňa": "SK-PO",
    "Stropkov": "SK-PO",
    "Svidník": "SK-PO",
    # Trnavský kraj (SK-TT)
    "Dunajská Streda": "SK-TT",
    "Galanta": "SK-TT",
    "Hlohovec": "SK-TT",
    "Piešťany": "SK-TT",
    "Senica": "SK-TT",
    "Skalica": "SK-TT",
    "Trnava": "SK-TT",
    # Trenčiansky kraj (SK-TN)
    "Bánovce nad Bebravou": "SK-TN",
    "Ilava": "SK-TN",
    "Nové Mesto nad Váhom": "SK-TN",
    "Partizánske": "SK-TN",
    "Považská Bystrica": "SK-TN",
    "Prievidza": "SK-TN",
    "Púchov": "SK-TN",
    "Trenčín": "SK-TN",
    "Myjava": "SK-TN",
    # Žilinský kraj (SK-ZA)
    "Bytča": "SK-ZA",
    "Čadca": "SK-ZA",
    "Kysucké Nové Mesto": "SK-ZA",
    "Martin": "SK-ZA",
    "Turčianske Teplice": "SK-ZA",
    "Žilina": "SK-ZA",
    "Dolný Kubín": "SK-ZA",
    "Námestovo": "SK-ZA",
    "Ružomberok": "SK-ZA",
    "Tvrdošín": "SK-ZA",
    "Liptovský Mikuláš": "SK-ZA",
}

# ─── Corteva Area → district mapping (from Nils's GDrive spreadsheet) ─────────
AREA_DISTRICT_MAP = OrderedDict([
    ("Area 1", [
        "Banská Štiavnica", "Žarnovica", "Žiar nad Hronom",  # SK-BB
        "Topoľčany",  # SK-NI
        "Bánovce nad Bebravou", "Ilava", "Nové Mesto nad Váhom", "Partizánske",
        "Považská Bystrica", "Prievidza", "Púchov", "Trenčín",  # SK-TN
        "Bytča", "Čadca", "Kysucké Nové Mesto", "Martin",
        "Turčianske Teplice", "Žilina",  # SK-ZA
    ]),
    ("Area 2", [
        "Komárno", "Dunajská Streda",  # SK-NI + SK-TT
    ]),
    ("Area 3", [
        "Michalovce", "Sobrance", "Trebišov",  # SK-KE
        "Humenné", "Snina", "Vranov nad Topľou",  # SK-PO
    ]),
    ("Area 4", [
        "Levice", "Nové Zámky",  # SK-NI
    ]),
    ("Area 5", [
        "Nitra", "Šaľa", "Zlaté Moravce",  # SK-NI
        "Galanta",  # SK-TT
    ]),
    ("Area 6", [
        "Banská Bystrica", "Brezno", "Detva", "Krupina", "Lučenec",
        "Poltár", "Revúca", "Rimavská Sobota", "Veľký Krtíš", "Zvolen",  # SK-BB
        "Rožňava",  # SK-KE
        "Dolný Kubín", "Námestovo", "Ružomberok", "Tvrdošín",  # SK-ZA
    ]),
    ("Area 7", [
        "Bratislava", "Malacky", "Pezinok", "Senec",  # SK-BA
        "Myjava",  # SK-TN
        "Hlohovec", "Piešťany", "Senica", "Skalica", "Trnava",  # SK-TT
    ]),
    ("Area 8", [
        "Gelnica", "Košice", "Spišská Nová Ves",  # SK-KE
        "Bardejov", "Kežmarok", "Levoča", "Medzilaborce", "Poprad",
        "Prešov", "Sabinov", "Stará Ľubovňa", "Stropkov", "Svidník",  # SK-PO
        "Liptovský Mikuláš",  # SK-ZA
    ]),
])

# ─── WOSR sales per area (bags, from GDrive spreadsheet) ──────────────────────
WOSR_SALES = OrderedDict([
    ("Area 1", 705),
    ("Area 2", 448),
    ("Area 3", 695),
    ("Area 4", 488),
    ("Area 5", 311),
    ("Area 6", 446),
    ("Area 7", 625),
    ("Area 8", 564),
])

# ─── Pricing parameters ──────────────────────────────────────────────────────
SUM_INSURED = 96.0     # EUR/ha
LOADING = 1.30         # 30% commercial loading
SEED_RATE_KG_HA = 3.5  # kg seed per hectare
BAG_WEIGHT_KG = 10.0   # approximate bag weight (2M seeds ~ 10kg)

# Kraj display names
KRAJ_NAMES = {
    "SK-BA": "Bratislavský",
    "SK-BB": "Banskobystrický",
    "SK-KE": "Košický",
    "SK-NI": "Nitriansky",
    "SK-PO": "Prešovský",
    "SK-TN": "Trenčiansky",
    "SK-TT": "Trnavský",
    "SK-ZA": "Žilinský",
}


def load_kraj_pricing(csv_path):
    """Load SK kraj-level pricing CSV into dict keyed by region_id."""
    pricing = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["country"] == "SK":
                pricing[row["region_id"]] = row
    return pricing


def get_area_kraje(districts):
    """Given list of districts, return unique set of kraje (region_ids)."""
    kraje = set()
    for d in districts:
        kraj = DISTRICT_TO_KRAJ.get(d)
        if kraj is None:
            print(f"  WARNING: district '{d}' not found in district→kraj mapping",
                  file=sys.stderr)
        else:
            kraje.add(kraj)
    return sorted(kraje)


def main():
    pricing_csv = Path(__file__).parent.parent / "pricing" / "SK_county_pricing.csv"
    if not pricing_csv.exists():
        print(f"ERROR: {pricing_csv} not found", file=sys.stderr)
        sys.exit(1)

    kraj_pricing = load_kraj_pricing(pricing_csv)
    output_dir = Path(__file__).parent.parent / "pricing"

    rows = []
    total_sales = sum(WOSR_SALES.values())
    total_premium = 0.0
    total_ha = 0.0

    for area, districts in AREA_DISTRICT_MAP.items():
        sales = WOSR_SALES[area]
        kraje = get_area_kraje(districts)

        lr_values = []
        lr_full_values = []
        worst_lr = 0.0
        worst_kraj = ""
        kraj_details = []

        for kraj_id in kraje:
            kp = kraj_pricing.get(kraj_id)
            if kp:
                lr_pricing = float(kp["lr_pricing_pct"])
                lr_full = float(kp["lr_full_mean_pct"])
                lr_values.append(lr_pricing)
                lr_full_values.append(lr_full)
                prem = float(kp["commercial_premium_eur_ha"])

                # Count how many districts from this area are in this kraj
                n_districts_in_kraj = sum(
                    1 for d in districts if DISTRICT_TO_KRAJ.get(d) == kraj_id
                )

                kraj_details.append({
                    "kraj_id": kraj_id,
                    "kraj_name": kp["region_name"],
                    "n_districts": n_districts_in_kraj,
                    "lr_pricing": lr_pricing,
                    "lr_full": lr_full,
                    "premium": prem,
                    "risk_zone": kp["risk_zone"],
                    "worst_year": kp["worst_year"],
                })
                if lr_pricing > worst_lr:
                    worst_lr = lr_pricing
                    worst_kraj = KRAJ_NAMES.get(kraj_id, kp["region_name"])
            else:
                print(f"  WARNING: {kraj_id} not found in pricing CSV",
                      file=sys.stderr)

        if not lr_values:
            continue

        # Simple average across kraje in this area
        avg_lr = sum(lr_values) / len(lr_values)
        avg_lr_full = sum(lr_full_values) / len(lr_full_values)
        avg_premium = avg_lr / 100 * SUM_INSURED * LOADING

        # Estimate hectares from sales
        est_ha = sales * BAG_WEIGHT_KG / SEED_RATE_KG_HA

        area_total_premium = est_ha * avg_premium
        total_premium += area_total_premium
        total_ha += est_ha

        # List districts grouped by kraj for display
        district_list = ", ".join(districts)

        rows.append({
            "area": area,
            "districts": district_list,
            "n_districts": len(districts),
            "kraje": kraje,
            "n_kraje": len(kraje),
            "wosr_sales_bags": sales,
            "est_hectares": round(est_ha),
            "avg_lr_std_pct": round(avg_lr, 2),
            "avg_lr_full_pct": round(avg_lr_full, 2),
            "avg_premium_eur_ha": round(avg_premium, 2),
            "area_total_premium_eur": round(area_total_premium),
            "worst_kraj": worst_kraj,
            "worst_kraj_lr_pct": round(worst_lr, 2),
            "kraj_details": kraj_details,
        })

    # ─── Write area-level CSV ─────────────────────────────────────────────────
    csv_path = output_dir / "SK_area_pricing.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "area", "kraje", "n_kraje", "n_districts", "wosr_sales_bags",
            "est_hectares", "avg_lr_std_pct", "avg_lr_full_pct",
            "avg_premium_eur_ha", "area_total_premium_eur",
            "worst_kraj", "worst_kraj_lr_pct"
        ])
        for r in rows:
            writer.writerow([
                r["area"],
                " + ".join(KRAJ_NAMES.get(k, k) for k in r["kraje"]),
                r["n_kraje"],
                r["n_districts"],
                r["wosr_sales_bags"],
                r["est_hectares"],
                r["avg_lr_std_pct"],
                r["avg_lr_full_pct"],
                r["avg_premium_eur_ha"],
                r["area_total_premium_eur"],
                r["worst_kraj"],
                r["worst_kraj_lr_pct"],
            ])

    print(f"Wrote: {csv_path}")

    # ─── Write Markdown report ────────────────────────────────────────────────
    md_path = output_dir / "SK_Area_Pricing_Report.md"
    with open(md_path, "w") as f:
        f.write("# WOSR Emergence Guarantee — Slovakia Area-Level Pricing\n\n")
        f.write("**Corteva Sales Areas (8) mapped to kraj-level ERA5 35yr pricing**\n\n")
        f.write(f"- **Total WOSR sales**: {total_sales:,} bags ({round(total_ha):,} est. hectares)\n")
        f.write(f"- **Total portfolio premium**: EUR {round(total_premium):,}\n")
        f.write(f"- **Weighted avg premium**: EUR {total_premium / total_ha:.2f}/ha\n")
        f.write(f"- **Sum insured**: EUR {SUM_INSURED:.0f}/ha | **Loading**: {LOADING:.0%}\n\n")
        f.write("---\n\n")

        # Area summary table
        f.write("## Area Pricing Summary\n\n")
        f.write("| Area | Kraje | Districts | WOSR Bags | Est. Ha | Avg LR Std % | Avg LR Full % | Premium EUR/ha | Area Premium EUR | Worst Kraj (LR%) |\n")
        f.write("|------|-------|-----------|-----------|---------|-------------|--------------|---------------|-----------------|------------------|\n")
        for r in rows:
            kraje_str = " + ".join(KRAJ_NAMES.get(k, k) for k in r["kraje"])
            f.write(
                f"| {r['area']} | {kraje_str} | {r['n_districts']} | "
                f"{r['wosr_sales_bags']:,} | {r['est_hectares']:,} | "
                f"{r['avg_lr_std_pct']:.2f}% | {r['avg_lr_full_pct']:.2f}% | "
                f"EUR {r['avg_premium_eur_ha']:.2f} | "
                f"EUR {r['area_total_premium_eur']:,} | "
                f"{r['worst_kraj']} ({r['worst_kraj_lr_pct']:.2f}%) |\n"
            )
        f.write(
            f"\n| **TOTAL** | 8 areas | {sum(r['n_districts'] for r in rows)} | "
            f"{total_sales:,} | {round(total_ha):,} | — | — | "
            f"EUR {total_premium / total_ha:.2f} | "
            f"**EUR {round(total_premium):,}** | — |\n\n"
        )

        f.write("---\n\n")

        # Kraj detail per area
        f.write("## Kraj Detail by Area\n\n")
        for r in rows:
            kraje_str = " + ".join(KRAJ_NAMES.get(k, k) for k in r["kraje"])
            f.write(f"### {r['area']} — {kraje_str}\n\n")
            f.write(f"**Districts ({r['n_districts']})**: {r['districts']}\n\n")
            f.write("| Kraj | Region ID | Districts in Area | Risk Zone | LR Std % | LR Full % | Premium EUR/ha | Worst Year |\n")
            f.write("|------|-----------|-------------------|-----------|---------|----------|---------------|------------|\n")
            for kd in r["kraj_details"]:
                f.write(
                    f"| {KRAJ_NAMES.get(kd['kraj_id'], kd['kraj_name'])} | "
                    f"{kd['kraj_id']} | {kd['n_districts']} | "
                    f"{kd['risk_zone']} | {kd['lr_pricing']:.2f}% | "
                    f"{kd['lr_full']:.2f}% | EUR {kd['premium']:.2f} | "
                    f"{kd['worst_year']} |\n"
                )
            f.write(
                f"\n**Area avg**: {r['avg_lr_std_pct']:.2f}% LR | "
                f"EUR {r['avg_premium_eur_ha']:.2f}/ha | "
                f"{r['wosr_sales_bags']:,} bags ({r['est_hectares']:,} ha)\n\n"
            )

        f.write("---\n\n")

        # District → Kraj reference
        f.write("## District → Kraj Reference\n\n")
        f.write("Each Corteva Area contains districts (okresy) from one or more kraje.\n")
        f.write("The area LR is the simple average of its constituent kraje LRs.\n\n")
        f.write("| Area | District | Kraj |\n")
        f.write("|------|----------|------|\n")
        for area, districts in AREA_DISTRICT_MAP.items():
            for d in districts:
                kraj_id = DISTRICT_TO_KRAJ.get(d, "?")
                f.write(f"| {area} | {d} | {KRAJ_NAMES.get(kraj_id, kraj_id)} ({kraj_id}) |\n")
        f.write("\n")

        f.write("---\n\n")

        # Methodology
        f.write("## Methodology Notes\n\n")
        f.write("- **Area→district mapping**: From Corteva Slovakia sales data (Nils's GDrive spreadsheet)\n")
        f.write("- **District→kraj mapping**: Standard Slovak administrative division (72 okresy → 8 kraje)\n")
        f.write("- **Kraj pricing**: ERA5-Land 35yr (1990-2024) sigmoid ELF model, Marsh-calibrated (CF=0.3589)\n")
        f.write("- **Area LR**: Simple average of constituent kraje LRs (each kraj counted once regardless of district count)\n")
        f.write("- **Hectare estimate**: bags x 10 kg/bag / 3.5 kg/ha seeding rate\n")
        f.write("- **Premium**: LR x EUR 96 (sum insured) x 1.30 (commercial loading)\n")
        f.write("- **Note**: SK pricing CSV uses 8 kraje (self-governing regions), not 72 districts. ")
        f.write("Areas that span multiple kraje get the average of those kraje.\n\n")
        f.write("*Generated by DigiFarm AS, March 2026*\n")

    print(f"Wrote: {md_path}")

    # ─── Print summary to stdout ──────────────────────────────────────────────
    print("\n=== WOSR Slovakia — Corteva Area Pricing Summary ===\n")
    print(f"{'Area':<10} {'Bags':>6} {'Est Ha':>7} {'Kraje':>6} {'LR%':>6} {'EUR/ha':>8} {'Total EUR':>10}  Kraje")
    print("-" * 95)
    for r in rows:
        kraje_short = " + ".join(KRAJ_NAMES.get(k, k)[:6] for k in r["kraje"])
        print(
            f"{r['area']:<10} {r['wosr_sales_bags']:>6,} "
            f"{r['est_hectares']:>7,} {r['n_kraje']:>6} "
            f"{r['avg_lr_std_pct']:>5.2f}% "
            f"{r['avg_premium_eur_ha']:>7.2f} "
            f"{r['area_total_premium_eur']:>10,}  {kraje_short}"
        )
    print("-" * 95)
    print(
        f"{'TOTAL':<10} {total_sales:>6,} {round(total_ha):>7,} "
        f"{'':>6} {'':>6} "
        f"{total_premium / total_ha:>7.2f} {round(total_premium):>10,}"
    )


if __name__ == "__main__":
    main()

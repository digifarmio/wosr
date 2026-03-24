# WOSR Emergence Guarantee — Comprehensive Project Definition

## 1. What Is This Project?

**Parametric climate insurance for Winter Oilseed Rape (WOSR) emergence risk**, bundled into Corteva seed bag sales across Central and Eastern Europe.

When a farmer buys Corteva WOSR seed, an emergence guarantee is automatically included. If climate conditions during the critical autumn sowing window prevent proper crop establishment (<20 plants/m²), the farmer receives an automatic payout — no field inspection, no claims adjuster. The trigger is a climate index computed from satellite-era weather reanalysis data.

**This is not traditional insurance.** It is a parametric guarantee: payouts are triggered by objective, third-party climate data (ERA5-Land from Copernicus/ECMWF), not by on-farm loss assessment. This structure avoids insurance regulation (critical for Corteva's accounting treatment) while providing real crop protection.

---

## 2. How This Project Started

### Origin: Corn Emergence Guarantee (2025)

The WOSR program extends an existing **corn emergence guarantee** that DigiFarm/Frontera built for Corteva Romania in 2025:

- **Jul–Nov 2025**: DigiFarm and Marsh (insurance broker) developed a 30-year historical loss ratio model for corn replanting risk in Romania, using county-level climate data
- **Sep 2025**: Premium pricing exercises with Marsh, Munich Re as potential reinsurer
- **Oct 2025**: FARM Replanting Insurance Specification finalized; Corteva pilot agreed for Romania 2026 (100,000 ha, Lumiposa-treated hybrids)
- **Nov 2025**: Descartes Underwriting joined as validation/underwriting partner
- **Dec 2025**: Fronterax Technologies S.L. acquired DigiFarm AS (EUR 4M SPA signed 2025-12-31)
- **Jan 2026**: Definitive Actuarial Methodology documents produced (multiple versions); Emergence Guarantee Agreement drafts circulated (USD 450K program fee)
- **Feb 2026**: Activation guides, claims submission guides, and one-pagers produced in English and Romanian

### Expansion to WOSR (March 2026)

On **2026-03-09**, Nils Helset (DigiFarm CEO) relayed from Matti Tiainen (Frontera Ag) that **Corteva wants to extend the emergence guarantee from corn to WOSR** across Romania and 5 additional CEE countries.

Key Slack messages from Nils (Mar 9–10):
- "We need to do the same underwriting process for winter oilseed rape for Romania"
- "Moldova, Poland, Ukraine, Czech Republic, Slovakia and Hungary"
- "Start with calculating autumn replant risk and then spring emergence after"
- "We need something asap this week" — meeting confirmed for **2026-03-11 at 3 PM**

The WOSR model was built in 48 hours (Mar 10–11), validated against Marsh Romania claims data, and presented at the meeting. It has since been extended from 11 years to 35 years (1990–2024) across all 6 countries.

---

## 3. Parties and Roles

| Party | Role | Key People |
|-------|------|------------|
| **DigiFarm AS** | Technology provider — builds the climate model, validation platform, and analytics | Konstantin Varik (CTO), Morris Warachi (engineer) |
| **Frontera Ag** | Commercial partner — coordinates with Corteva, manages the insurance program | Matti Tiainen |
| **Fronterax Technologies S.L.** | Parent company (acquired DigiFarm Dec 2025) | Nils Helset (CEO) |
| **Corteva Agriscience** | Seed company — bundles guarantee into seed bag price, pays program fee | Alexandra Gheorghe (RO), country leads per market |
| **Marsh** | Insurance broker — structured the original corn program, provided Romania claims data for calibration | Horatiu Udroiu (Vara Ag/Marsh broker) |
| **Descartes Underwriting** | Reinsurance/validation partner — reviews methodology, provides underwriting capacity | Antoine, Etienne Selles |
| **Munich Re / Hannover Re** | Potential reinsurers — referenced in program structure discussions | — |

---

## 4. Countries and Status

| Country | Counties/Regions | Status | National Avg LR (Std) | Avg Premium |
|---------|-----------------|--------|----------------------|-------------|
| **Romania** | 42 județe | Complete (35yr) + area pricing | 6.1% | EUR 5.81/ha |
| **Moldova** | 29 raioane | Complete (35yr) | 8.1% | EUR 7.75/ha |
| **Poland** | 16 voivodeships | Complete (35yr) | 4.8% | EUR 4.59/ha |
| **Hungary** | 19 counties | Complete (35yr) | 8.1% | EUR 7.82/ha |
| **Czech Republic** | 14 kraje | Complete (35yr) | 0.4% | EUR 0.37/ha |
| **Slovakia** | 8 kraje | Complete (35yr) + area mapping | 0.7% | EUR 0.70/ha |

**Ukraine** was in the original country list but deprioritized (no Corteva sales data yet).

---

## 5. Data Sources

### ERA5-Land Reanalysis (primary)
- **Provider**: Copernicus Climate Data Store (CDS), ECMWF
- **Resolution**: 0.1° (~9 km), hourly → aggregated to daily
- **Period**: 1990–2024 (35 crop years), with 2025 processing in progress
- **Variables**:
  - `swvl1` — Soil moisture, layer 1 (0–7 cm) → drought index
  - `2m_temperature` — Daily Tmin → frost index
  - `total_precipitation` — Crust formation trigger
  - `snow_depth_water_equivalent` — Snow protection for frost

### Marsh Romania Claims Data (calibration)
- **Source**: Marsh/Vara Ag, provided during Jul–Nov 2025 pricing discussions
- **Content**: Romania WOSR portfolio long-term loss ratio: **8.4%** at approximately 10 drought days
- **Use**: Calibration anchor for the sigmoid ELF model (CF = 0.3589)
- **GDrive references**: `Frontera Ag | Corn, WOSR and Sunflower Historical Payouts Exercise 2020-2024 | Romania V5 Final`, `Final Model | Frontera | Marsh Romania WOSR 18.08.2025 V5`

### Corteva Sales Data
- **Romania WOSR**: `WOSR sales 2025.xlsx` — 10 Areas, 77,787 total bags
- **Romania Area→County mapping**: `2026 Lumiposa corn.xlsx` — 10 Areas mapped to 41 counties (same areas for corn and WOSR)
- **Slovakia WOSR**: GDrive `Frontera X _ Corteva SK Template _ WOSR Sales Data 2025` — 8 Areas mapped to 72 districts
- **Hungary**: Seed bag data pending from Corteva HU country lead

### WOSR Claims Spreadsheet
- **URL**: https://docs.google.com/spreadsheets/d/1rDgY_ObppGBQZYTa4K-dVNhWohlcXBl9/edit
- **Content**: Historical WOSR claims/loss data used in early methodology design

---

## 6. Methodology

### Overview

For each county and crop year, the model computes a **loss ratio** (expected payout as % of sum insured) based on climate conditions during two windows:

- **Autumn (Aug–Oct)**: Drought stress during sowing/emergence → primary peril
- **Winter (Dec–Feb)**: Frost kill of established plants → secondary peril (Full Package only)

### Peril Model

#### A. Autumn Drought Index
```
I_drought = count of days in Aug 20 – Oct 20 where swvl1 < 0.15 m³/m³
```
Dry topsoil prevents seed germination and seedling establishment.

#### B. Emergence Loss Factor (sigmoid)
```
ELF(d) = 1 / (1 + exp(-K × (d - X0)))

K  = 0.35    (steepness)
X0 = 13.39   (midpoint — 50% loss at ~13 drought days)
```
A few dry days → negligible impact. Beyond ~10 days → losses accelerate rapidly.

#### C. Calibration
```
LR_standard = ELF(d) × CF

CF = 0.3589  (calibrated so ELF(10) × CF = 8.4% = Marsh Romania LR)
```

#### D. Soil Crust Loading (+1.5%)
Applied when:
- County clay content > 30%, AND
- Heavy rain (>30mm in 48h) within 5–20 days post-sowing

Clay soils form a hard crust that physically blocks seedlings.

#### E. Winter Frost Index
```
I_frost = count of days in Dec 1 – Feb 28 where:
  - Tmin < -12°C, AND
  - Snow water equivalent < 10mm (no insulating cover)
```

#### F. Catastrophic Frost
Triggered when Tmin < -18°C with bare/thin soil cover → adds full winter loading.

### Packages

| Package | Formula | Covers |
|---------|---------|--------|
| **Standard** | `ELF × CF + crust_loading` | Autumn emergence only |
| **Full** | `Standard + LR_winter + 5% base` | Emergence + winter frost + base loading |

### Pricing

```
LR_pricing = 60% × LR_5yr_avg + 40% × LR_35yr_avg   (blend recent + long-term)
Premium    = LR_pricing × EUR 96/ha × 1.30             (sum insured × loading)
```

- **EUR 96/ha**: Standard WOSR seed bag replacement value
- **1.30**: 30% commercial loading (expenses, brokerage, risk margin)
- **60/40 blend**: Overweights recent climate (increasing drought trend)

---

## 7. Commercial Structure

Based on the Frontera X & Corteva Agreement Process document (Nov 2025):

- **Program fee**: EUR/USD 450,000 (2026 season, Romania corn — WOSR TBD)
- **Broader structure**: EUR 1,700,000 (Option A — validated approach)
- **Corteva's role**: Bundles guarantee into seed price, delivers in-kind farmer benefits
- **DigiFarm's role**: Validates claims via FARM platform, provides analytics
- **Reinsurance**: Descartes Underwriting provides capacity; Corteva as beneficiary
- **Regulatory**: Structured as parametric guarantee (non-insurance) to avoid regulatory classification
- **Liability cap**: DigiFarm capped at EUR 1,700,000 per season

### Premium Flow (WOSR Romania, estimated)

From the area-level pricing analysis:

| Area | WOSR Bags | Est. Ha | Avg LR | Premium EUR/ha | Area Premium |
|------|-----------|---------|--------|---------------|-------------|
| Area 1 | 11,549 | 32,997 | 18.4% | EUR 22.97 | EUR 757,926 |
| Area 2 | 12,865 | 36,757 | 14.0% | EUR 17.43 | EUR 640,845 |
| Area 3 | 5,544 | 15,840 | 2.2% | EUR 2.72 | EUR 43,046 |
| Area 4 | 22,594 | 64,554 | 8.4% | EUR 10.45 | EUR 674,856 |
| Area 5 | 5,678 | 16,223 | 9.7% | EUR 12.07 | EUR 195,740 |
| Area 6 | 2,585 | 7,386 | 2.7% | EUR 3.34 | EUR 24,680 |
| Area T | 2,192 | 6,263 | 1.0% | EUR 1.27 | EUR 7,943 |
| Area 8 | 2,653 | 7,580 | 3.3% | EUR 4.07 | EUR 30,815 |
| Area 10 | 7,364 | 21,040 | 10.4% | EUR 13.01 | EUR 273,739 |
| Area 11 | 4,763 | 13,609 | 1.0% | EUR 1.24 | EUR 16,870 |
| **TOTAL** | **77,787** | **222,249** | — | **EUR 12.00** | **EUR 2,666,458** |

**Risk concentration**: Areas 1 + 2 (Ialomița/Călărași + Buzău/Brăila/Galați — Wallachian Plain) account for 52% of total premium but only 31% of hectares.

---

## 8. Risk Zones

### Romania

| Zone | Counties | Characteristics | Avg LR |
|------|----------|----------------|--------|
| **Z1** | 17 (south/east) | Wallachian Plain + Moldovan Plateau — hot, drought-exposed, clay-heavy soils | High |
| **Z2** | 11 (west/central) | Transylvania foothills, Banat — moderate rainfall, mixed soils | Moderate |
| **Z3** | 14 (north/mountains) | Carpathian + northern counties — cooler, wetter, lower drought risk | Low |

### Key Loss Years (Romania)
- **2011**: 16.0% national LR — severe autumn drought, worst in 35yr record
- **2019**: 16.6% national LR — concentrated in southern plains
- **2012**: 13.8% national LR
- **2023**: 9.8% national LR
- **2024**: 9.3% national LR
- **2003**: 8.4% national LR — calibration anchor year

---

## 9. Deliverables Produced

### Data & Analysis
| Deliverable | Location |
|-------------|----------|
| 210 county-year CSV results (6 countries × 35 years) | `s3://digifarm-wosr-underwriting/results/` and `results/` |
| Country summary CSVs | `analysis/<CC>_summary.csv` |
| Full cross-country analysis report | `analysis/WOSR_Results_Report.md` |
| County-level pricing CSVs (all 6 countries) | `pricing/<CC>_county_pricing.csv` |
| RO area-level pricing (Corteva Areas) | `pricing/RO_area_pricing.csv` |
| Area pricing report | `pricing/RO_Area_Pricing_Report.md` |
| Corteva pricing package | `pricing/WOSR_Corteva_Pricing_Package.md` |

### Google Sheets (per-country, 35yr data)
| Country | Sheet URL |
|---------|-----------|
| Romania | https://docs.google.com/spreadsheets/d/1zH7IyXpe1bJ0uVTp-LlsCZGife7oGBTmrjIBFSg49ZE |
| Moldova | https://docs.google.com/spreadsheets/d/1Q97jhCifTnKgIBdS0JnFG2WDDgnQp9jhvufBnrgtor0 |
| Poland | https://docs.google.com/spreadsheets/d/1leg8Sk0TXLWR6CuIHAcUzPto5WaTrGFniJXa5e0c-HY |
| Hungary | https://docs.google.com/spreadsheets/d/14uMCMNFMv9BbyGKrsmkKh-xtvOXkFpx21J83ibuS4Uo |
| Czech Republic | https://docs.google.com/spreadsheets/d/10MXzYGRRENUvjjY9L0hSLzB_G54GXGer1bfUmBR_m0Q |
| Slovakia | https://docs.google.com/spreadsheets/d/1aNfh2HOQzkN6M8MHAqQJ-VXyDBDE7Fky51vrI-_2O_o |

GDrive folder: https://drive.google.com/drive/folders/1_lxwoAFUrmV7yEWQ2HS0tlomVgpKpFFR

### Methodology Documents (GDrive)
| Document | URL |
|----------|-----|
| Romania Methodology v1.1 | https://docs.google.com/document/d/1OE9yWdKWaSOiTJs_8svptg-0jmegnvSkI49VJkg2gFY |
| All Countries Methodology v1.1 | https://docs.google.com/document/d/1xiDZBxmNkxX9v8_UVi5yUAsVBwHOPaxG0qoYtks7C6g |
| Romania Methodology (repo) | https://github.com/digifarmio/wosr/blob/main/docs/WOSR_Romania_Methodology.md |

### Interactive Demo
- **URL**: http://wosr.demos.digifarm.tools/?token=TqH8k66T1hTUi4GT
- 6-country tabs, year slider, sortable LR table with heat colors, Chart.js trends

---

## 10. Code Repository

**GitHub**: https://github.com/digifarmio/wosr (private, `digifarmio` org)

### Scripts
| Script | Purpose |
|--------|---------|
| `wosr_era5_fetch.py` | Download ERA5-Land from CDS per country/year (autumn + winter windows) |
| `wosr_loss_calc.py` | Compute county-level loss ratios from ERA5 NetCDF (sigmoid ELF + frost + crust) |
| `wosr_aggregate.py` | Aggregate per-year CSVs into country summaries |
| `wosr_corteva_pricing.py` | Generate commercial pricing tables and reports |
| `wosr_area_pricing.py` | Map county pricing to Corteva sales Areas (RO) |
| `wosr_finalize.sh` | Sync S3 → run analysis → upload summaries |

### HPC (SLURM)
| Script | Cluster | Purpose |
|--------|---------|---------|
| `wosr_betzy_country.sbatch` | Betzy | Per-country job, years 1995–2024 |
| `wosr_betzy_extension.sbatch` | Betzy | Extension years 1990–1994 |
| `wosr_betzy_2025.sbatch` | Betzy | Year 2025 processing (submitted 2026-03-24) |
| `wosr_saga_country.sbatch` | Saga | Per-country job (quota exhausted — do not use) |

### Infrastructure
- **S3 bucket**: `s3://digifarm-wosr-underwriting/` (results, summaries)
- **Demo bucket**: `s3://wosr.demos.digifarm.tools/`
- **HPC account**: `nn12037k` (Sigma2/NRIS)
- **Saga**: Quota exhausted (604K/600K CPU hours)
- **Betzy**: Active — `preproc` partition, 4 CPU / 16G RAM per job

---

## 11. Key Decisions and Assumptions

| Decision | Rationale |
|----------|-----------|
| Sigmoid ELF (not linear) | Better models agronomic reality: few dry days → low impact, >10 days → rapid escalation |
| CF calibrated to Marsh Romania only | Only market with real claims data; other countries use same CF (conservative) |
| 60/40 blend (5yr/35yr) | Recent climate trends show increasing drought; pure 35yr average would underweight this |
| EUR 96/ha sum insured | Standard WOSR seed bag replacement value (from Corteva/Frontera) |
| 30% commercial loading | Covers expenses, brokerage, risk margin — standard for parametric products |
| County centroids (not field-level) | Pricing is portfolio-level, not per-field; field-level is handled by the Docker emergence detection model |
| 0.15 m³/m³ soil moisture threshold | Below this level, WOSR germination is severely impaired (agronomic literature) |
| -12°C frost threshold (with no snow) | Unprotected WOSR plants suffer significant frost damage below this (WOSR cold tolerance literature) |
| -18°C catastrophic threshold | Near-total winter kill without snow cover |

---

## 12. Two Complementary Models

It is important to understand that DigiFarm operates **two separate models** for the emergence guarantee:

| | Historical Loss Model (this project) | Field-Level Emergence Detection |
|---|---|---|
| **Purpose** | Pricing, underwriting, reinsurance | Claims validation, payout triggering |
| **Method** | ERA5-Land climate reanalysis → sigmoid loss function | Sentinel-2 satellite imagery → ML emergence classification |
| **Spatial unit** | County (centroid) | Individual field |
| **Time horizon** | 35 years historical (1990–2024) | Current season, near-real-time |
| **Output** | Loss ratio (%), premium (EUR/ha) | Binary: emerged / not emerged |
| **Platform** | Python scripts + HPC | Docker container (Descartes-reviewed) |
| **Validation** | Marsh Romania claims data | Ground truth from field inspections |

Descartes has been reviewing the Docker field-level model for production readiness. The correspondence about "data mismatch" (Feb 2025) was about the difference between these two models — they are complementary, not contradictory.

### Field-Level Emergence Validation Data (Lithuania)

A working example of the field-level emergence detection system exists for Lithuania:
- **File**: `digifarm emergence 2025 laukai.xls` ([GDrive](https://docs.google.com/spreadsheets/d/1QmMS7kPP-ptBzP-hMJTgXqFlc4nqWV_Q/edit))
- **Content**: 61 fields (476.9 ha) with emergence detection dates for 2023, 2024, 2025
- **Crop types**: Winter rapeseed (RAŽ), winter wheat (KVŽ), peas (ŽIR), beans (PUP), feed grains (PDJ), cruciferous (KRŽ), spring wheat (KVV)
- **Data source**: NMA (Lithuanian National Paying Agency) field registry + DigiFarm satellite emergence detection
- **Relevance**: Demonstrates the field-level emergence detection capability in production — the same system that validates claims for the WOSR guarantee

This dataset is also relevant to the **sure2** (satellite assessment) and **tillage** (field monitoring) projects.

---

## 13. Reference Product: Mariflor Full Crop Cover Program

A reference product structure from Mariflor ([GDrive presentation](https://docs.google.com/presentation/d/1waLWyb2OjyEJ2n1TNJ6UDkcBY0AUYr2D/edit)) shows how emergence fits within a broader crop insurance program:

| Component | Coverage | Verification Method |
|-----------|----------|-------------------|
| **Emergence** | Corn: EUR 250–350/ha | NDVI Satellite |
| **Revenue** | Full loss: -1000 EUR/ha | — |
| **Additional Harvest Costs** | 80% of amount per index | — |
| **Reseed** | EUR 250/ha | Photos |
| **Crop Abandonment** | — | Photos + cooperative verification |

Key program terms:
- Overall insured limit = 50% of committed capital
- In case of refusal, no revenue coverage
- 2 premium payments: 30% in April, 70% in October

This is relevant as a **reference architecture** for how emergence guarantees can be packaged as part of a broader crop cover program — our WOSR emergence guarantee is currently standalone, but could eventually be bundled similarly.

---

## 14. Reinsurance and Partner Validation

### Marsh (broker)
- Provided Romania WOSR claims data (2020–2024) for calibration
- Conducted pricing exercises (Aug–Nov 2025)
- Introduced Munich Re as potential reinsurer
- Key contact: Horatiu Udroiu (Vara Ag / Marsh Romania)
- GDrive: `Final Model | Frontera | Marsh Romania WOSR 18.08.2025 V5`

### Descartes Underwriting (validation)
- Reviewing Docker field-level emergence model for production
- Validating historical loss methodology
- Providing underwriting capacity for the program
- Key contacts: Antoine, Etienne Selles (etienne.selles@descartesunderwriting.com)
- Pending: Updated correspondence with 35yr results (email draft exists)

### Munich Re / Hannover Re
- Referenced in agreement process documents as potential reinsurers
- No active engagement on WOSR specifically (corn program context)

---

## 15. Pending Actions

### Immediate
1. **Share demo + docs with Nils** — demo link + methodology v1.1 GDocs
2. **Send Matti email** — update draft from 30yr/3 countries to 35yr/all 6 countries + area pricing
3. **2025 data processing** — 6 Betzy jobs submitted (IDs 1469797–1469802), will extend to 36yr

### Short-term
4. **SK area pricing** — Apply same mapping logic using SK seed bag data (just received from Nils)
5. **HU seed bags** — Waiting for data from Corteva Hungary country lead
6. **Descartes email** — Send updated results with 35yr data
7. **Update GSheets** — Add 2025 data once Betzy jobs complete

### Medium-term
8. **Corn ERA5 methodology** — Same pipeline adapted for corn (different sowing window, calibration)
9. **Sunflower** — Syngenta yield insurance for Romania (separate project, meeting next Monday)
10. **Country-specific CF calibration** — If non-RO claims data becomes available, improve accuracy

---

## 16. Key Reference Documents

### In This Repository
| File | Purpose |
|------|---------|
| `CONTEXT.md` | Original task briefing with Nils's Slack messages |
| `PROJECT_STATUS.md` | Living status tracker with all results and links |
| `docs/WOSR_Romania_Methodology.md` | Technical methodology for Romania |
| `docs/WOSR_Project_Definition.md` | This document |
| `pricing/WOSR_Corteva_Pricing_Package.md` | Client-facing pricing package |
| `pricing/RO_Area_Pricing_Report.md` | Corteva Area-level pricing |

### On Google Drive
| Document | Content |
|----------|---------|
| [WOSR claims data spreadsheet](https://docs.google.com/spreadsheets/d/1rDgY_ObppGBQZYTa4K-dVNhWohlcXBl9/edit) | Historical WOSR claims |
| [Definitive Actuarial Methodology (2026-01-19)](https://docs.google.com/document/d/...) | Corn methodology template that WOSR was adapted from |
| [FARM Replanting Insurance Spec (2025-10-21)](https://docs.google.com/document/d/...) | Technical specification for the FARM platform |
| [Frontera X & Corteva Agreement Process](https://docs.google.com/document/d/1adArxM-WN9uUGzFGHrPpocmbwN5bPzwgtEFRCyQv7tc/edit) | EUR 1.7M program structure |
| [Mariflor Full Crop Cover Program](https://docs.google.com/presentation/d/1waLWyb2OjyEJ2n1TNJ6UDkcBY0AUYr2D/edit) | Reference product structure: emergence + revenue + reseed + crop abandonment |
| [Lithuania Emergence Detection 2025](https://docs.google.com/spreadsheets/d/1QmMS7kPP-ptBzP-hMJTgXqFlc4nqWV_Q/edit) | Field-level emergence data: 61 fields, 476.9 ha, 2023–2025 (also relevant to sure2/tillage) |
| [Corteva SK WOSR Sales 2025](https://docs.google.com/spreadsheets/d/1VUOWhKx8B44tABiCQotu08fShzLtXqualcsowZP4MjE/edit) | Slovakia Area→district mapping + WOSR sales data |

### External Knowledge Base
| File | Content |
|------|---------|
| `/home/ubuntu/dpro/data/gdrive/profiles/clients/corteva.md` | Full Corteva document inventory |
| `/home/ubuntu/dpro/data/gdrive/profiles/clients/frontera.md` | Full Frontera document inventory |
| `/home/ubuntu/dpro/data/gdrive/profiles/clients/marsh.md` | All Marsh meeting notes and docs |
| `/home/ubuntu/dpro/data/gdrive/profiles/contracts/frontera-x-corteva-agreement-process.md` | Contract structure analysis |

---

*Last updated: 2026-03-24 | DigiFarm AS*

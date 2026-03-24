# WOSR Emergence Guarantee — Romania

## Project Overview

DigiFarm is building a **parametric climate insurance** product for Winter Oilseed Rape (WOSR) emergence risk. The product is designed for **Corteva Agriscience** seed sales across Central and Eastern Europe, brokered through **Frontera Ag** and reinsured by **Descartes Underwriting**.

The core idea: when a farmer buys Corteva WOSR seed, an emergence guarantee is bundled into the seed bag price. If climate conditions during the critical sowing/emergence window cause poor establishment (<20 plants/m²), the farmer receives an automatic payout — no field inspection needed.

**Countries covered:** Romania (RO), Moldova (MD), Poland (PL), Hungary (HU), Czech Republic (CZ), Slovakia (SK).

### Romania — Why It Matters

Romania is the **anchor market**: largest WOSR acreage in the portfolio, highest climate risk variability, and the only country with historical claims data (Marsh Romania portfolio) for model calibration. Romania pricing is validated; other countries are priced relative to the Romanian calibration.

---

## Data Source

**ERA5-Land reanalysis** from the Copernicus Climate Data Store (CDS), at 0.1° (~9 km) resolution, hourly timesteps aggregated to daily.

Variables used:
- `swvl1` — Volumetric soil water content, layer 1 (0–7 cm)
- `2m_temperature` — Air temperature at 2 metres (for daily Tmin)
- `total_precipitation` — Daily accumulated precipitation
- `snow_depth_water_equivalent` — Snow cover (SWE, kg/m²)

**Period:** 35 years, 1990–2024 (crop years).

**Spatial units:** 42 Romanian counties (județe), each represented by its centroid coordinate.

---

## Methodology

The model computes a **loss ratio** (expected payout as % of sum insured) for each county and year, based on three climate perils:

### 1. Autumn Drought Index (I_drought)

Counts the number of days in the **sowing/emergence window** (Aug 20 – Oct 20) where topsoil moisture drops below a critical threshold:

```
I_drought = count of days where swvl1 < 0.15 m³/m³
```

Dry topsoil during this window prevents seed germination and seedling establishment — the primary cause of emergence failure.

### 2. Emergence Loss Factor (ELF) — Sigmoid Model

The drought day count is converted to a continuous loss factor using a **sigmoid function**:

```
ELF(d) = 1 / (1 + exp(-K × (d - X0)))
```

| Parameter | Value | Meaning |
|-----------|-------|---------|
| K | 0.35 | Steepness of the loss curve |
| X0 | 13.39 | Midpoint — 50% loss at ~13 drought days |

This reflects the agronomic reality: a few dry days have minimal impact, but once drought days exceed ~10, emergence losses accelerate rapidly.

### 3. Calibration Factor (CF)

The raw ELF is scaled to match observed claims experience:

```
LR_standard = ELF(d) × CF
```

**CF = 0.3589**, calibrated so that:
- At 10 drought days → ELF(10) = 0.234 → LR = **8.4%**
- This matches the **Marsh Romania portfolio** long-term loss ratio of 8.4%

### 4. Soil Crust Loading (+1.5%)

For counties with **clay content > 30%**, if heavy rain (>30 mm in 48h) falls in the 5–20 days after sowing, a +1.5% crust loading is added. Clay soils form a hard surface crust that physically blocks seedling emergence.

### 5. Winter Frost Index (I_frost)

Counts days in **Dec 1 – Feb 28** where:
- Daily minimum temperature < -12°C, AND
- Snow cover (SWE) < 10 mm (no insulating snow blanket)

Exposed WOSR plants without snow cover are vulnerable to frost kill.

### 6. Catastrophic Frost Flag

Triggered when **Tmin < -18°C** on any day in Dec–Feb with bare/thin soil cover. Adds the full winter frost loading to the loss ratio.

### 7. Loss Ratio Packages

| Package | Formula | What It Covers |
|---------|---------|----------------|
| **Standard** | `LR_standard = ELF × CF + crust_loading` | Autumn emergence risk only |
| **Full** | `LR_full = LR_standard + LR_winter + 5%` | Emergence + winter frost + base loading |

### 8. Pricing Blend

Final pricing uses a **weighted blend** of recent and long-term loss experience:

```
LR_pricing = 60% × LR_5yr_avg + 40% × LR_35yr_avg
```

This overweights recent climate trends (which show increasing drought frequency) while retaining long-term statistical stability.

### 9. Commercial Premium

```
Premium (€/ha) = LR_pricing × €96 × 1.30
```

- **€96/ha**: sum insured (standard WOSR seed bag replacement value)
- **1.30**: 30% commercial loading (expenses, brokerage, risk margin)

---

## GSheet Column Definitions

**Sheet:** [WOSR ERA5 35yr Historical Losses - Romania](https://docs.google.com/spreadsheets/d/1zH7IyXpe1bJ0uVTp-LlsCZGife7oGBTmrjIBFSg49ZE)

The sheet contains **1,470 rows** (42 counties × 35 years) with these columns:

| Column | Description |
|--------|-------------|
| **Country** | `RO` |
| **County** | Romanian county name (județ) |
| **Year** | Crop year (1990–2024). "2020" means autumn 2020 sowing + winter 2020/21 |
| **Loss Ratio Standard (%)** | Drought-only loss ratio. This is the main pricing metric |
| **Loss Ratio Full Package (%)** | Standard + winter frost + 5% base loading |
| **Risk Zone** | Z1 (south/east, high risk), Z2 (west, moderate), Z3 (north/mountains, low) |
| **Drought Days** | Count of days with swvl1 < 0.15 in Aug 20 – Oct 20 window |
| **Frost Days** | Count of unprotected frost days (Tmin < -12°C, low snow) in Dec–Feb |
| **Frost Catastrophic** | 1 if any day had Tmin < -18°C with bare soil, else 0 |
| **ELF Raw** | Raw sigmoid output before calibration (0–1 scale) |

### How to Read the Numbers

- **LR Standard 0%** = no drought stress that year — good emergence expected
- **LR Standard 5–10%** = moderate drought — some replanting likely
- **LR Standard >20%** = severe drought — widespread emergence failure (e.g., 2011, 2019)
- **Drought Days 0–5** = normal conditions
- **Drought Days 10+** = significant dry spell during sowing window
- **Frost Catastrophic = 1** = extreme cold event without snow cover (rare but severe)

---

## Romania Key Results (35 Years, 1990–2024)

| Metric | Value |
|--------|-------|
| National avg LR (Standard) | 6.1% |
| National avg LR (Full Package) | 10.4% |
| National avg premium | €5.81/ha |
| Highest-risk county | Calarasi (26.1% LR, €25.04/ha) |
| Lowest-risk counties | Constanta, Botosani, Bistrita-Nasaud (~0.4% LR, €0.36/ha) |
| Worst national year | 2011 (16.0% national mean LR) |
| Major loss years | 2011, 2019, 2012, 2023, 2024, 2008, 2009 |

### Risk Zones

| Zone | Counties | Avg LR | Description |
|------|----------|--------|-------------|
| Z1 | 17 (south/east) | High | Wallachian Plain + Moldovan Plateau — drought-exposed |
| Z2 | 11 (west/central) | Moderate | Transylvania foothills + Banat |
| Z3 | 14 (north/mountains) | Low | Carpathian + northern counties — cooler, wetter |

---

## Validation

The model is calibrated against the **Marsh Romania** WOSR portfolio, which reported a long-term loss ratio of **8.4%** at approximately 10 drought days. Our sigmoid model reproduces this exactly: ELF(10) × CF = 0.234 × 0.3589 = 8.4%.

Cross-validation against known bad years:
- **2003**: severe summer drought across southern Romania — model produces 8.4% national LR with Dolj at 35.4%
- **2011**: worst year in 35yr record — model shows 16.0% national LR, concentrated in Braila/Calarasi/Galati
- **2019**: second-worst — 16.6% national LR, again southern plains

---

## Next Steps

1. **2025 crop year processing** — ERA5 data for autumn 2025 + winter 2025/26 is now available. Jobs submitted to Betzy HPC to extend the dataset to 36 years.
2. **Corteva Area mapping** — Map Corteva's sales Areas to Romanian counties for portfolio-level premium calculation (same mapping as corn program).
3. **Matti/Corteva pricing package** — Updated 35yr pricing for all 6 countries ready to share.
4. **Descartes review** — County-level tables shared with reinsurance partner for validation.
5. **Corn + sunflower extension** — Same ERA5 methodology adapted for other crop emergence guarantees (different sowing windows and calibration parameters).

---

## Code Repository

Source code: [github.com/digifarmio/wosr](https://github.com/digifarmio/wosr)

| Script | Purpose |
|--------|---------|
| `wosr_era5_fetch.py` | Download ERA5-Land data from CDS for each country/year |
| `wosr_loss_calc.py` | Compute county-level loss ratios from ERA5 NetCDF files |
| `wosr_aggregate.py` | Aggregate per-year CSVs into country summaries |
| `wosr_corteva_pricing.py` | Generate commercial pricing tables |

---

*Prepared by DigiFarm AS, March 2026*

# WOSR Underwriting Pipeline — Project Status

**Last updated:** 2026-03-23
**Meeting:** Descartes/Corteva call at 3 PM CET 2026-03-11 (completed)

---

## Pipeline Summary

Climate-based emergence guarantee pricing for Winter Oilseed Rape (WOSR) across Romania + 5 CEE countries (MD, PL, HU, CZ, SK). **35-year** historical ERA5-Land analysis (1990–2024), calibrated against Marsh Romania portfolio LR of 8.4% at 10 drought days.

**Key methodology:** Sigmoid ELF model → drought index → calibrated loss ratio, with winter frost, crust, and catastrophe loadings.

---

## Code Status: Production-Ready (v1 Pilot)

| Fix | File | Commit |
|-----|------|--------|
| Sigmoid recalibration: ELF_X0 10.0 → 13.39 | wosr_loss_calc.py:222 | 70f105d |
| Catastrophic frost: added bare-soil condition | wosr_loss_calc.py:329 | 70f105d |
| Crust loading: +1.5% when crust_flag=1 | wosr_loss_calc.py:349 | 70f105d |
| Crust window: uses actual sowing_doy | wosr_loss_calc.py:290 | 70f105d |
| ERA5 year range: 1995→1940 lower bound | wosr_era5_fetch.py:98 | Morris (Mar 2026) |

---

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| ELF_K | 0.35 | Sigmoid steepness |
| ELF_X0 | 13.39 | Calibrated midpoint (was 10.0 — critical fix) |
| CF | 0.3589 | Marsh-calibrated: ELF(10)=0.234 → LR=8.4% |
| Sum insured | €96/ha | Corteva seed bag value |
| Commercial loading | 1.30× | 30% margin |
| Pricing blend | 60% 5yr + 40% 35yr | Weighted LR for premium |
| Historical window | 1990–2024 (35 years) | Extended from 30yr per Nils request |

---

## S3 Results (as of 2026-03-23)

**Bucket:** `s3://digifarm-wosr-underwriting/results/<COUNTRY>/`

**Total: 210 CSV files — ALL 6 COUNTRIES COMPLETE**

| Country | Years | Status | Nat. Avg LR (Std) | Nat. Avg LR (Full) | Avg Premium |
|---------|-------|--------|-------------------|---------------------|-------------|
| RO | 1990–2024 (35/35) | ✅ Complete | 6.1% | 10.4% | €5.81/ha |
| MD | 1990–2024 (35/35) | ✅ Complete | 8.1% | 10.4% | €7.75/ha |
| PL | 1990–2024 (35/35) | ✅ Complete | 4.8% | 10.4% | €4.59/ha |
| HU | 1990–2024 (35/35) | ✅ Complete | 8.1% | 12.2% | €7.82/ha |
| CZ | 1990–2024 (35/35) | ✅ Complete | 0.4% | 5.7% | €0.37/ha |
| SK | 1990–2024 (35/35) | ✅ Complete | 0.7% | 6.2% | €0.70/ha |

---

## HPC Status

- **Saga (nn12037k):** Billing quota exhausted (604,821/600,000 CPU hours used). Do not use.
- **Betzy (nn12037k):** Used by Morris to complete HU/CZ/SK and 1990-1994 extension. ~253K hours available when Morris started; check remaining quota before submitting new jobs.
- **SSH:** `ssh betzy-long` (OTP required)
- **Scripts on Betzy:** `/cluster/work/users/digifarm/wosr/scripts/wosr_betzy_country.sbatch` (1995-2024), `wosr_betzy_extension.sbatch` (1990-1994)

---

## Google Sheets (per Nils's request, Mar 23)

All 6 countries uploaded to GDrive country subfolders. Main folder: https://drive.google.com/drive/folders/1_lxwoAFUrmV7yEWQ2HS0tlomVgpKpFFR

| Country | Sheet ID |
|---------|----------|
| Romania | 1zH7IyXpe1bJ0uVTp-LlsCZGife7oGBTmrjIBFSg49ZE |
| Moldova | 1Q97jhCifTnKgIBdS0JnFG2WDDgnQp9jhvufBnrgtor0 |
| Poland | 1leg8Sk0TXLWR6CuIHAcUzPto5WaTrGFniJXa5e0c-HY |
| Hungary | 14uMCMNFMv9BbyGKrsmkKh-xtvOXkFpx21J83ibuS4Uo |
| Czech Republic | 10MXzYGRRENUvjjY9L0hSLzB_G54GXGer1bfUmBR_m0Q |
| Slovakia | 1aNfh2HOQzkN6M8MHAqQJ-VXyDBDE7Fky51vrI-_2O_o |

Format: Country, County, Year, LR Standard (%), LR Full Package (%), Risk Zone, Drought Days, Frost Days, Frost Catastrophic, ELF Raw. Compiled per-county per-year, 1990–2024.

---

## Syncing & Running Analysis

```bash
cd /home/ubuntu/wosr
aws s3 sync s3://digifarm-wosr-underwriting/results/ results/ --quiet
python3 scripts/wosr_aggregate.py --all --results-dir results/ --output-dir analysis/
python3 scripts/wosr_analyze_results.py --results-dir results/ --output-dir analysis/
python3 scripts/wosr_corteva_pricing.py --all
git add results/ analysis/ pricing/
git commit -m "Update results/analysis/pricing"
git push
```

---

## Corteva Sales Data (pending integration)

File: `WOSR sales 2025.xlsx` — ~78K bags by Area (1,2,3,4,5,6,T,8,10,11).
**Contact for mapping:** Alexandra Gheorghe at Corteva (identified by Morris).
**Blocker:** Area→county mapping still needed. Nils has it (same as corn areas).

---

## Pending Actions (priority order)

1. **Send follow-up to Etienne (Descartes)** — update with 1K corn backtest: avg CR 7.6% vs Excel 6.6% (+1.0%). Draft exists in Gmail (Re: Satellite Claim Rate vs Excel Loss Ratio). Descartes deliverable target: Mar 25-28.
2. **Send Matti email** — 35yr preliminary pricing for all 6 countries. Gmail draft ready.
3. **Get Area→county mapping** — from Nils or Alexandra Gheorghe at Corteva.
4. **Finalize Descartes deliverables package** (target Mar 25-28): county LR tables, risk zones, premiums, methodology notes.
5. **Corn/sunflower ERA5 methodology** — Nils wants same pipeline for corn/sunflower. Needs crop-specific calibration (Konstantin to design).

---

## Outreach Log

| Recipient | Channel | Subject | Status | Date |
|-----------|---------|---------|--------|------|
| Nils Helset | Slack DM | Area→county mapping | Sent | 2026-03-16 |
| Matti Tiainen | Gmail draft | WOSR 30yr pricing (RO/MD/PL) | **Draft — update to 35yr, then send** | 2026-03-16 |
| Sigma2 support | Gmail draft | Emergency quota request | **Moot — quota issue resolved via Betzy** | 2026-03-16 |
| Etienne Selles | Gmail draft | Re: Satellite Claim Rate vs Excel LR | **Draft — needs 1K result update, then send** | 2026-03-15 |

---

## Key Results (35yr)

| Country | Nat. Avg LR | Worst County | Worst LR | Key Loss Years |
|---------|------------|--------------|----------|----------------|
| RO | 6.1% | Călărași | ~26% | 2011, 2019, 2008-09 |
| MD | 8.1% | Taraclia | ~19% | 2017, 2023, 2011 |
| PL | 4.8% | Kuyavian-Pomeranian | ~18% | 2005, 2018 |
| HU | 8.1% | Bács-Kiskun | ~32% | TBD |
| CZ | 0.4% | (low risk) | ~2% | TBD |
| SK | 0.7% | (low risk) | ~3% | TBD |

---

## Contacts

| Person | Role | Contact |
|--------|------|---------|
| Nils Helset | DigiFarm CEO | Slack U8TCVUANL, DM: DE0159YCA |
| Matti Tiainen | Frontera Ag (client) | matti.tiainen@frontera.ag |
| Etienne Selles | Descartes (reinsurance) | etienne.selles@descartesunderwriting.com |
| Alexandra Gheorghe | Corteva | Area→county mapping contact |
| Horatiu Udroiu | Vara Ag / Marsh broker | horatiu@varaag.com |
| Konstantin Varik | DigiFarm CTO | project owner |

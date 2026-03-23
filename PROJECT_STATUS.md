# WOSR Underwriting Pipeline — Project Status

**Last updated:** 2026-03-23 (session 2)
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

| Country | Sheet ID | Status |
|---------|----------|--------|
| Romania | 1zH7IyXpe1bJ0uVTp-LlsCZGife7oGBTmrjIBFSg49ZE | ✅ Verified (42 counties × 35yr, data matches CSVs) |
| Moldova | 1Q97jhCifTnKgIBdS0JnFG2WDDgnQp9jhvufBnrgtor0 | ✅ Complete |
| Poland | 1leg8Sk0TXLWR6CuIHAcUzPto5WaTrGFniJXa5e0c-HY | ✅ Complete |
| Hungary | 14uMCMNFMv9BbyGKrsmkKh-xtvOXkFpx21J83ibuS4Uo | ✅ Complete |
| Czech Republic | 10MXzYGRRENUvjjY9L0hSLzB_G54GXGer1bfUmBR_m0Q | ✅ Complete |
| Slovakia | 1aNfh2HOQzkN6M8MHAqQJ-VXyDBDE7Fky51vrI-_2O_o | ✅ Complete |

Format: Country, County, Year, LR Standard (%), LR Full Package (%), Risk Zone, Drought Days, Frost Days, Frost Catastrophic, ELF Raw. Compiled per-county per-year, 1990–2024.

---

## Methodology Docs (v1.1, 23 March 2026)

Updated from 30yr (1995–2024) to 35yr (1990–2025). New docs in GDrive folder: https://drive.google.com/drive/folders/1doORGQUclYCwK9KE9anj8p8G0z3h7CLl

| Doc | GDoc ID |
|-----|---------|
| Romania v1.1 | 1OE9yWdKWaSOiTJs_8svptg-0jmegnvSkI49VJkg2gFY |
| All Countries v1.1 | 1xiDZBxmNkxX9v8_UVi5yUAsVBwHOPaxG0qoYtks7C6g |

Key changes: year range 1995→1990, "30-year"→"35-year", added ERA5 35yr national avg (6.1% std, 10.4% full for RO), updated summary table, added demo link.

---

## Interactive Demo

**S3:** `s3://wosr.demos.digifarm.tools/` (deployed 2026-03-23)
**URL:** http://wosr.demos.digifarm.tools.s3-website.eu-central-1.amazonaws.com/ ✅ working

**DNS pending:** Add Route53 CNAME: `wosr.demos.digifarm.tools` → `wosr.demos.digifarm.tools.s3-website.eu-central-1.amazonaws.com`
(Same pattern as tillage-demo.digifarm.tools — no CloudFront needed for MVP)

Features: 6-country tabs, year slider 1990–2024, sortable LR table with heat colors, Chart.js historical trend, Historical Average mode with P90 column.

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

1. **Add DNS record** — `wosr.demos.digifarm.tools` CNAME → `wosr.demos.digifarm.tools.s3-website.eu-central-1.amazonaws.com` in Route53 (need DNS access).
2. **Share new docs with Nils** — Romania v1.1 and All Countries v1.1 GDocs created 2026-03-23 (IDs above).
3. **Send Matti email** — 35yr preliminary pricing for all 6 countries. Gmail draft ready (update from 30yr RO/MD/PL to 35yr all 6).
4. **Get Area→county mapping** — from Nils or Alexandra Gheorghe at Corteva.
5. **Compute 2025 data** — run Betzy jobs for all 6 countries (year=2025) to extend to 36yr.
6. **HU seed bags** — waiting for data from Corteva HU country lead before pricing HU.
7. **Corn/sunflower ERA5 methodology** — Nils wants same pipeline. Needs crop-specific calibration (Konstantin to design).

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

# WOSR Project — Handoff for Morris

**Date:** 2026-03-12
**Project:** Winter Oilseed Rape (WOSR) Emergence Guarantee Underwriting
**Repo:** `digifarmio/wosr` at `/home/ubuntu/wosr/`
**Contact if stuck:** Nils Helset (Slack U8TCVUANL) or Konstantin

---

## What This Is

We're building a parametric climate insurance product for WOSR (rapeseed) across Romania + 5 CEE countries (Moldova, Poland, Hungary, Czech Republic, Slovakia). The model computes a drought index from ERA5-Land climate data and maps it to a loss ratio using a calibrated sigmoid function. Client is Corteva Agriscience / Frontera.

Read `CONTEXT.md` for full background, and `PROJECT_STATUS.md` for current state.

---

## Current State

**55 historical year-country CSVs computed** (out of ~180 needed for 30-year history):

| Country | Done | Still needed |
|---------|------|-------------|
| RO | 1995–2010 | 2011–2024 |
| CZ, HU, MD, PL | 1995–2002 | 2003–2024 |
| SK | 1995–2001 | 2002–2024 |

**5 SLURM jobs running on Saga** computing more years right now. They will expire (hit wall time) ~15:30–17:10 CET today.

---

## Your Main Job: Keep the Data Coming

The bottleneck is the Copernicus CDS API — it throttles to ~2 concurrent downloads, so each job only processes ~1–2 years per hour. Jobs expire before finishing. You need to resubmit them repeatedly until all years are done.

### Step 1 — Check job status
```bash
ssh saga "squeue -u digifarm"
```

### Step 2 — When a job is gone (expired or finished), resubmit it

```bash
# For country jobs (MD, PL, HU, CZ, SK) — do all 5:
scp /home/ubuntu/wosr/scripts/wosr_saga_country.sbatch digifarm@saga.sigma2.no:/cluster/work/users/digifarm/wosr/scripts/
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_MD scripts/wosr_saga_country.sbatch MD"
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_PL scripts/wosr_saga_country.sbatch PL"
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_HU scripts/wosr_saga_country.sbatch HU"
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_CZ scripts/wosr_saga_country.sbatch CZ"
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_SK scripts/wosr_saga_country.sbatch SK"

# For RO job:
scp /home/ubuntu/wosr/scripts/wosr_saga.sbatch digifarm@saga.sigma2.no:/cluster/work/users/digifarm/wosr/scripts/
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch scripts/wosr_saga.sbatch"
```

**The scripts automatically skip years already in S3** — so resubmitting is always safe, no duplicates.

### Step 3 — Sync new results, commit, push

After jobs produce new files (check S3 count going up), run this on the server:

```bash
cd /home/ubuntu/wosr

# Sync from S3
aws s3 sync s3://digifarm-wosr-underwriting/results/ results/ --quiet

# Run aggregation + analysis
python3 scripts/wosr_aggregate.py --all
python3 scripts/wosr_analyze_results.py

# Commit new results
git add results/ analysis/
git commit -m "Add <COUNTRY> results through <YEAR>, update analysis"
git push
```

Or just run the all-in-one script:
```bash
bash /home/ubuntu/wosr/scripts/wosr_finalize.sh
```

### How to check S3 progress
```bash
aws s3 ls s3://digifarm-wosr-underwriting/results/ --recursive | grep "\.csv" | wc -l
# Should go up from 55 toward ~180
```

---

## When All 30 Years Are Done

Once S3 has all ~180 CSVs (RO: 30, others: 30 each):

```bash
bash /home/ubuntu/wosr/scripts/wosr_finalize.sh
python3 scripts/wosr_corteva_pricing.py --all
```

This generates the final county-level pricing package in `pricing/`.

---

## Pending: Corteva Sales Data Integration

File `WOSR sales 2025.xlsx` has Corteva Romania seed bag sales by "Area" (their internal territory names). We need the **Area → Romanian county mapping** to use these as exposure weights in pricing.

**Ask Nils** (Slack U8TCVUANL) for the mapping. He mentioned this on 2026-03-12. Once you have it, add a mapping dict to `scripts/wosr_corteva_pricing.py` (look for the county weighting section).

---

## Key Files

| File | What it is |
|------|-----------|
| `scripts/wosr_saga_country.sbatch` | Per-country SLURM job script |
| `scripts/wosr_saga.sbatch` | RO main SLURM job script |
| `scripts/wosr_loss_calc.py` | Core loss model (sigmoid ELF) |
| `scripts/wosr_aggregate.py` | Aggregates CSVs into county summaries |
| `scripts/wosr_analyze_results.py` | Generates analysis report |
| `scripts/wosr_corteva_pricing.py` | Generates Corteva pricing package |
| `scripts/wosr_finalize.sh` | All-in-one: sync + aggregate + analyze |
| `results/<CC>/wosr_<CC>_<YEAR>.csv` | One CSV per country-year |
| `pricing/WOSR_Corteva_Pricing_Package.md` | Current pricing deliverable |
| `PROJECT_STATUS.md` | Full status + all commands |

---

## Key Model Parameters (don't change without Konstantin's OK)

- **ELF_K = 0.35**, **ELF_X0 = 13.39**, **CF = 0.3589**
- These are calibrated to match Marsh Romania LR of 8.4% at 10 drought days
- ELF_X0 was recently fixed from 10.0 → 13.39 — this was critical

---

## Saga HPC Access

```bash
ssh saga   # logs in as digifarm@saga.sigma2.no
```

SLURM account: `nn12037k`. Never request more than 8 CPUs per job on Saga.

---

## Questions / Issues

- Slack Nils (U8TCVUANL) for business/Corteva questions
- Check `CONTEXT.md` for meeting notes and Descartes/Marsh background
- S3 bucket: `s3://digifarm-wosr-underwriting/`

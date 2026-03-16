# WOSR Underwriting Pipeline — Project Status

**Last updated:** 2026-03-16
**Meeting:** Descartes/Corteva call at 3 PM CET 2026-03-11 (completed)

---

## Pipeline Summary

Climate-based emergence guarantee pricing for Winter Oilseed Rape (WOSR) across Romania + 5 CEE countries (MD, PL, HU, CZ, SK). 30-year historical ERA5-Land analysis (1995–2024), calibrated against Marsh Romania portfolio LR of 8.4% at 10 drought days.

**Key methodology:** Sigmoid ELF model → drought index → calibrated loss ratio, with winter frost, crust, and catastrophe loadings.

---

## Code Status: Production-Ready (v1 Pilot)

All critical issues from GPT-5.4 Codex review have been fixed:

| Fix | File | Commit |
|-----|------|--------|
| Sigmoid recalibration: ELF_X0 10.0 → 13.39 | wosr_loss_calc.py:222 | 70f105d |
| Catastrophic frost: added bare-soil condition | wosr_loss_calc.py:329 | 70f105d |
| Crust loading: +1.5% when crust_flag=1 | wosr_loss_calc.py:349 | 70f105d |
| Crust window: uses actual sowing_doy | wosr_loss_calc.py:290 | 70f105d |

See `analysis/codex_review_response.md` for full review response.

---

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| ELF_K | 0.35 | Sigmoid steepness |
| ELF_X0 | 13.39 | Calibrated midpoint (was 10.0 — critical fix) |
| CF | 0.3589 | Marsh-calibrated: ELF(10)=0.234 → LR=8.4% |
| Sum insured | €96/ha | Corteva seed bag value |
| Commercial loading | 1.30× | 30% margin |
| Pricing blend | 60% 5yr + 40% 30yr | Weighted LR for premium |

---

## S3 Results (as of 2026-03-15)

**Bucket:** `s3://digifarm-wosr-underwriting/results/<COUNTRY>/`

**Total: 124 CSV files**

| Country | Years in S3 | Status |
|---------|-------------|--------|
| RO | 1995–2024 (30/30) | ✅ Complete |
| MD | 1995–2024 (30/30) | ✅ Complete |
| PL | 1995–2024 (30/30) | ✅ Complete |
| HU | 1995–2006 (12/30) | ⏸ Blocked — Saga quota exhausted |
| CZ | 1995–2005 (11/30) | ⏸ Blocked — Saga quota exhausted |
| SK | 1995–2005 (11/30) | ⏸ Blocked — Saga quota exhausted |

---

## SLURM Status (as of 2026-03-15)

**Both Saga accounts (nn12037k and nn6000k) billing quota exhausted.**
- No jobs can run until quota resets (~April 1)
- HU/CZ/SK pending jobs (17062162–17062164) have been cancelled
- When quota resets: resubmit per country using the commands below

---

## Resubmitting Jobs (after they expire)

Country jobs expire ~15:30 CET, RO job ~17:10 CET. After each expires, resubmit:

```bash
# Copy scripts to Saga (do once)
scp scripts/wosr_saga_country.sbatch digifarm@saga.sigma2.no:/cluster/work/users/digifarm/wosr/scripts/
scp scripts/wosr_saga.sbatch digifarm@saga.sigma2.no:/cluster/work/users/digifarm/wosr/scripts/

# Resubmit country jobs
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_MD scripts/wosr_saga_country.sbatch MD"
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_PL scripts/wosr_saga_country.sbatch PL"
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_HU scripts/wosr_saga_country.sbatch HU"
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_CZ scripts/wosr_saga_country.sbatch CZ"
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch --job-name=wosr_SK scripts/wosr_saga_country.sbatch SK"

# Resubmit RO
ssh saga "cd /cluster/work/users/digifarm/wosr && sbatch scripts/wosr_saga.sbatch"
```

---

## Syncing New Results & Committing

```bash
cd /home/ubuntu/wosr
aws s3 sync s3://digifarm-wosr-underwriting/results/ results/ --quiet
python3 scripts/wosr_aggregate.py --all
python3 scripts/wosr_analyze_results.py
git add results/ analysis/
git commit -m "Add <COUNTRY> results through <YEAR>, update analysis"
git push
```

Or use the all-in-one finalize script:
```bash
bash /home/ubuntu/wosr/scripts/wosr_finalize.sh
```

---

## Corteva Sales Data (pending integration)

File: `WOSR sales 2025.xlsx` — Corteva Romania 2025 seed bag sales by Area (~78K bags total).

**Blocker:** "Areas" are Corteva internal sales territories. Area→county mapping requested from Nils on 2026-03-16 via Slack. Nils confirmed (2026-03-12) "same areas as corn" and forwarded email — likely went to k@varik.ru, not Gmail. Awaiting response or check k@varik.ru inbox.

## Outreach Log (2026-03-16)

| Recipient | Channel | Subject | Status |
|-----------|---------|---------|--------|
| Nils Helset | Slack DM | Area→county mapping for Corteva sales data | Sent |
| Matti Tiainen | Gmail draft | WOSR preliminary 30yr pricing (RO/MD/PL) | **Draft — needs review before sending** |
| Sigma2 support | Gmail draft | Emergency quota top-up (nn12037k/nn6000k) | **Draft — needs review before sending** |
| Etienne (Descartes) | Gmail draft | Re: Satellite Claim Rate vs Excel Loss Ratio | **Draft from 2026-03-15 — needs review** |

---

## After All 30 Years Complete: Final Steps

1. `bash /home/ubuntu/wosr/scripts/wosr_finalize.sh`
2. `python3 scripts/wosr_corteva_pricing.py --all`
3. Update `pricing/WOSR_Corteva_Pricing_Package.md` with final 30-year numbers
4. Integrate Corteva sales data as exposure weights (once Area→county map received from Nils)
5. Send final package to Matti Tiainen (matti.tiainen@frontera.ag)

---

## Key Results (Preliminary — based on available years)

| Country | Year | Nat. Mean LR | Notable |
|---------|------|-------------|---------|
| RO | 2003 | 8.4% | 2003 drought — worst year, validates model |
| RO | 2004 | 0.33% | Normal year |
| MD | 1995 | 0.74% | Low loss |
| PL | 1995 | 0.54% | Low loss |
| SK | 1995 | 0.42% | Low loss |

RO 2003 national mean = exact Marsh calibration target. Model discriminative power confirmed.

---

## Future Improvements (not urgent for v1)

1. **EUROSTAT acreage weights** — county-level WOSR sown area as national LR weights
2. **Hourly ERA5** — replace 4×daily with hourly for accurate frost minima
3. **Country-specific CF** — calibrate non-RO countries once claims data available (Matti/Corteva)
4. **Satellite validation** — plant count model per county

---

## Contacts

| Person | Role | Contact |
|--------|------|---------|
| Matti Tiainen | Frontera Ag (client) | matti.tiainen@frontera.ag |
| Nils Helset | DigiFarm CEO | Slack U8TCVUANL, DM: DE0159YCA |
| Antoine & Etienne | Descartes (reinsurance) | via email |
| Konstantin Varik | DigiFarm CTO | project owner |

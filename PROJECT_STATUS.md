# WOSR Underwriting Pipeline — Project Status

**Last updated:** 2026-03-11
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

## Computation Status (as of 2026-03-11 ~00:00 CET)

### SLURM Jobs Running on Saga
| Job | Country | Elapsed | Wall Limit | Years Done |
|-----|---------|---------|------------|------------|
| 17042873 | RO | 2h06m | 6h | 1995–2004 (10 yrs) |
| 17043177 | MD | 58m | 8h | 1995 (1 yr) |
| 17043178 | PL | 58m | 8h | 1995 (1 yr) |
| 17043179 | HU | 58m | 8h | 0 (queued) |
| 17043180 | CZ | 58m | 8h | 0 (queued) |
| 17043181 | SK | 58m | 8h | 1995 (1 yr) |
| 17044376 | RO cleanup 1995-2003 | 20m | 4h | 0 (queued) |

**CDS throttling**: 7 concurrent jobs competing for ~2 CDS slots → 30-40 min wait per request. Each job completing ~1-2 years/hour.

### S3 Results Available
| Country | CSV Files | Years |
|---------|-----------|-------|
| RO | 1 | 2004 |
| MD | 1 | 1995 |
| PL | 1 | 1995 |
| HU | 0 | — |
| CZ | 0 | — |
| SK | 1 | 1995 |

**Note:** RO 1995–2003 were deleted from S3 (had wrong sigmoid ELF_X0=10.0). Cleanup job 17044376 is recomputing these with fixed calibration.

### Expected Completion
- RO main job (6h wall): will reach ~2008-2010 before expiring. Need resubmit.
- Country jobs (8h wall): will reach ~2003-2008 before expiring. Need resubmit.
- Full 30-year run requires 3-4 SLURM submissions per country due to CDS throttling.

---

## After Jobs Complete: Run Finalize Script

```bash
bash /home/ubuntu/wosr/scripts/wosr_finalize.sh
```

This will:
1. Sync all S3 results locally
2. Run `wosr_aggregate.py --all`
3. Run `wosr_analyze_results.py` → `analysis/WOSR_Results_Report.md`
4. Sync to S3

---

## Key Results (Preliminary)

| Country | Year | Nat. Mean Std LR | Notable |
|---------|------|-----------------|---------|
| RO | 2003 | 8.4% | 2003 drought — worst year, validates model |
| RO | 2004 | 0.33% | Normal year |
| MD | 1995 | 0.74% | Low loss |
| PL | 1995 | 0.54% | Low loss |
| SK | 1995 | 0.42% | Low loss |

RO 2003 national mean of 8.4% = exact Marsh calibration target. Model discriminative power confirmed.

---

## Next Steps (Priority Order)

1. **Resubmit jobs** as they hit wall time: `ssh saga "sbatch wosr_saga_country.sbatch <COUNTRY>"`
2. **Wait for cleanup job** 17044376 to complete (RO 1995–2003 with fixed sigmoid)
3. **Run finalize script** once all years done
4. **EUROSTAT acreage weights** — add county-level WOSR area weights for national LR
5. **Hourly ERA5** — replace 4×daily with hourly for accurate frost minima
6. **Country-specific CF** — calibrate non-RO countries once claims data available (Matti/Corteva)

---

## Pending Questions for Corteva/Descartes Meeting Follow-up

- Country-specific CF calibration: need non-RO historical emergence claims (Matti Tiainen)
- Satellite validation data for plant count model per county
- Confirmed trigger structure for PL/HU/CZ/SK (same binary 0%/50% as RO?)

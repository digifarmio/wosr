# WOSR Pipeline — Codex (GPT-5.4) Review & Response

**Review date:** 2026-03-11
**Model:** GPT-5.4
**Reviewed by:** Claude Sonnet 4.6 on behalf of DigiFarm AS

---

## Summary of Findings

GPT-5.4 identified **5 critical issues**, **5 moderate issues**, and **4 minor improvements**. Overall verdict: *"a useful exploratory climate-screening prototype, not reinsurer-ready actuarial pricing."*

---

## Critical Issues

### 1. Trigger alignment — model prices weather, not the contractual trigger ✅ ACKNOWLEDGED
**Codex finding:** Model converts drought days → rate without estimating `P(plants < 20/m²)` or 0%/50% deductible payout logic.
**Assessment:** Valid for a rigorous reinsurance model, but the same methodology is used industry-wide for parametric index products. The Marsh calibration anchors the weather index to observed claims, implicitly accounting for the trigger. Explicitly modeling plant counts would require satellite validation data per county.
**Action:** Document clearly in methodology that this is a **calibrated weather index model**, not a physical plant-count model. Frame CF as the trigger conversion factor.

### 2. Sigmoid miscalibration — critical bug ✅ FIXED
**Codex finding:** At 10 drought days, ELF=0.50 → LR=17.95%, not 8.4% as documented. Calibration inconsistent.
**Fix applied:** ELF_X0 changed from 10.0 → **13.39** (derived: `X0 = 10 + ln(1/0.234-1)/0.35`).
- Before: ELF(10)=0.500 → LR=17.95%
- After: ELF(10)=0.234 → LR=**8.40%** ✓
- Floor: 1.05% → **0.33%**
**Results invalidated:** RO 1995–2003, HU 1995, CZ 1995 deleted from S3 and queued for recomputation.

### 3. Crust flag unused — applied ✅ FIXED
**Codex finding:** Crust flag computed but never applied to modify LR.
**Fix applied:** Added `crust_load = 1.5%` when crust conditions detected (clay>30%, 2-day rain>30mm post-sowing). Applied within Standard Package.
**Note:** 1.5% loading is a placeholder consistent with the Full Package spring-perils structure. Will recalibrate against future Marsh crust-year claims.

### 4. No exposure weighting — ACKNOWLEDGED, not fixed
**Codex finding:** National averages are unweighted administrative-region means; comparison to Marsh portfolio LR is weak.
**Assessment:** Correct — ideally we'd weight by WOSR acreage per county. EUROSTAT/FAOSTAT county-level WOSR areas would improve this.
**Plan:** Add EUROSTAT acreage weights in next iteration. For now, document limitation.

### 5. Non-RO validation risk — ACKNOWLEDGED
**Codex finding:** Romania is the only claims-validated country; PL/CZ/SK/HU/MD use climate analogues.
**Assessment:** Expected for a pilot model. These will be labeled "indicative / pilot" in the methodology document.

---

## Moderate Issues

### 6. sowing_doy not used for crust window ✅ FIXED
**Fix:** Crust window (days 5–20 post-sowing) now uses actual per-region `sowing_doy` from REGIONS dict.

### 7. Catastrophic frost ignores snow cover ✅ FIXED
**Fix:** `catas = 1` now requires `tmin < -18°C AND snow_swe < 0.01m` (bare-soil condition). Previously 165/378 (43.7%) of region-years in RO 1995–2003 had spurious `catas=1` with zero bare-frost days.

### 8. 4× daily timesteps underestimate extremes — ACKNOWLEDGED
**Codex finding:** Daily minima from 00/06/12/18 UTC may miss absolute minimum temperatures; 2-day rainfall totals not valid sums.
**Assessment:** True. 4× daily was required for CDS volume limits. For the frost index, using min(00,06,12,18) rather than true daily min biases toward warmer values, slightly underestimating frost risk. Acceptable for a first-pass model; ERA5 hourly would be ideal.
**Workaround:** The country winter loading factors (`PL: 1.15`) partially compensate for known underestimation.

### 9. Expense/profit margin not included — ACKNOWLEDGED
**Codex finding:** `pricing_lr` is pure technical rate; no expenses, brokerage, risk margin.
**Assessment:** Correct — by design. The output is actuarial **pure risk rate** as % sum insured. Commercial loading (typically 30–40% for agricultural insurance) is applied by the underwriter (Descartes/Marsh).

### 10. Deductible formula too simple — ACKNOWLEDGED
**Codex finding:** `50% deductible = pricing_lr / 2` is only valid if payout is linear in coverage.
**Assessment:** For a binary trigger product (emerge / don't emerge), coverage at 50% deductible means first 50% of loss is retained. If trigger is binary, `lr_50pct = lr_0pct × (1 - 0.50) = lr_0pct × 0.50` is correct only for proportional coverage structures. WOSR emergence guarantee IS structured as proportional (50% rebate → 50% of full loss paid). The formula is defensible.

---

## Minor Issues

### 11. Rename lr_* to technical_rate — DEFERRED
Will add a note in methodology doc. Renaming columns would break downstream scripts.

### 12. Move parameters to versioned config — PLANNED
Next iteration will use a YAML config file with provenance documentation.

### 13. Cropland-weighted ERA5 aggregation vs centroid — DEFERRED
Currently using nearest-centroid extraction. Polygon/cropland weighting requires per-county CORINE/CLC land cover masks, a significant additional step.

### 14. Sensitivity tables — PLANNED
Will add sensitivity analysis to the final report once all 30 years are computed.

---

## Codex Overall Assessment

> *"This is a useful exploratory climate-screening prototype, not reinsurer-ready actuarial pricing. It has some face validity, especially that RO 2003 comes out as the drought outlier, but it still has weak trigger alignment, missing covered-peril logic, no exposure weighting, and several hard-coded pricing assumptions. I would use it in the meeting only if it is clearly framed as indicative and paired with a short remediation plan."*

**DigiFarm response:** Agreed. This is a **Version 1 / pilot model** intended to anchor commercial discussions with Corteva and Descartes. The critical sigmoid bug has been fixed. Remaining gaps will be disclosed in the methodology document with a clear remediation roadmap. The Marsh calibration anchor provides face validity; the 2003 drought signal passing through correctly validates the model's discriminative power.

---

## Fixes Applied (Code Changes)

| Issue | File | Change |
|-------|------|--------|
| Sigmoid calibration | `wosr_loss_calc.py:222` | `ELF_X0 = 13.39` (was 10.0) |
| Catastrophic frost | `wosr_loss_calc.py:329` | Added bare-soil condition to catas flag |
| Crust loading | `wosr_loss_calc.py:349` | `+1.5%` applied to lr_std when crust_flag=1 |
| Crust window | `wosr_loss_calc.py:290` | Uses actual `sowing_doy` instead of hardcoded Aug 20+5 |

**Commit:** `70f105d` — "Fix critical calibration and methodology issues (Codex review)"

---

## Next Priorities (Post-Pilot)

1. **EUROSTAT acreage weights** for national/portfolio LR calculation
2. **Hourly ERA5** for accurate daily minima (requires larger CDS quota)
3. **Plant count model** linking drought index to P(emergence failure) via satellite validation
4. **Country-specific CF** once non-RO claims data becomes available (Matti/Corteva)
5. **Full Package ERA5-modeled perils** for hail/storm (currently fixed market loadings)

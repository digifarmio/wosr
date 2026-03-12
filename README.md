# WOSR Underwriting Pipeline

Parametric climate insurance pricing for **Winter Oilseed Rape (WOSR)** emergence guarantees across Romania and 5 CEE countries (MD, PL, HU, CZ, SK).

Built for Corteva Agriscience / Frontera by DigiFarm AS.

---

## How It Works

1. Fetches ERA5-Land climate reanalysis (1995–2024) via Copernicus CDS API
2. Computes a drought index (days without sufficient soil moisture during emergence window)
3. Maps drought index → loss ratio via calibrated sigmoid ELF model
4. Applies frost, crust, and catastrophe loadings
5. Outputs county-level premium rates

**Calibration:** Marsh Romania portfolio LR = 8.4% at 10 drought days (ELF_X0=13.39, CF=0.3589)

---

## Documentation

| Doc | Contents |
|-----|----------|
| [`MORRIS.md`](MORRIS.md) | **Start here if continuing this work** — step-by-step handoff guide |
| [`PROJECT_STATUS.md`](PROJECT_STATUS.md) | Current computation status, S3 coverage, resubmit commands |
| [`CONTEXT.md`](CONTEXT.md) | Full task briefing, Slack messages, meeting notes, GDrive links |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code project instructions |
| [`pricing/WOSR_Corteva_Pricing_Package.md`](pricing/WOSR_Corteva_Pricing_Package.md) | Current pricing deliverable for Corteva |

---

## Quick Status

- **55 / ~180** country-year CSVs computed (30-year history × 6 countries)
- RO: 1995–2010 done | CZ/HU/MD/PL: 1995–2002 done | SK: 1995–2001 done
- SLURM jobs running on Saga, need periodic resubmission due to CDS throttling

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for full details and resubmit commands.

---

## Key Directories

```
results/<CC>/wosr_<CC>_<YEAR>.csv   # one file per country-year
scripts/                            # all processing scripts + SLURM job files
analysis/                           # aggregated reports
pricing/                            # Corteva pricing package
```

---

## Contacts

- **Matti Tiainen** — Frontera Ag (client): matti.tiainen@frontera.ag
- **Nils Helset** — DigiFarm CEO: Slack U8TCVUANL
- **Konstantin Varik** — DigiFarm CTO: project owner

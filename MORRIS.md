# WOSR Project — Handoff Notes

**Handed back to Konstantin: 2026-03-23**

Morris covered Mar 12-23. Full handoff report from Morris is in the git history / project notes.

For current state and next steps see `PROJECT_STATUS.md`.

## What Morris Completed (Mar 12-23)

- All 6 countries: **35 years complete** (1990–2024), 210 CSVs in S3
- Extended year range from 30yr (1995-2024) to 35yr (1990-1994) per Nils request
- Moved WOSR compute from Saga (quota exhausted) to **Betzy**
- Created individual Google Sheets per country in GDrive (see PROJECT_STATUS for links)
- Fixed ERA5 fetch year validation (1995→1940 lower bound)
- Betzy module loading fix: `source /etc/profile.d/z00_lmod.sh && module load StdEnv && module load awscli`

## Key Betzy paths

| Path | Description |
|------|-------------|
| `/cluster/work/users/digifarm/wosr/scripts/wosr_betzy_country.sbatch` | Main job (1995-2024) |
| `/cluster/work/users/digifarm/wosr/scripts/wosr_betzy_extension.sbatch` | Extension job (1990-1994) |
| `/cluster/work/users/digifarm/wosr/scripts/upload_results_to_s3.sh` | Manual S3 upload |
| `/cluster/work/users/digifarm/wosr/results/{CC}/` | Per-year CSVs |

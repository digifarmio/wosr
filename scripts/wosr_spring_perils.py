#!/usr/bin/env python3
"""
wosr_spring_perils.py
Fetch ERA5-Land spring data and compute 4 additional Full Package perils.

Adds to existing result CSVs:
  - Spring frost: Tmin ≤ -3°C after Mar 15 (post green-up)
  - Hail proxy: Tmax > 30°C AND daily precip > 20mm (May–Jul)
  - Storm/lodging: wind speed > 13 m/s OR daily rain > 50mm (May–Jul)
  - Spring vegetation drought: root zone moisture < 0.18 for 21+ consecutive days (Apr–Jun)

Usage:
    python wosr_spring_perils.py --country RO --year 2020 \
        --output-dir /tmp/era5_wosr/ \
        --result-csv results/RO/wosr_RO_2020.csv
"""

import argparse
import datetime
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# Reuse region definitions from wosr_loss_calc
from wosr_loss_calc import REGIONS

# Country bounding boxes (same as fetch script)
COUNTRY_BBOX = {
    "RO": [48.3, 20.2, 43.6, 30.0],
    "MD": [48.5, 26.6, 45.4, 30.2],
    "PL": [54.9, 14.1, 49.0, 24.2],
    "CZ": [51.1, 12.1, 48.5, 18.9],
    "SK": [49.6, 16.8, 47.7, 22.6],
    "HU": [48.6, 16.1, 45.7, 22.9],
    "UA": [52.4, 22.1, 44.4, 40.2],
}

# Spring window ERA5-Land variables
SPRING_VARS = [
    "2m_temperature",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]

# Peril thresholds
SPRING_FROST_K = 270.15       # -3°C in Kelvin
SPRING_DROUGHT_THRESH = 0.18  # m³/m³ root zone average
SPRING_DROUGHT_CONSEC = 21    # consecutive days needed
STORM_WIND_THRESH = 13.0      # m/s sustained (≈ 20 m/s gust)
STORM_RAIN_THRESH = 50.0      # mm/day
HAIL_TMAX_K = 303.15          # 30°C in Kelvin
HAIL_RAIN_THRESH = 20.0       # mm/day

# Calibration: peril LR per "event day" (GDoc central estimates as basis)
# Spring frost: 2.0% from ~5 event days nationally → 0.4% per day
# Hail: 1.5% from ~3 event days nationally → 0.5% per day
# Storm: 1.0% from ~2 event days nationally → 0.5% per day
# Spring drought: 2.0% when triggered (binary: 21+ days → full loading)
LR_PER_SPRING_FROST_DAY = 0.4
LR_PER_HAIL_DAY = 0.5
LR_PER_STORM_DAY = 0.5
LR_SPRING_DROUGHT_TRIGGERED = 2.0


def fetch_spring_window(bbox, year, output_path):
    """Fetch ERA5-Land spring window: Mar 1 – Jul 15 of year+1."""
    if output_path.exists():
        print(f"  Spring NC already exists, skipping: {output_path}")
        return

    import cdsapi
    client = cdsapi.Client(quiet=False)

    spring_year = str(year + 1)
    times = ["00:00", "06:00", "12:00", "18:00"]
    days = [f"{d:02d}" for d in range(1, 32)]

    print(f"  Fetching spring window ({spring_year}, Mar–Jul)...")
    zip_path = output_path.with_suffix(".zip")
    client.retrieve(
        "reanalysis-era5-land",
        {
            "variable": SPRING_VARS,
            "year": [spring_year],
            "month": ["03", "04", "05", "06", "07"],
            "day": days,
            "time": times,
            "area": bbox,
            "format": "netcdf",
        },
        str(zip_path),
    )
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        nc_names = [n for n in names if n.endswith(".nc")]
        if not nc_names:
            raise RuntimeError(f"No .nc in zip {zip_path}: {names}")
        zf.extract(nc_names[0], path=output_path.parent)
        (output_path.parent / nc_names[0]).rename(output_path)
    zip_path.unlink()
    print(f"  Saved: {output_path} ({output_path.stat().st_size / 1e6:.1f} MB)")


def extract_centroid(ds, lat, lon, var):
    return ds[var].sel(latitude=lat, longitude=lon, method="nearest")


def compute_daily_stat(ds_var, stat="min"):
    time_dim = "valid_time" if "valid_time" in ds_var.dims else "time"
    if stat == "min":
        return ds_var.resample({time_dim: "1D"}).min()
    elif stat == "max":
        return ds_var.resample({time_dim: "1D"}).max()
    elif stat == "mean":
        return ds_var.resample({time_dim: "1D"}).mean()
    elif stat == "sum":
        return ds_var.resample({time_dim: "1D"}).sum()


def compute_spring_perils(region, year, ds_spring):
    """Compute 4 spring/summer perils for one region/year."""
    region_id, name, lat, lon, clay_pct, sowing_doy, risk_zone = region
    spring_year = year + 1

    result = {"region_id": region_id}

    try:
        # --- Extract and compute daily values ---
        t2m_h = extract_centroid(ds_spring, lat, lon, "t2m")
        tmin = compute_daily_stat(t2m_h, "min")
        tmax = compute_daily_stat(t2m_h, "max")
        time_dim = "valid_time" if "valid_time" in tmin.dims else "time"
        t = tmin[time_dim].values

        swvl1_h = extract_centroid(ds_spring, lat, lon, "swvl1")
        swvl2_h = extract_centroid(ds_spring, lat, lon, "swvl2")
        swvl1_daily = compute_daily_stat(swvl1_h, "mean")
        swvl2_daily = compute_daily_stat(swvl2_h, "mean")

        tp_h = extract_centroid(ds_spring, lat, lon, "tp")
        tp_daily = compute_daily_stat(tp_h, "mean") * 1000 * 4  # m → mm, ×4 for 4 timesteps/day

        u10_h = extract_centroid(ds_spring, lat, lon, "u10")
        v10_h = extract_centroid(ds_spring, lat, lon, "v10")
        u10_daily_max = compute_daily_stat(u10_h, "max")
        v10_daily_max = compute_daily_stat(v10_h, "max")
        # Approximate daily max wind speed from max components
        ws_daily = np.sqrt(u10_daily_max.values**2 + v10_daily_max.values**2)

        # --- 1. SPRING FROST: Tmin ≤ -3°C after Mar 15 ---
        frost_start = np.datetime64(f"{spring_year}-03-15")
        frost_end = np.datetime64(f"{spring_year}-04-30")
        frost_mask = (t >= frost_start) & (t <= frost_end)
        tmin_spring = tmin.values[frost_mask]
        spring_frost_days = int(np.sum(tmin_spring < SPRING_FROST_K))
        lr_spring_frost = min(spring_frost_days * LR_PER_SPRING_FROST_DAY, 5.0)  # cap at 5%

        # --- 2. HAIL PROXY: Tmax > 30°C AND precip > 20mm (May–Jul) ---
        hail_start = np.datetime64(f"{spring_year}-05-01")
        hail_end = np.datetime64(f"{spring_year}-07-15")
        hail_mask = (t >= hail_start) & (t <= hail_end)
        n_hail = min(hail_mask.sum(), len(tmax.values), len(tp_daily.values))
        tmax_summer = tmax.values[:n_hail][hail_mask[:n_hail]]
        tp_summer = tp_daily.values[:n_hail][hail_mask[:n_hail]]
        hail_days = int(np.sum((tmax_summer > HAIL_TMAX_K) & (tp_summer > HAIL_RAIN_THRESH)))
        lr_hail = min(hail_days * LR_PER_HAIL_DAY, 3.0)  # cap at 3%

        # --- 3. STORM: wind > 13 m/s OR rain > 50mm (May–Jul) ---
        ws_summer = ws_daily[:n_hail][hail_mask[:n_hail]]
        storm_days = int(np.sum((ws_summer > STORM_WIND_THRESH) | (tp_summer > STORM_RAIN_THRESH)))
        lr_storm = min(storm_days * LR_PER_STORM_DAY, 3.0)  # cap at 3%

        # --- 4. SPRING VEGETATION DROUGHT: root zone < 0.18 for 21+ consec days (Apr–Jun) ---
        drought_start = np.datetime64(f"{spring_year}-04-15")
        drought_end = np.datetime64(f"{spring_year}-06-15")
        drought_mask = (t >= drought_start) & (t <= drought_end)
        n_dr = min(drought_mask.sum(), len(swvl1_daily.values), len(swvl2_daily.values))
        swvl1_dr = swvl1_daily.values[:n_dr][drought_mask[:n_dr]]
        swvl2_dr = swvl2_daily.values[:n_dr][drought_mask[:n_dr]]
        root_zone = (swvl1_dr + swvl2_dr) / 2.0
        # Count max consecutive days below threshold
        below = root_zone < SPRING_DROUGHT_THRESH
        max_consec = 0
        current = 0
        for b in below:
            if b:
                current += 1
                max_consec = max(max_consec, current)
            else:
                current = 0
        spring_drought_days = max_consec
        lr_spring_drought = LR_SPRING_DROUGHT_TRIGGERED if spring_drought_days >= SPRING_DROUGHT_CONSEC else 0.0

        result.update({
            "spring_frost_days": spring_frost_days,
            "lr_spring_frost_pct": round(lr_spring_frost, 2),
            "hail_days": hail_days,
            "lr_hail_pct": round(lr_hail, 2),
            "storm_days": storm_days,
            "lr_storm_pct": round(lr_storm, 2),
            "spring_drought_consec_days": spring_drought_days,
            "lr_spring_drought_pct": round(lr_spring_drought, 2),
        })

    except Exception as e:
        print(f"  WARNING: {region_id} spring perils failed: {e}")
        result.update({
            "spring_frost_days": 0, "lr_spring_frost_pct": 0,
            "hail_days": 0, "lr_hail_pct": 0,
            "storm_days": 0, "lr_storm_pct": 0,
            "spring_drought_consec_days": 0, "lr_spring_drought_pct": 0,
        })

    return result


def main():
    parser = argparse.ArgumentParser(description="Compute spring/summer perils from ERA5-Land.")
    parser.add_argument("--country", required=True, choices=list(REGIONS.keys()))
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--output-dir", required=True, help="Directory for spring NetCDF cache")
    parser.add_argument("--result-csv", required=True, help="Existing result CSV to merge into")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip ERA5 fetch (use cached NC)")
    args = parser.parse_args()

    bbox = COUNTRY_BBOX[args.country]
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    spring_nc = out_dir / f"era5_wosr_{args.country}_{args.year}_spring.nc"

    # Step 1: Fetch spring ERA5-Land data
    if not args.skip_fetch:
        fetch_spring_window(bbox, args.year, spring_nc)
    if not spring_nc.exists():
        sys.exit(f"Spring NC not found: {spring_nc}")

    # Step 2: Load and compute perils
    print(f"Computing spring perils for {args.country} {args.year}...")
    ds = xr.open_dataset(spring_nc)
    rename_map = {
        "volumetric_soil_water_layer_1": "swvl1",
        "volumetric_soil_water_layer_2": "swvl2",
        "2m_temperature": "t2m",
        "total_precipitation": "tp",
        "10m_u_component_of_wind": "u10",
        "10m_v_component_of_wind": "v10",
    }
    for old, new in rename_map.items():
        if old in ds:
            ds = ds.rename({old: new})

    regions = REGIONS[args.country]
    spring_results = []
    for i, region in enumerate(regions):
        print(f"  [{i+1}/{len(regions)}] {region[1]}...")
        row = compute_spring_perils(region, args.year, ds)
        spring_results.append(row)
        print(f"    frost={row.get('spring_frost_days',0)}d "
              f"hail={row.get('hail_days',0)}d "
              f"storm={row.get('storm_days',0)}d "
              f"drought={row.get('spring_drought_consec_days',0)}d")

    ds.close()

    # Step 3: Merge with existing result CSV
    result_path = Path(args.result_csv)
    if not result_path.exists():
        sys.exit(f"Result CSV not found: {result_path}")

    df_base = pd.read_csv(result_path)
    df_spring = pd.DataFrame(spring_results)
    df_merged = df_base.merge(df_spring, on="region_id", how="left")

    # Add spring peril columns to the result
    spring_cols = ["lr_spring_frost_pct", "lr_hail_pct", "lr_storm_pct", "lr_spring_drought_pct"]
    for col in spring_cols:
        if col not in df_merged.columns:
            df_merged[col] = 0.0
        df_merged[col] = df_merged[col].fillna(0.0)

    # Scale ERA5 spring frost so 35yr RO avg ≈ 1.5% (raw avg = 0.408%)
    # This preserves the year-to-year and county-to-county signal shape
    SPRING_FROST_SCALE = 3.678
    df_merged["lr_spring_frost_scaled_pct"] = (
        df_merged["lr_spring_frost_pct"] * SPRING_FROST_SCALE
    ).round(2)

    # Full Package = Standard + Winter + scaled spring frost + market loadings
    # Hail (+0.75%), storm/lodging (+0.75%), spring drought (+2.0%) are flat
    # market-rate loadings — ERA5 cannot reliably capture these sub-grid perils
    MARKET_HAIL = 0.75
    MARKET_STORM = 0.75
    MARKET_SPRING_DROUGHT = 2.0
    df_merged["lr_full_pct"] = (
        df_merged["lr_standard_pct"]
        + df_merged["lr_winter_pct"]
        + df_merged["lr_spring_frost_scaled_pct"]
        + MARKET_HAIL
        + MARKET_STORM
        + MARKET_SPRING_DROUGHT
    ).round(2)

    df_merged.to_csv(result_path, index=False)
    print(f"\nUpdated: {result_path}")
    print(f"  Mean LR Full (new): {df_merged['lr_full_pct'].mean():.1f}%")
    print(f"  Spring frost contrib: {df_merged['lr_spring_frost_pct'].mean():.2f}%")
    print(f"  Hail contrib: {df_merged['lr_hail_pct'].mean():.2f}%")
    print(f"  Storm contrib: {df_merged['lr_storm_pct'].mean():.2f}%")
    print(f"  Spring drought contrib: {df_merged['lr_spring_drought_pct'].mean():.2f}%")

    # Cleanup spring NC to save disk
    spring_nc.unlink(missing_ok=True)
    print(f"  Cleaned up: {spring_nc}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
wosr_era5_fetch.py
Fetch ERA5-Land data for WOSR historical loss analysis.

Downloads two seasonal windows per country per year:
  - Autumn window: Aug 1 – Oct 31  (sowing/emergence peril: drought, soil crust)
  - Winter window: Nov 1 – Mar 31 of year+1  (frost kill peril)

Variables: swvl1 (soil moisture), 2m_temperature, snow_depth_water_equivalent

Output: NetCDF files written to --output-dir (local path, then uploaded to S3 by caller).

Usage:
    python wosr_era5_fetch.py --country RO --year 1995 --output-dir /tmp/era5_wosr/
"""

import argparse
import os
import sys
from pathlib import Path

import cdsapi

# Country bounding boxes [north, west, south, east]
COUNTRY_BBOX = {
    "RO": [48.3, 20.2, 43.6, 30.0],   # Romania
    "MD": [48.5, 26.6, 45.4, 30.2],   # Moldova
    "PL": [54.9, 14.1, 49.0, 24.2],   # Poland
    "CZ": [51.1, 12.1, 48.5, 18.9],   # Czech Republic
    "SK": [49.6, 16.8, 47.7, 22.6],   # Slovakia
    "HU": [48.6, 16.1, 45.7, 22.9],   # Hungary
    "UA": [52.4, 22.1, 44.4, 40.2],   # Ukraine (full; filter to west/central in analysis)
}

AUTUMN_VARS = [
    "volumetric_soil_water_layer_1",
    "2m_temperature",
    "total_precipitation",
]

WINTER_VARS = [
    "2m_temperature",
    "snow_depth_water_equivalent",
]


def fetch_window(client, bbox, variables, years, months, output_path):
    """Download ERA5-Land for given bbox/variables/time range."""
    if output_path.exists():
        print(f"  Already exists, skipping: {output_path}")
        return

    times = [f"{h:02d}:00" for h in range(24)]
    days = [f"{d:02d}" for d in range(1, 32)]

    print(f"  Fetching {output_path.name} ({bbox}, {years}, months={months})")
    client.retrieve(
        "reanalysis-era5-land",
        {
            "variable": variables,
            "year": years,
            "month": months,
            "day": days,
            "time": times,
            "area": bbox,
            "format": "netcdf",
        },
        str(output_path),
    )
    print(f"  Saved: {output_path} ({output_path.stat().st_size / 1e6:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Fetch ERA5-Land for WOSR analysis.")
    parser.add_argument("--country", required=True, choices=list(COUNTRY_BBOX.keys()),
                        help="ISO country code")
    parser.add_argument("--year", type=int, required=True,
                        help="WOSR crop year (sowing year; winter window spans into year+1)")
    parser.add_argument("--output-dir", required=True,
                        help="Local directory for NetCDF output")
    parser.add_argument("--cds-key", default=None,
                        help="CDS API key (defaults to ~/.cdsapirc)")
    args = parser.parse_args()

    if args.year < 1995 or args.year > 2024:
        sys.exit(f"Year must be 1995–2024, got {args.year}")

    bbox = COUNTRY_BBOX[args.country]
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = cdsapi.Client(quiet=False)

    # --- Autumn window: Aug–Oct of sowing year ---
    autumn_path = out_dir / f"era5_wosr_{args.country}_{args.year}_autumn.nc"
    fetch_window(
        client, bbox, AUTUMN_VARS,
        years=[str(args.year)],
        months=["08", "09", "10"],
        output_path=autumn_path,
    )

    # --- Winter window: Nov of sowing year + Dec–Mar of harvest year ---
    winter_year1 = str(args.year)
    winter_year2 = str(args.year + 1)
    winter_path = out_dir / f"era5_wosr_{args.country}_{args.year}_winter.nc"
    fetch_window(
        client, bbox, WINTER_VARS,
        years=sorted({winter_year1, winter_year2}),
        months=["11", "12", "01", "02", "03"],
        output_path=winter_path,
    )

    print(f"\nDone. Files in {out_dir}:")
    for f in sorted(out_dir.glob(f"era5_wosr_{args.country}_{args.year}_*.nc")):
        print(f"  {f.name}  ({f.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

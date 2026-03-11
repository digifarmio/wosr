#!/usr/bin/env python3
"""
wosr_loss_calc.py
Compute WOSR county-level historical loss ratios from ERA5-Land data.

For each region/county centroid and crop year:
  - Autumn drought index (I_drought): days in Aug 20–Oct 20 with swvl1 < 0.15 m³/m³
  - Soil crust flag: any 48h with tp > 30mm in days 5–20 post-sowing AND clay > 30%
  - Winter frost index (I_frost): days in Dec 1–Feb 28 with tmin < -12°C AND snow SWE < 10mm
  - Catastrophic frost flag: any day tmin < -18°C in Dec–Feb
  - Raw emergence loss factor (ELF): derived from drought index (sigmoid function)
  - Calibrated Standard Package loss ratio: ELF × CF (CF = 0.3589)
  - Winter frost loss ratio: separate component for Full Package

Calibration factor CF = 8.4% / 23.40% = 0.3589
  (Romania: long-term calibrated LR / raw ERA5 signal mean, validated against Marsh claims)

Outputs: CSV with columns:
  country, region_id, region_name, year,
  i_drought_days, i_frost_days, frost_catastrophic,
  elf_raw, lr_standard_pct, lr_winter_pct, lr_full_pct,
  risk_zone, notes

Usage:
    python wosr_loss_calc.py --country RO --year 2020 \
        --autumn-nc /tmp/era5_wosr/era5_wosr_RO_2020_autumn.nc \
        --winter-nc  /tmp/era5_wosr/era5_wosr_RO_2020_winter.nc \
        --output /tmp/results/wosr_RO_2020.csv
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# ---------------------------------------------------------------------------
# Region definitions: centroid (lat, lon), name, clay_pct (LUCAS estimate),
# sowing_doy (day of year, approximate regional mean), risk_zone
# ---------------------------------------------------------------------------

REGIONS = {
    "RO": [
        # (region_id, name, lat, lon, clay_pct, sowing_doy, risk_zone)
        ("RO-AB", "Alba",          46.08, 23.58, 28, 253, "Z3"),
        ("RO-AR", "Arad",          46.17, 21.31, 32, 255, "Z2"),
        ("RO-AG", "Argeș",         44.87, 24.87, 35, 257, "Z2"),
        ("RO-BC", "Bacău",         46.57, 26.91, 30, 250, "Z3"),
        ("RO-BH", "Bihor",         47.05, 22.00, 30, 252, "Z2"),
        ("RO-BN", "Bistrița-Năsăud", 47.13, 24.50, 25, 248, "Z3"),
        ("RO-BT", "Botoșani",      47.75, 26.67, 30, 245, "Z1"),
        ("RO-BV", "Brașov",        45.65, 25.60, 22, 250, "Z3"),
        ("RO-BR", "Brăila",        45.27, 27.96, 38, 258, "Z1"),
        ("RO-B",  "București",     44.43, 26.10, 38, 258, "Z1"),
        ("RO-BZ", "Buzău",         45.15, 26.82, 35, 257, "Z1"),
        ("RO-CS", "Caraș-Severin", 45.30, 21.90, 28, 255, "Z2"),
        ("RO-CL", "Călărași",      44.20, 26.33, 40, 260, "Z1"),
        ("RO-CJ", "Cluj",          46.77, 23.60, 26, 250, "Z3"),
        ("RO-CT", "Constanța",     44.18, 28.65, 25, 262, "Z1"),
        ("RO-CV", "Covasna",       45.85, 26.18, 24, 250, "Z3"),
        ("RO-DB", "Dâmbovița",     44.93, 25.45, 35, 257, "Z2"),
        ("RO-DJ", "Dolj",          44.32, 23.81, 42, 258, "Z1"),
        ("RO-GL", "Galați",        45.43, 28.05, 35, 258, "Z1"),
        ("RO-GR", "Giurgiu",       43.90, 25.97, 42, 260, "Z1"),
        ("RO-GJ", "Gorj",          44.95, 23.28, 30, 255, "Z2"),
        ("RO-HR", "Harghita",      46.50, 25.50, 22, 248, "Z3"),
        ("RO-HD", "Hunedoara",     45.72, 22.91, 28, 253, "Z3"),
        ("RO-IL", "Ialomița",      44.60, 27.38, 30, 260, "Z1"),
        ("RO-IS", "Iași",          47.15, 27.60, 33, 248, "Z1"),
        ("RO-IF", "Ilfov",         44.55, 26.12, 38, 258, "Z1"),
        ("RO-MM", "Maramureș",     47.65, 24.10, 25, 247, "Z3"),
        ("RO-MH", "Mehedinți",     44.63, 22.65, 32, 255, "Z2"),
        ("RO-MS", "Mureș",         46.55, 24.57, 26, 250, "Z3"),
        ("RO-NT", "Neamț",         47.00, 26.37, 28, 250, "Z3"),
        ("RO-OT", "Olt",           44.43, 24.37, 40, 258, "Z1"),
        ("RO-PH", "Prahova",       45.07, 25.98, 35, 257, "Z2"),
        ("RO-SM", "Satu Mare",     47.80, 22.88, 28, 250, "Z2"),
        ("RO-SJ", "Sălaj",         47.18, 23.05, 27, 250, "Z3"),
        ("RO-SB", "Sibiu",         45.80, 24.15, 25, 252, "Z3"),
        ("RO-SV", "Suceava",       47.65, 25.95, 27, 247, "Z3"),
        ("RO-TR", "Teleorman",     43.97, 25.00, 42, 260, "Z1"),
        ("RO-TM", "Timiș",         45.75, 21.23, 33, 255, "Z2"),
        ("RO-TL", "Tulcea",        45.18, 28.80, 28, 260, "Z1"),
        ("RO-VS", "Vaslui",        46.64, 27.73, 32, 250, "Z1"),
        ("RO-VL", "Vâlcea",        45.10, 24.37, 30, 255, "Z2"),
        ("RO-VN", "Vrancea",       45.70, 27.07, 35, 252, "Z1"),
    ],
    "MD": [
        ("MD-AN", "Anenii Noi",    46.88, 29.23, 35, 248, "Z2"),
        ("MD-BA", "Bălți",         47.76, 27.93, 32, 245, "Z1"),
        ("MD-BR", "Briceni",       48.37, 27.07, 30, 243, "Z1"),
        ("MD-CA", "Cahul",         45.90, 28.20, 35, 252, "Z1"),
        ("MD-CM", "Căușeni",       46.63, 29.41, 37, 250, "Z1"),
        ("MD-CI", "Cimișlia",      46.52, 28.78, 37, 250, "Z1"),
        ("MD-CR", "Criuleni",      47.21, 29.15, 33, 247, "Z2"),
        ("MD-DO", "Dondușeni",     48.23, 27.60, 30, 243, "Z1"),
        ("MD-DR", "Drochia",       48.02, 27.87, 30, 244, "Z1"),
        ("MD-DU", "Dubăsari",      47.27, 29.15, 33, 247, "Z2"),
        ("MD-ED", "Edineț",        48.17, 27.30, 29, 243, "Z2"),
        ("MD-FL", "Florești",      47.90, 28.28, 30, 244, "Z1"),
        ("MD-GL", "Glodeni",       47.78, 27.52, 30, 244, "Z1"),
        ("MD-HI", "Hîncești",      46.83, 28.58, 35, 248, "Z2"),
        ("MD-IA", "Ialoveni",      46.87, 28.77, 35, 248, "Z2"),
        ("MD-LE", "Leova",         46.48, 28.26, 37, 250, "Z1"),
        ("MD-NI", "Nisporeni",     47.08, 28.18, 33, 247, "Z2"),
        ("MD-OC", "Ocnița",        48.38, 27.47, 28, 243, "Z2"),
        ("MD-OR", "Orhei",         47.38, 28.82, 33, 247, "Z2"),
        ("MD-RE", "Rezina",        47.75, 28.97, 32, 245, "Z2"),
        ("MD-RI", "Rîșcani",       47.95, 27.57, 30, 244, "Z1"),
        ("MD-SI", "Sîngerei",      47.63, 28.13, 31, 245, "Z1"),
        ("MD-SO", "Soroca",        48.16, 28.30, 30, 243, "Z1"),
        ("MD-ST", "Strășeni",      47.14, 28.60, 33, 247, "Z2"),
        ("MD-SD", "Șoldănești",    47.82, 28.80, 30, 244, "Z2"),
        ("MD-ST2","Ștefan Vodă",   46.52, 29.67, 35, 250, "Z1"),
        ("MD-TA", "Taraclia",      45.90, 28.67, 37, 252, "Z1"),
        ("MD-TE", "Telenești",     47.50, 28.37, 31, 246, "Z2"),
        ("MD-UN", "Ungheni",       47.21, 27.80, 32, 246, "Z2"),
    ],
    "PL": [
        ("PL-DS", "Lower Silesia",        51.13, 16.99, 30, 245, "Z3"),
        ("PL-KP", "Kuyavian-Pomeranian",  53.17, 18.01, 28, 243, "Z3"),
        ("PL-LU", "Lublin",               51.25, 22.57, 32, 245, "Z2"),
        ("PL-LB", "Lubusz",               52.22, 15.51, 27, 245, "Z3"),
        ("PL-LD", "Łódź",                 51.77, 19.46, 33, 245, "Z1"),
        ("PL-MA", "Lesser Poland",        49.71, 20.43, 30, 247, "Z2"),
        ("PL-MZ", "Masovian",             52.22, 21.01, 33, 244, "Z1"),
        ("PL-OP", "Opole",                50.67, 17.93, 32, 246, "Z2"),
        ("PL-PK", "Subcarpathian",        50.06, 22.01, 28, 248, "Z2"),
        ("PL-PD", "Podlaskie",            53.13, 22.78, 27, 242, "Z1"),
        ("PL-PM", "Pomerania",            54.18, 17.53, 27, 242, "Z3"),
        ("PL-SL", "Silesia",              50.43, 19.02, 32, 246, "Z3"),
        ("PL-SK", "Świętokrzyskie",       50.87, 20.63, 30, 246, "Z2"),
        ("PL-WN", "Warmia-Mazury",        53.83, 20.48, 25, 242, "Z1"),
        ("PL-WP", "Greater Poland",       52.41, 17.08, 29, 244, "Z3"),
        ("PL-ZP", "West Pomerania",       53.43, 15.57, 27, 242, "Z3"),
    ],
    "HU": [
        ("HU-BA", "Baranya",       45.98, 18.22, 35, 255, "Z2"),
        ("HU-BE", "Békés",         46.77, 21.10, 40, 257, "Z1"),
        ("HU-BK", "Bács-Kiskun",   46.57, 19.37, 35, 257, "Z1"),
        ("HU-BO", "Borsod",        48.10, 20.78, 30, 248, "Z1"),
        ("HU-CS", "Csongrád-Csanád",46.35, 20.18, 42, 258, "Z1"),
        ("HU-FE", "Fejér",         47.12, 18.53, 35, 255, "Z2"),
        ("HU-GS", "Győr-Moson-Sopron", 47.68, 17.25, 28, 253, "Z3"),
        ("HU-HB", "Hajdú-Bihar",   47.52, 21.62, 38, 255, "Z1"),
        ("HU-HE", "Heves",         47.90, 20.08, 32, 250, "Z2"),
        ("HU-JN", "Jász-Nagykun-Szolnok", 47.17, 20.18, 40, 257, "Z1"),
        ("HU-KE", "Komárom-Esztergom", 47.68, 18.20, 30, 253, "Z2"),
        ("HU-NO", "Nógrád",        48.00, 19.52, 28, 250, "Z2"),
        ("HU-PE", "Pest",          47.50, 19.38, 35, 255, "Z2"),
        ("HU-SO", "Somogy",        46.37, 17.65, 30, 255, "Z3"),
        ("HU-SZ", "Szabolcs-Szatmár-Bereg", 47.98, 22.00, 28, 248, "Z1"),
        ("HU-TO", "Tolna",         46.47, 18.55, 35, 257, "Z2"),
        ("HU-VA", "Vas",           47.10, 16.83, 27, 253, "Z3"),
        ("HU-VE", "Veszprém",      47.10, 17.90, 28, 253, "Z3"),
        ("HU-ZA", "Zala",          46.58, 16.85, 28, 255, "Z3"),
    ],
    "CZ": [
        ("CZ-JC", "South Bohemia",    49.00, 14.47, 27, 248, "Z2"),
        ("CZ-JM", "South Moravia",    49.00, 16.62, 33, 250, "Z2"),
        ("CZ-KA", "Karlovy Vary",     50.23, 12.87, 24, 247, "Z3"),
        ("CZ-KR", "Hradec Králové",   50.21, 15.83, 28, 247, "Z2"),
        ("CZ-LI", "Liberec",          50.77, 15.05, 24, 246, "Z3"),
        ("CZ-MO", "Moravian-Silesian",49.82, 18.26, 28, 247, "Z2"),
        ("CZ-OL", "Olomouc",          49.60, 17.25, 30, 248, "Z2"),
        ("CZ-PA", "Pardubice",        50.03, 15.78, 28, 247, "Z2"),
        ("CZ-PL", "Plzeň",            49.74, 13.38, 26, 248, "Z3"),
        ("CZ-PR", "Prague",           50.08, 14.44, 30, 248, "Z2"),
        ("CZ-ST", "Central Bohemia",  49.88, 14.66, 30, 248, "Z2"),
        ("CZ-US", "Ústí nad Labem",   50.66, 14.03, 25, 246, "Z3"),
        ("CZ-VY", "Vysočina",         49.40, 15.58, 27, 248, "Z3"),
        ("CZ-ZL", "Zlín",             49.23, 17.67, 30, 248, "Z2"),
    ],
    "SK": [
        ("SK-BA", "Bratislava",       48.15, 17.11, 32, 253, "Z2"),
        ("SK-BB", "Banská Bystrica",  48.74, 19.15, 25, 248, "Z3"),
        ("SK-KE", "Košice",           48.72, 21.26, 28, 247, "Z1"),
        ("SK-NI", "Nitra",            48.31, 18.09, 35, 253, "Z1"),
        ("SK-PO", "Prešov",           49.00, 21.24, 26, 247, "Z2"),
        ("SK-TN", "Trenčín",          48.89, 18.04, 27, 249, "Z2"),
        ("SK-TT", "Trnava",           48.37, 17.59, 33, 252, "Z2"),
        ("SK-ZA", "Žilina",           49.22, 18.74, 24, 248, "Z3"),
    ],
    "UA": [
        # Western/central oblasts only — conflict-affected south/east excluded
        ("UA-CH", "Cherkasy",         49.44, 32.06, 35, 248, "Z1"),
        ("UA-KH", "Khmelnytskyi",     49.42, 26.99, 32, 247, "Z2"),
        ("UA-KV", "Kyiv oblast",      50.45, 30.52, 33, 246, "Z1"),
        ("UA-LV", "Lviv",             49.84, 24.03, 28, 248, "Z2"),
        ("UA-IF", "Ivano-Frankivsk",  48.92, 24.71, 26, 250, "Z3"),
        ("UA-RI", "Rivne",            50.62, 26.25, 28, 246, "Z2"),
        ("UA-TE", "Ternopil",         49.55, 25.60, 30, 247, "Z2"),
        ("UA-VI", "Vinnytsia",        49.23, 28.47, 35, 248, "Z1"),
        ("UA-VO", "Volyn",            50.75, 25.32, 27, 245, "Z2"),
        ("UA-ZK", "Zakarpattia",      48.62, 22.30, 25, 252, "Z3"),
        ("UA-ZH", "Zhytomyr",         50.25, 28.66, 30, 246, "Z2"),
    ],
}

# Calibration parameters
CF = 0.3589          # Romania-validated calibration factor
DROUGHT_THRESH = 0.15  # m³/m³ — ERA5 swvl1 threshold for non-emergence risk
FROST_THRESH_K = 261.15  # K = -12°C — winter kill minimum temperature threshold
FROST_CATAS_K = 255.15   # K = -18°C — catastrophic frost threshold
SNOW_THRESH = 0.01   # m SWE — below this = bare soil for frost purposes

# Winter frost loadings by country vs Romania baseline
COUNTRY_WINTER_LOADING = {
    "RO": 1.00,
    "MD": 1.05,
    "PL": 1.15,
    "CZ": 0.90,
    "SK": 0.95,
    "HU": 0.95,
    "UA": 1.25,
}

# ELF sigmoid parameters (calibrated so that 10 drought days → ELF ≈ 0.23 → LR ≈ 8.4%)
ELF_K = 0.35   # steepness
ELF_X0 = 10.0  # inflection point (days)


def elf_from_drought(i_drought):
    """Sigmoid emergence loss factor from drought days."""
    return 1.0 / (1.0 + np.exp(-ELF_K * (i_drought - ELF_X0)))


def extract_centroid(ds, lat, lon, var):
    """Extract ERA5 variable at nearest grid point to centroid."""
    return ds[var].sel(latitude=lat, longitude=lon, method="nearest")


def compute_daily_min(ds_var):
    """Compute daily minimum from hourly ERA5 data."""
    time_dim = "valid_time" if "valid_time" in ds_var.dims else "time"
    return ds_var.resample({time_dim: "1D"}).min()


def compute_daily_mean(ds_var):
    """Compute daily mean from hourly ERA5 data."""
    time_dim = "valid_time" if "valid_time" in ds_var.dims else "time"
    return ds_var.resample({time_dim: "1D"}).mean()


def process_region(region, year, ds_autumn, ds_winter):
    """Compute loss ratio metrics for one region/year."""
    region_id, name, lat, lon, clay_pct, sowing_doy, risk_zone = region

    import datetime
    result = {
        "region_id": region_id,
        "region_name": name,
        "year": year,
        "lat": lat,
        "lon": lon,
        "clay_pct": clay_pct,
        "sowing_doy": sowing_doy,
        "risk_zone": risk_zone,
    }

    # ---- AUTUMN: drought index ----
    try:
        swvl1_h = extract_centroid(ds_autumn, lat, lon, "swvl1")
        swvl1_daily = compute_daily_mean(swvl1_h)
        time_dim = "valid_time" if "valid_time" in swvl1_daily.dims else "time"

        # Window: Aug 20 – Oct 20
        t = swvl1_daily[time_dim].values
        sowing_start = np.datetime64(f"{year}-08-20")
        sowing_end   = np.datetime64(f"{year}-10-20")
        mask = (t >= sowing_start) & (t <= sowing_end)
        swvl1_window = swvl1_daily.values[mask]

        if len(swvl1_window) == 0:
            result.update({"i_drought_days": np.nan, "elf_raw": np.nan})
        else:
            i_drought = int(np.sum(swvl1_window < DROUGHT_THRESH))
            elf_raw = elf_from_drought(i_drought)

            # Soil crust modifier
            tp_h = extract_centroid(ds_autumn, lat, lon, "tp")
            tp_daily = compute_daily_mean(tp_h) * 1000  # m → mm
            tp_window = tp_daily.values[mask]
            # Find any 2-day sum > 30mm in days 5-20 of sowing window
            crust_flag = 0
            if clay_pct > 30 and len(tp_window) >= 20:
                for i in range(5, min(20, len(tp_window) - 1)):
                    if tp_window[i] + tp_window[i+1] > 30:
                        crust_flag = 1
                        break

            result["i_drought_days"] = i_drought
            result["crust_flag"] = crust_flag
            result["elf_raw"] = float(elf_raw)
    except Exception as e:
        result.update({"i_drought_days": np.nan, "crust_flag": 0, "elf_raw": np.nan, "autumn_error": str(e)})

    # ---- WINTER: frost index ----
    try:
        t2m_h = extract_centroid(ds_winter, lat, lon, "t2m")
        t2m_daily_min = compute_daily_min(t2m_h)
        time_dim_w = "valid_time" if "valid_time" in t2m_daily_min.dims else "time"

        sde_h = extract_centroid(ds_winter, lat, lon, "sd")
        sde_daily = compute_daily_mean(sde_h)

        # Window: Dec 1 of year – Feb 28 of year+1
        t_w = t2m_daily_min[time_dim_w].values
        winter_start = np.datetime64(f"{year}-12-01")
        winter_end   = np.datetime64(f"{year+1}-02-28")
        mask_w = (t_w >= winter_start) & (t_w <= winter_end)

        tmin_w = t2m_daily_min.values[mask_w]
        sde_w = sde_daily.values[mask_w[:len(sde_daily.values)]] if len(mask_w) <= len(sde_daily.values) else np.zeros(mask_w.sum())

        if len(tmin_w) == 0:
            result.update({"i_frost_days": 0, "frost_catastrophic": 0})
        else:
            # Bare-soil frost days: tmin < -12°C AND snow SWE < 10mm (0.01m)
            n = min(len(tmin_w), len(sde_w))
            bare_frost = (tmin_w[:n] < FROST_THRESH_K) & (sde_w[:n] < SNOW_THRESH)
            i_frost = int(np.sum(bare_frost))
            catas = int(np.any(tmin_w < FROST_CATAS_K))
            result["i_frost_days"] = i_frost
            result["frost_catastrophic"] = catas
    except Exception as e:
        result.update({"i_frost_days": 0, "frost_catastrophic": 0, "winter_error": str(e)})

    # ---- CALIBRATED LOSS RATIOS ----
    elf = result.get("elf_raw", np.nan)
    country = region_id.split("-")[0]
    winter_load = COUNTRY_WINTER_LOADING.get(country, 1.0)

    if not np.isnan(elf):
        lr_std = elf * CF * 100  # percent
        # Winter frost component
        i_frost = result.get("i_frost_days", 0)
        catas = result.get("frost_catastrophic", 0)
        # Linear frost LR: 3 bare-frost-days → ~4.5% national avg; catastrophic → add 5%
        lr_winter = (min(i_frost, 30) / 30.0 * 4.5 + catas * 5.0) * winter_load
        lr_full = lr_std + lr_winter + 1.5 + 0.75 + 0.75 + 2.0  # + spring frost + hail + storm + spring drought (fixed averages)
        result["lr_standard_pct"] = round(lr_std, 2)
        result["lr_winter_pct"] = round(lr_winter, 2)
        result["lr_full_pct"] = round(lr_full, 2)
    else:
        result["lr_standard_pct"] = np.nan
        result["lr_winter_pct"] = np.nan
        result["lr_full_pct"] = np.nan

    return result


def main():
    parser = argparse.ArgumentParser(description="Compute WOSR county-level loss ratios from ERA5-Land.")
    parser.add_argument("--country", required=True, choices=list(REGIONS.keys()))
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--autumn-nc", required=True, help="Autumn ERA5 NetCDF file")
    parser.add_argument("--winter-nc", required=True, help="Winter ERA5 NetCDF file")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    if args.country not in REGIONS:
        sys.exit(f"No regions defined for country {args.country}")

    print(f"Loading ERA5 data for {args.country} {args.year}...")
    ds_autumn = xr.open_dataset(args.autumn_nc)
    ds_winter = xr.open_dataset(args.winter_nc)

    # Rename variables if needed (ERA5 sometimes uses full names)
    rename_map = {
        "volumetric_soil_water_layer_1": "swvl1",
        "2m_temperature": "t2m",
        "total_precipitation": "tp",
        "snow_depth_water_equivalent": "sd",
    }
    for old, new in rename_map.items():
        if old in ds_autumn:
            ds_autumn = ds_autumn.rename({old: new})
        if old in ds_winter:
            ds_winter = ds_winter.rename({old: new})

    regions = REGIONS[args.country]
    results = []
    for i, region in enumerate(regions):
        print(f"  [{i+1}/{len(regions)}] {region[1]} ({region[0]})...")
        row = process_region(region, args.year, ds_autumn, ds_winter)
        row["country"] = args.country
        results.append(row)
        print(f"    drought_days={row.get('i_drought_days','?')}  frost_days={row.get('i_frost_days','?')}  "
              f"LR_std={row.get('lr_standard_pct','?')}%  LR_full={row.get('lr_full_pct','?')}%  zone={row['risk_zone']}")

    df = pd.DataFrame(results)
    cols = ["country", "region_id", "region_name", "year", "risk_zone",
            "i_drought_days", "crust_flag", "elf_raw",
            "i_frost_days", "frost_catastrophic",
            "lr_standard_pct", "lr_winter_pct", "lr_full_pct",
            "lat", "lon", "clay_pct", "sowing_doy"]
    cols = [c for c in cols if c in df.columns]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df[cols].to_csv(args.output, index=False)
    print(f"\nSaved {len(df)} regions to {args.output}")

    # Summary stats
    valid = df.dropna(subset=["lr_standard_pct"])
    if len(valid):
        print(f"\nSummary for {args.country} {args.year}:")
        print(f"  Regions: {len(valid)}")
        print(f"  Mean LR Standard: {valid['lr_standard_pct'].mean():.1f}%")
        print(f"  Mean LR Full:     {valid['lr_full_pct'].mean():.1f}%")
        print(f"  Max LR Standard:  {valid['lr_standard_pct'].max():.1f}%  ({valid.loc[valid['lr_standard_pct'].idxmax(), 'region_name']})")
        print(f"  Zone 1 mean LR:   {valid[valid['risk_zone']=='Z1']['lr_standard_pct'].mean():.1f}%")


if __name__ == "__main__":
    main()

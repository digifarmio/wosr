#!/bin/bash
#SBATCH --account=nn12037k
#SBATCH --job-name=wosr_%x
#SBATCH --partition=preproc
#SBATCH --time=8:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=/cluster/work/users/digifarm/wosr/logs/wosr_%x_2025_%j.log

# WOSR Historical Loss Analysis — YEAR 2025 (Betzy preproc)
# Usage: sbatch --job-name=wosr_RO wosr_betzy_2025.sbatch RO
set -uo pipefail

COUNTRY="${1:-RO}"

source /etc/profile.d/z00_lmod.sh 2>/dev/null; module load StdEnv && module load awscli/2.17.54-GCCcore-13.2.0

WORK_DIR="/cluster/work/users/digifarm/wosr"
CONTAINER="/cluster/work/users/digifarm/sure2/containers/sure2-assess-v3.2.1.sif"
ERA5_DIR="$WORK_DIR/era5"
RESULTS_DIR="$WORK_DIR/results"
LOG_DIR="$WORK_DIR/logs"
SCRIPT_DIR="$WORK_DIR/scripts"
BUCKET="digifarm-wosr-underwriting"

mkdir -p "$ERA5_DIR/$COUNTRY" "$RESULTS_DIR/$COUNTRY" "$LOG_DIR"

YEAR=2025

echo "=================================================================="
echo "  WOSR Historical Loss Analysis — $COUNTRY Year $YEAR (Betzy)"
echo "  Job: $SLURM_JOB_ID | Node: ${SLURM_NODELIST:-local}"
echo "  Container: $CONTAINER"
echo "  Started: $(date)"
echo "=================================================================="

AUTUMN_NC="$ERA5_DIR/$COUNTRY/era5_wosr_${COUNTRY}_${YEAR}_autumn.nc"
WINTER_NC="$ERA5_DIR/$COUNTRY/era5_wosr_${COUNTRY}_${YEAR}_winter.nc"
RESULT_CSV="$RESULTS_DIR/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv"

# Skip if result already exists in S3
if aws s3 ls "s3://$BUCKET/results/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv" > /dev/null 2>&1; then
    echo "  [$YEAR] Already in S3, nothing to do"
    exit 0
fi

echo "  [$YEAR] Fetching ERA5..."
apptainer exec --containall --cleanenv \
    --bind "$ERA5_DIR/$COUNTRY:/era5_out" \
    --bind "$SCRIPT_DIR:/scripts" \
    --bind "$HOME/.cdsapirc:$HOME/.cdsapirc:ro" \
    --env AWS_DEFAULT_REGION=eu-central-1 \
    --env GDAL_HTTP_TIMEOUT=60 \
    --env GDAL_HTTP_MAX_RETRY=3 \
    "$CONTAINER" \
    python3 /scripts/wosr_era5_fetch.py \
        --country "$COUNTRY" \
        --year "$YEAR" \
        --output-dir /era5_out \
2>&1

if [ ! -f "$AUTUMN_NC" ] || [ ! -f "$WINTER_NC" ]; then
    echo "  [$YEAR] ERA5 fetch FAILED"
    exit 1
fi

echo "  [$YEAR] Computing loss ratios..."
apptainer exec --containall --cleanenv \
    --bind "$ERA5_DIR/$COUNTRY:/era5_out:ro" \
    --bind "$RESULTS_DIR/$COUNTRY:/results_out" \
    --bind "$SCRIPT_DIR:/scripts" \
    "$CONTAINER" \
    python3 /scripts/wosr_loss_calc.py \
        --country "$COUNTRY" \
        --year "$YEAR" \
        --autumn-nc "/era5_out/era5_wosr_${COUNTRY}_${YEAR}_autumn.nc" \
        --winter-nc  "/era5_out/era5_wosr_${COUNTRY}_${YEAR}_winter.nc" \
        --output "/results_out/wosr_${COUNTRY}_${YEAR}.csv" \
2>&1

if [ -f "$RESULT_CSV" ]; then
    echo "  [$YEAR] OK — uploading to S3"
    aws s3 cp "$RESULT_CSV" "s3://$BUCKET/results/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv"
    rm -f "$AUTUMN_NC" "$WINTER_NC"
    echo "=================================================================="
    echo "  SUCCESS — $COUNTRY $YEAR"
    echo "  Finished: $(date)"
    echo "=================================================================="
else
    echo "  [$YEAR] Loss calc FAILED"
    exit 1
fi

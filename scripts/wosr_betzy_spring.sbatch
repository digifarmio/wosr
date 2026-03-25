#!/bin/bash
#SBATCH --account=nn12037k
#SBATCH --job-name=wosr_sp_%x
#SBATCH --partition=preproc
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=/cluster/work/users/digifarm/wosr/logs/wosr_spring_%x_%j.log

# WOSR Spring Perils — fetch spring ERA5 + compute 4 additional perils (Betzy)
# Usage: sbatch --job-name=RO wosr_betzy_spring.sbatch RO
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

echo "=================================================================="
echo "  WOSR Spring Perils — $COUNTRY (Betzy)"
echo "  Job: $SLURM_JOB_ID | Node: ${SLURM_NODELIST:-local}"
echo "  Started: $(date)"
echo "=================================================================="

YEARS_START=1990
YEARS_END=2025
TOTAL_OK=0
TOTAL_FAIL=0

# First, sync existing results from S3
echo "  Syncing existing results from S3..."
aws s3 sync "s3://$BUCKET/results/$COUNTRY/" "$RESULTS_DIR/$COUNTRY/" --quiet

for YEAR in $(seq $YEARS_START $YEARS_END); do
    RESULT_CSV="$RESULTS_DIR/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv"

    if [ ! -f "$RESULT_CSV" ]; then
        echo "  [$YEAR] No base result CSV, skipping"
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
        continue
    fi

    # Check if already has spring perils (spring_frost_days column)
    if head -1 "$RESULT_CSV" | grep -q "spring_frost_days"; then
        echo "  [$YEAR] Already has spring perils, skipping"
        TOTAL_OK=$((TOTAL_OK + 1))
        continue
    fi

    echo "  [$YEAR] Fetching spring ERA5 + computing perils..."
    apptainer exec --containall --cleanenv \
        --bind "$ERA5_DIR/$COUNTRY:/era5_out" \
        --bind "$RESULTS_DIR/$COUNTRY:/results" \
        --bind "$SCRIPT_DIR:/scripts" \
        --bind "$HOME/.cdsapirc:$HOME/.cdsapirc:ro" \
        --env AWS_DEFAULT_REGION=eu-central-1 \
        --env GDAL_HTTP_TIMEOUT=120 \
        --env GDAL_HTTP_MAX_RETRY=5 \
        --env PYTHONPATH=/scripts \
        "$CONTAINER" \
        python3 /scripts/wosr_spring_perils.py \
            --country "$COUNTRY" \
            --year "$YEAR" \
            --output-dir /era5_out \
            --result-csv "/results/wosr_${COUNTRY}_${YEAR}.csv" \
    2>&1

    # Check if spring columns were added
    if head -1 "$RESULT_CSV" | grep -q "spring_frost_days"; then
        echo "  [$YEAR] OK — uploading to S3"
        aws s3 cp "$RESULT_CSV" "s3://$BUCKET/results/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv"
        TOTAL_OK=$((TOTAL_OK + 1))
    else
        echo "  [$YEAR] Spring perils FAILED"
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
    fi
done

echo ""
echo "=================================================================="
echo "  COMPLETE — $COUNTRY Spring Perils"
echo "  OK: $TOTAL_OK  |  Failed: $TOTAL_FAIL"
echo "  Finished: $(date)"
echo "=================================================================="

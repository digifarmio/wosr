#!/bin/bash
#SBATCH --account=nn12037k
#SBATCH --job-name=wosr_analysis
#SBATCH --partition=normal
#SBATCH --time=06:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=/cluster/work/users/digifarm/wosr/logs/wosr_%j.log

# WOSR Historical Loss Analysis — Saga
# Runs ERA5 fetch + loss calculation for all countries, 1995–2024
# Results uploaded to s3://digifarm-wosr-underwriting/

set -uo pipefail

module load awscli/2.17.54-GCCcore-13.2.0

WORK_DIR="/cluster/work/users/digifarm/wosr"
CONTAINER="/cluster/work/users/digifarm/sure2/containers/sure2-assess-v1.2.sif"
ERA5_DIR="$WORK_DIR/era5"
RESULTS_DIR="$WORK_DIR/results"
LOG_DIR="$WORK_DIR/logs"
SCRIPT_DIR="$WORK_DIR/scripts"
BUCKET="digifarm-wosr-underwriting"

mkdir -p "$ERA5_DIR" "$RESULTS_DIR" "$LOG_DIR"

echo "=================================================================="
echo "  WOSR Historical Loss Analysis"
echo "  Job: $SLURM_JOB_ID | Node: ${SLURM_NODELIST:-local}"
echo "  Container: $CONTAINER"
echo "  Started: $(date)"
echo "=================================================================="

# Countries to process (comma-free, one per line in the loop)
COUNTRIES=(RO MD PL HU CZ SK)
# UA is lower priority — added at end but can be skipped if time is short
YEARS_START=1995
YEARS_END=2024

TOTAL_OK=0
TOTAL_FAIL=0

for COUNTRY in "${COUNTRIES[@]}"; do
    echo ""
    echo "=== Country: $COUNTRY ==="
    mkdir -p "$ERA5_DIR/$COUNTRY" "$RESULTS_DIR/$COUNTRY"

    for YEAR in $(seq $YEARS_START $YEARS_END); do
        AUTUMN_NC="$ERA5_DIR/$COUNTRY/era5_wosr_${COUNTRY}_${YEAR}_autumn.nc"
        WINTER_NC="$ERA5_DIR/$COUNTRY/era5_wosr_${COUNTRY}_${YEAR}_winter.nc"
        RESULT_CSV="$RESULTS_DIR/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv"

        # Skip if result already exists in S3
        if aws s3 ls "s3://$BUCKET/results/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv" > /dev/null 2>&1; then
            echo "  [$YEAR] Already in S3, skipping"
            continue
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
            echo "  [$YEAR] ERA5 fetch FAILED — skipping loss calc"
            TOTAL_FAIL=$((TOTAL_FAIL + 1))
            continue
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
            # Clean up ERA5 files to save disk space (they're large)
            rm -f "$AUTUMN_NC" "$WINTER_NC"
            TOTAL_OK=$((TOTAL_OK + 1))
        else
            echo "  [$YEAR] Loss calc FAILED"
            TOTAL_FAIL=$((TOTAL_FAIL + 1))
        fi

    done

    echo "  Aggregating $COUNTRY results..."
    # Sync completed results from S3 to local (aggregate runs inside container, no boto3 needed)
    aws s3 sync "s3://$BUCKET/results/$COUNTRY/" "$RESULTS_DIR/$COUNTRY/" --quiet
    SUMMARY_DIR="$WORK_DIR/summaries"
    mkdir -p "$SUMMARY_DIR"
    apptainer exec --containall --cleanenv \
        --bind "$RESULTS_DIR:/results_in:ro" \
        --bind "$SUMMARY_DIR:/summaries_out" \
        --bind "$SCRIPT_DIR:/scripts" \
        "$CONTAINER" \
        python3 /scripts/wosr_aggregate.py \
            --country "$COUNTRY" \
            --results-dir /results_in \
            --output-dir /summaries_out \
    2>&1
    # Upload summary to S3
    if [ -f "$SUMMARY_DIR/${COUNTRY}_summary.csv" ]; then
        aws s3 cp "$SUMMARY_DIR/${COUNTRY}_summary.csv" \
            "s3://$BUCKET/summary/${COUNTRY}_summary.csv"
        echo "  Uploaded summary to S3"
    fi

done

echo ""
echo "=================================================================="
echo "  COMPLETE"
echo "  OK: $TOTAL_OK  |  Failed: $TOTAL_FAIL"
echo "  Finished: $(date)"
echo "=================================================================="

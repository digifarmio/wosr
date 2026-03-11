#!/bin/bash
#SBATCH --account=nn12037k
#SBATCH --job-name=wosr_cleanup
#SBATCH --partition=normal
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=/cluster/work/users/digifarm/wosr/logs/wosr_cleanup_%j.log

# Recompute specific country-years with fixed sigmoid calibration
# RO 1995-2003, HU 1995, CZ 1995 — all had wrong ELF_X0=10.0

set -uo pipefail
module load awscli/2.17.54-GCCcore-13.2.0

WORK_DIR="/cluster/work/users/digifarm/wosr"
CONTAINER="/cluster/work/users/digifarm/sure2/containers/sure2-assess-v1.2.sif"
ERA5_DIR="$WORK_DIR/era5"
RESULTS_DIR="$WORK_DIR/results"
SCRIPT_DIR="$WORK_DIR/scripts"
BUCKET="digifarm-wosr-underwriting"

echo "=== WOSR Cleanup: recompute with fixed sigmoid (ELF_X0=13.39) ==="
echo "Started: $(date)"

TOTAL_OK=0; TOTAL_FAIL=0

# List of country-years to recompute
declare -a JOBS=(
  "RO 1995" "RO 1996" "RO 1997" "RO 1998" "RO 1999"
  "RO 2000" "RO 2001" "RO 2002" "RO 2003"
  "HU 1995" "CZ 1995"
)

for JOB in "${JOBS[@]}"; do
  COUNTRY=$(echo $JOB | awk '{print $1}')
  YEAR=$(echo $JOB | awk '{print $2}')

  echo ""
  echo "=== $COUNTRY $YEAR ==="
  mkdir -p "$ERA5_DIR/$COUNTRY" "$RESULTS_DIR/$COUNTRY"

  AUTUMN_NC="$ERA5_DIR/$COUNTRY/era5_wosr_${COUNTRY}_${YEAR}_autumn.nc"
  WINTER_NC="$ERA5_DIR/$COUNTRY/era5_wosr_${COUNTRY}_${YEAR}_winter.nc"
  RESULT_CSV="$RESULTS_DIR/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv"

  echo "  Fetching ERA5..."
  apptainer exec --containall --cleanenv \
    --bind "$ERA5_DIR/$COUNTRY:/era5_out" \
    --bind "$SCRIPT_DIR:/scripts" \
    --bind "$HOME/.cdsapirc:$HOME/.cdsapirc:ro" \
    --env AWS_DEFAULT_REGION=eu-central-1 \
    "$CONTAINER" \
    python3 /scripts/wosr_era5_fetch.py \
      --country "$COUNTRY" --year "$YEAR" --output-dir /era5_out \
  2>&1

  if [ ! -f "$AUTUMN_NC" ] || [ ! -f "$WINTER_NC" ]; then
    echo "  ERA5 fetch FAILED"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    continue
  fi

  echo "  Computing loss ratios..."
  apptainer exec --containall --cleanenv \
    --bind "$ERA5_DIR/$COUNTRY:/era5_out:ro" \
    --bind "$RESULTS_DIR/$COUNTRY:/results_out" \
    --bind "$SCRIPT_DIR:/scripts" \
    "$CONTAINER" \
    python3 /scripts/wosr_loss_calc.py \
      --country "$COUNTRY" --year "$YEAR" \
      --autumn-nc "/era5_out/era5_wosr_${COUNTRY}_${YEAR}_autumn.nc" \
      --winter-nc "/era5_out/era5_wosr_${COUNTRY}_${YEAR}_winter.nc" \
      --output "/results_out/wosr_${COUNTRY}_${YEAR}.csv" \
  2>&1

  if [ -f "$RESULT_CSV" ]; then
    aws s3 cp "$RESULT_CSV" "s3://$BUCKET/results/$COUNTRY/wosr_${COUNTRY}_${YEAR}.csv"
    rm -f "$AUTUMN_NC" "$WINTER_NC"
    TOTAL_OK=$((TOTAL_OK + 1))
    echo "  OK — uploaded"
  else
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    echo "  Loss calc FAILED"
  fi
done

echo ""
echo "=== CLEANUP COMPLETE: OK=$TOTAL_OK FAIL=$TOTAL_FAIL ==="
echo "Finished: $(date)"

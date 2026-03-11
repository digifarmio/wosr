#!/bin/bash
# wosr_finalize.sh
# Run after all SLURM jobs complete:
# 1. Sync all S3 results locally
# 2. Run aggregate for all countries
# 3. Run analysis report
# 4. Sync summaries back to S3
set -uo pipefail

RESULTS_DIR="/home/ubuntu/wosr/results"
ANALYSIS_DIR="/home/ubuntu/wosr/analysis"
BUCKET="digifarm-wosr-underwriting"

echo "=== Syncing all S3 results locally ==="
for C in RO MD PL HU CZ SK; do
    mkdir -p "$RESULTS_DIR/$C"
    aws s3 sync "s3://$BUCKET/results/$C/" "$RESULTS_DIR/$C/" --quiet
    COUNT=$(ls "$RESULTS_DIR/$C"/*.csv 2>/dev/null | wc -l)
    echo "  $C: $COUNT CSVs"
done

echo ""
echo "=== Running aggregate for all countries ==="
python3 /home/ubuntu/wosr/scripts/wosr_aggregate.py \
    --all \
    --results-dir "$RESULTS_DIR" \
    --output-dir "$ANALYSIS_DIR"

echo ""
echo "=== Running analysis report ==="
python3 /home/ubuntu/wosr/scripts/wosr_analyze_results.py \
    --results-dir "$RESULTS_DIR" \
    --output-dir "$ANALYSIS_DIR"

echo ""
echo "=== Uploading summaries to S3 ==="
aws s3 sync "$ANALYSIS_DIR/" "s3://$BUCKET/analysis/" --quiet
echo "  Uploaded to s3://$BUCKET/analysis/"

echo ""
echo "DONE. Results in $ANALYSIS_DIR"

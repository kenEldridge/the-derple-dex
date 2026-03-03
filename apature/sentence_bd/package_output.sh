#!/usr/bin/env bash
# Package the SBD output for delivery.
# Creates: sbd_output_YYYY-MM-DD.zip containing all JSON files + README.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/output"
DATE=$(date +%Y-%m-%d)
ZIP_NAME="sbd_output_${DATE}.zip"

cd "$OUTPUT_DIR"
zip -j "$SCRIPT_DIR/$ZIP_NAME" README.md *.json

echo "Created: $ZIP_NAME ($(du -h "$SCRIPT_DIR/$ZIP_NAME" | cut -f1))"

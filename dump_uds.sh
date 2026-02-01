#!/usr/bin/env bash

# Dump all files under obd/uds into a single text file (uds_dump.txt),
# with clear file headers.
#
# Usage:
#   ./dump_uds.sh
#   ./dump_uds.sh [root_dir] [output_file]
#
# Defaults:
#   root_dir   = obd/uds
#   outputFile = uds_dump.txt

ROOT_DIR="${1:-obd/uds}"
OUT_FILE="${2:-uds_dump.txt}"

if [ ! -d "$ROOT_DIR" ]; then
  echo "Directory '$ROOT_DIR' not found (pwd: $(pwd))" >&2
  exit 1
fi

# Truncate/create the output file first
: > "$OUT_FILE" || {
  echo "Cannot write to '$OUT_FILE'" >&2
  exit 1
}

# Redirect all following output to the file
exec >"$OUT_FILE"

# You won't see this in terminal, it'll go into uds_dump.txt:
echo "# UDS dump generated from '$ROOT_DIR'"
echo "# Working directory: $(pwd)"
echo ""

# Find all regular files under ROOT_DIR, skip __pycache__ and dotfiles, then sort.
find "$ROOT_DIR" -type f \
  ! -path "*/__pycache__/*" \
  ! -name ".*" \
  | sort \
  | while IFS= read -r file; do
      echo "===== FILE: $file ====="
      cat "$file"
      echo ""
      echo ""
    done

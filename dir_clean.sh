#!/bin/bash
set -euo pipefail

# Directory Cleanup Script for WormCat
# Cleans generated run directories and temporary failure files across:
#   1. worm_cat/static/dynamic (run outputs, uploaded data files)
#   2. worm_cat                (leftover temporary files/dirs from failed runs)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default target directories to clean
DEFAULT_TARGETS=(
  "$SCRIPT_DIR/worm_cat/static/dynamic"
  "$SCRIPT_DIR/worm_cat"
)

# Date/Month criteria matching timestamps (%b-%d-%Y)
CRITERIA=(
  "Jan-" "Feb-" "Mar-" "Apr-" "May-" "Jun-"
  "Jul-" "Aug-" "Sep-" "Oct-" "Nov-" "Dec-"
  "jan-" "feb-" "mar-" "apr-" "may-" "jun-"
  "jul-" "aug-" "sep-" "oct-" "nov-" "dec-"
)

# Protected items that MUST NOT be deleted under any circumstances
PROTECTED_ITEMS=(
  "static"
  "templates"
  "utils"
  "services"
  "tasks"
  "logs"
  "wormcat_batch"
  "__pycache__"
  "forms.py"
  "worm_cat.R"
  "worm_cat_app.py"
  "test_wormcat_r.py"
  "run.sh"
  "run_celery.sh"
  "stop.sh"
  "active_annotation_file.json"
  "async_email_timeout.txt"
  "output.csv"
  "run_data_analysis.sh"
  "sunburst.templet"
)

DRY_RUN=false
TARGETS=()

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--dry-run|-n] [directory_paths...]"
      echo "Cleans generated timestamped runs and leftover failure files."
      echo "Defaults to cleaning both 'worm_cat/static/dynamic' and 'worm_cat'."
      exit 0
      ;;
    *)
      TARGETS+=("$1")
      shift
      ;;
  esac
done

# If no target directories passed, use defaults
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("${DEFAULT_TARGETS[@]}")
fi

function is_protected() {
  local item_name="$1"
  for protected in "${PROTECTED_ITEMS[@]}"; do
    if [[ "$item_name" == "$protected" ]]; then
      return 0
    fi
  done
  # Also protect permanent user tracking logs (e.g. users.txt, users_aug_2026.txt)
  if [[ "$item_name" == users*.txt ]]; then
    return 0
  fi
  return 1
}

function matches_criteria() {
  local item_name="$1"

  # Match month criteria (e.g., Dan_Higgins_Aug-16-..., Aug-16-..., worm-cat_Aug-16-...)
  for crit in "${CRITERIA[@]}"; do
    if [[ "$item_name" == *"$crit"* ]]; then
      return 0
    fi
  done

  # Match specific failure leftover patterns
  if [[ "$item_name" == worm-cat_*.csv || "$item_name" == worm_cat_output* || "$item_name" == worm_cat_output*.zip ]]; then
    return 0
  fi

  return 1
}

deleted_dirs=0
deleted_files=0

shopt -s nullglob

for target_dir in "${TARGETS[@]}"; do
  # Resolve path if relative
  if [[ "$target_dir" != /* ]]; then
    target_dir="$PWD/$target_dir"
  fi

  if [[ ! -d "$target_dir" ]]; then
    echo "Directory not found, skipping: $target_dir"
    continue
  fi

  echo "Scanning: $target_dir"

  for item_path in "$target_dir"/*; do
    [[ -e "$item_path" ]] || continue
    item_name="$(basename "$item_path")"

    # Skip protected assets/source files
    if is_protected "$item_name"; then
      continue
    fi

    # Check if item matches cleanup criteria
    if matches_criteria "$item_name"; then
      if [[ -d "$item_path" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
          echo "  [DRY-RUN] Would delete directory: $item_name"
        else
          echo "  Deleting directory: $item_name"
          rm -rf "$item_path"
        fi
        ((deleted_dirs++))
      elif [[ -f "$item_path" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
          echo "  [DRY-RUN] Would delete file: $item_name"
        else
          echo "  Deleting file: $item_name"
          rm -f "$item_path"
        fi
        ((deleted_files++))
      fi
    fi
  done
done

shopt -u nullglob

echo "--------------------------------------------------"
if [[ "$DRY_RUN" == true ]]; then
  echo "Dry-run complete. Would remove: $deleted_dirs directories, $deleted_files files."
else
  echo "Cleanup complete. Removed: $deleted_dirs directories, $deleted_files files."
fi

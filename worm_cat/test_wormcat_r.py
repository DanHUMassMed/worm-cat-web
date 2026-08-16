#!/usr/bin/env python3
"""
Test runner for worm_cat/worm_cat.R

Verifies:
1. Rscript and required R packages (wormcat, argparse) are installed.
2. Direct execution of worm_cat.R with sample dataset (sams-1_up.csv).
3. Generation of expected output artifacts (fisher cat1, cat2, cat3 csv files).
"""

import sys
import shutil
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Paths relative to worm_cat/ directory
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SAMPLE_INPUT = SCRIPT_DIR / "static" / "download" / "sams-1_up.csv"
DYNAMIC_DIR = SCRIPT_DIR / "static" / "dynamic"
R_SCRIPT = SCRIPT_DIR / "worm_cat.R"

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"


def check_r_environment() -> bool:
    print(f"{BLUE}[1/3] Checking R environment and packages...{NC}")
    if not shutil.which("Rscript"):
        print(f"{RED}[ERROR] 'Rscript' executable not found in PATH.{NC}")
        print("Please install R: https://www.r-project.org/")
        return False

    # Check R packages
    check_cmd = [
        "Rscript",
        "-e",
        "req <- c('argparse', 'wormcat'); "
        "missing <- req[!req %in% installed.packages()[, 'Package']]; "
        "if (length(missing) > 0) { cat(paste('MISSING:', paste(missing, collapse=','))); quit(status=1) } "
        "else { cat('OK') }"
    ]
    res = subprocess.run(check_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"{RED}[ERROR] Missing required R packages.{NC}")
        if "MISSING:" in res.stdout:
            missing_pkgs = res.stdout.strip().replace("MISSING:", "").split(",")
            print(f"Missing: {missing_pkgs}")
        print("\nTo install required R packages, run in R:")
        print("  install.packages(c('argparse', 'devtools', 'ggplot2', 'data.table'))")
        print("  devtools::install_github('dphiggs01/wormcat')")
        return False

    print(f"{GREEN}✓ Rscript and required packages (wormcat, argparse) are ready.{NC}")
    return True


def run_wormcat_r_test(input_file: Path, title: str = "test_rgs", annotation: str = "whole_genome_v2_nov-11-2021.csv", input_type: str = "Wormbase.ID", keep_output: bool = False) -> bool:
    print(f"\n{BLUE}[2/3] Executing worm_cat.R test run...{NC}")
    if not input_file.exists():
        print(f"{RED}[ERROR] Input sample file not found: {input_file}{NC}")
        return False

    timestamp = datetime.now().strftime("%b-%d-%Y-%H_%M_%S")
    out_dir_name = f"test_run_{timestamp}"

    # Ensure dynamic dir exists
    DYNAMIC_DIR.mkdir(parents=True, exist_ok=True)

    final_output_path = DYNAMIC_DIR / out_dir_name

    cmd = [
        "Rscript",
        str(R_SCRIPT),
        "--file", str(input_file),
        "--title", title,
        "--out_dir", str(final_output_path),
        "--annotation_file", annotation,
        "--input_type", input_type,
    ]

    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {SCRIPT_DIR}\n")

    res = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)

    if res.stdout:
        print(f"--- R Output ---\n{res.stdout.strip()}\n----------------")
    if res.stderr:
        print(f"--- R Messages/Warnings ---\n{res.stderr.strip()}\n---------------------------")

    # The R script moves out_dir to ./static/dynamic/<out_dir>
    final_output_path = DYNAMIC_DIR / out_dir_name

    print(f"\n{BLUE}[3/3] Verifying generated output files...{NC}")
    if not final_output_path.exists() or not final_output_path.is_dir():
        print(f"{RED}[FAIL] Expected output directory does not exist: {final_output_path}{NC}")
        return False

    expected_files = [
        "rgs_fisher_cat1_apv.csv",
        "rgs_fisher_cat2_apv.csv",
        "rgs_fisher_cat3_apv.csv",
    ]

    all_passed = True
    for expected in expected_files:
        p = final_output_path / expected
        if p.exists() and p.stat().st_size > 0:
            lines = p.read_text().strip().split("\n")
            row_count = max(0, len(lines) - 1)
            print(f"{GREEN}✓ Found {expected} ({row_count} data rows, {p.stat().st_size} bytes){NC}")
        else:
            # Check alternative naming if apv suffix not present
            alt = final_output_path / expected.replace("_apv.csv", ".csv")
            if alt.exists() and alt.stat().st_size > 0:
                print(f"{GREEN}✓ Found {alt.name} ({alt.stat().st_size} bytes){NC}")
            else:
                print(f"{RED}✗ Missing or empty expected file: {expected}{NC}")
                all_passed = False

    if all_passed:
        print(f"\n{GREEN}========================================={NC}")
        print(f"{GREEN}SUCCESS: worm_cat.R completed and produced valid results!{NC}")
        print(f"Output directory: {final_output_path}")
        print(f"{GREEN}========================================={NC}")
    else:
        print(f"\n{RED}FAILURE: Output files did not match expected structure.{NC}")

    if not keep_output and final_output_path.exists():
        print(f"\nCleaning up temporary test directory: {final_output_path}")
        shutil.rmtree(final_output_path, ignore_errors=True)
    elif keep_output:
        print(f"\nKept test output at: {final_output_path}")

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Test execution of worm_cat/worm_cat.R")
    parser.add_argument("-f", "--file", type=Path, default=SAMPLE_INPUT, help="Input CSV file to process (default: sams-1_up.csv)")
    parser.add_argument("-t", "--title", default="test_rgs", help="Title for analysis (default: test_rgs)")
    parser.add_argument("-a", "--annotation", default="whole_genome_v2_nov-11-2021.csv", help="Annotation file name")
    parser.add_argument("-i", "--input-type", default="Wormbase.ID", choices=["Wormbase.ID", "Sequence ID"], help="Input gene ID type")
    parser.add_argument("--keep", action="store_true", help="Keep generated test output directory")
    args = parser.parse_args()

    if not check_r_environment():
        sys.exit(1)

    success = run_wormcat_r_test(
        input_file=args.file,
        title=args.title,
        annotation=args.annotation,
        input_type=args.input_type,
        keep_output=args.keep,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

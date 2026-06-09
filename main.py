"""Zone 1 project entry point.

Run without arguments to rebuild the CSVs and print the analysis summary.
"""

from __future__ import annotations

import sys

import pandas as pd

from analyzer import main as analyze_main
from scraper import BASE_DISH_CSV, VARIANTS_CSV, main as build_main


def verify_outputs() -> None:
    for csv_path in (BASE_DISH_CSV, VARIANTS_CSV):
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing generated file: {csv_path}")
        frame = pd.read_csv(csv_path)
        print(f"Verified {csv_path.name}: {frame.shape[0]} rows x {frame.shape[1]} columns")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in {"all", "--build", "--scrape"}:
        build_main()
        verify_outputs()

    if mode in {"all", "--analyze"}:
        analyze_main()


if __name__ == "__main__":
    main()

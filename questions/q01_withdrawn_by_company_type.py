#!/usr/bin/env python3
"""Q1 — Withdrawn IPOs by company type."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ipo_scoop import (
    SOURCE_URL,
    add_offered_value,
    company_type,
    load_recently_filed,
)


def withdrawn_ipos(df: pd.DataFrame) -> pd.DataFrame:
    out = df.loc[df["Expected To Trade"] == "Withdrawn"].copy()
    out["Company Type"] = out["Company"].map(company_type)
    return add_offered_value(out)


def summarize(withdrawn: pd.DataFrame) -> pd.Series:
    return (
        withdrawn.groupby("Company Type", sort=False)["Shares_offered_value"]
        .sum()
        .sort_values(ascending=False)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=SOURCE_URL)
    parser.add_argument("--before", default=None, help="File-date cutoff YYYY-MM-DD")
    parser.add_argument("--snapshot", default=None)
    args = parser.parse_args()

    raw = load_recently_filed(args.source)
    if args.snapshot:
        Path(args.snapshot).parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(args.snapshot, index=False)

    withdrawn = withdrawn_ipos(raw)
    if args.before:
        withdrawn = withdrawn[
            pd.to_datetime(withdrawn["File Date"]) < pd.Timestamp(args.before)
        ]

    totals = summarize(withdrawn)
    print(f"Q1 withdrawn rows: {len(withdrawn)}")
    print()
    print(totals.to_string())
    print()
    print(
        "Highest withdrawn IPO value: "
        f"{totals.index[0]} with {float(totals.iloc[0]):.4f} ($ millions)"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Withdrawn IPO value by company type (IPOScoop recently filed list)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_URL = "https://www.iposcoop.com/ipos-recently-filed"


def parse_price(value) -> float:
    """Extract a numeric price from strings like '$8.00'; '-' / missing -> NaN."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if text in {"", "-", "–", "—", "nan", "None"}:
        return np.nan
    match = re.search(r"[-+]?\d*\.?\d+", text.replace(",", ""))
    return float(match.group()) if match else np.nan


def to_numeric(value) -> float:
    """Convert shares / estimated volume fields, stripping $ and commas."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip().replace("$", "").replace(",", "")
    if text in {"", "-", "–", "—", "nan", "None"}:
        return np.nan
    try:
        return float(text)
    except ValueError:
        match = re.search(r"[-+]?\d*\.?\d+", text)
        return float(match.group()) if match else np.nan


def company_type(name: str) -> str:
    """Assign the first matching company-type rule (order matters)."""
    text = str(name)
    if "Technologies" in text:
        return "Technologies"
    if (
        "Acquisition Corp" in text
        or "Acquisition Corporation" in text
        or "Corp" in text
    ):
        return "Acquisition Corp"
    if "Inc" in text or "Incorporated" in text:
        return "Inc."
    if "Group" in text:
        return "Group"
    if "Ltd" in text or "Limited" in text:
        return "Limited"
    if "Holdings" in text or "Holding" in text:
        return "Holdings"
    return "Other"


def load_recently_filed(source: str) -> pd.DataFrame:
    path = Path(source)
    if path.suffix.lower() == ".csv" and path.exists():
        return pd.read_csv(path)
    tables = pd.read_html(source)
    if not tables:
        raise RuntimeError(f"No HTML tables found in {source}")
    return tables[0]


def withdrawn_ipos(df: pd.DataFrame) -> pd.DataFrame:
    out = df.loc[df["Expected To Trade"] == "Withdrawn"].copy()
    out["Company Type"] = out["Company"].map(company_type)
    out["Avg_price"] = out[["Price Low", "Price High"]].map(parse_price).mean(axis=1)
    shares = out["Shares (millions)"].map(to_numeric)
    est_vol = out["Est $ Vol (millions)"].map(to_numeric)
    offered = shares * out["Avg_price"]
    out["Shares_offered_value"] = np.where(offered.notna(), offered, est_vol)
    return out


def summarize(withdrawn: pd.DataFrame) -> pd.Series:
    return (
        withdrawn.groupby("Company Type", sort=False)["Shares_offered_value"]
        .sum()
        .sort_values(ascending=False)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=SOURCE_URL,
        help="HTML URL or local file passed to pandas.read_html()",
    )
    parser.add_argument(
        "--before",
        default=None,
        help="Optional inclusive-exclusive file-date cutoff (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--snapshot",
        default=None,
        help="Optional path to write the raw recently-filed table as CSV.",
    )
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
    top_type = totals.index[0]
    top_value = float(totals.iloc[0])

    print(f"Withdrawn rows: {len(withdrawn)}")
    print()
    print(totals.to_string())
    print()
    print(
        f"Highest withdrawn IPO value: {top_type} "
        f"with {top_value:.4f} ($ millions)"
    )


if __name__ == "__main__":
    main()

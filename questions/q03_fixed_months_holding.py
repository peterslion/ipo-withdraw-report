#!/usr/bin/env python3
"""Q3 — Optimal 1–12 month hold after IPO (median growth from first close)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from questions.q02_median_sharpe_2025_ipos import (  # noqa: E402
    PRICINGS_URL,
    download_prices,
    engineer,
    filter_ipos,
    load_pricings,
)

GROWTH_COLS = [f"future_growth_{m}_m" for m in range(1, 13)]


def add_future_growth(stocks_df: pd.DataFrame) -> pd.DataFrame:
    out = stocks_df.copy()
    grouped = out.groupby("Ticker")["Close"]
    for months in range(1, 13):
        days = months * 21
        out[f"future_growth_{months}_m"] = grouped.transform(
            lambda s, d=days: s.shift(-d) / s
        )
    return out


def ipo_entry_growth(stocks_df: pd.DataFrame) -> pd.DataFrame:
    """Keep each ticker's first trading day after joining min_date to the panel."""
    featured = add_future_growth(stocks_df)
    min_dates = (
        featured.groupby("Ticker", as_index=False)["Date"]
        .min()
        .rename(columns={"Date": "min_date"})
    )
    return featured.merge(
        min_dates,
        left_on=["Ticker", "Date"],
        right_on=["Ticker", "min_date"],
        how="inner",
    )


def load_close(path: str) -> pd.DataFrame:
    close = pd.read_csv(path, index_col=0, parse_dates=True)
    return close.dropna(axis=1, how="all")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pricings", default=str(ROOT / "data" / "ipos_2025_pricings.csv"))
    parser.add_argument(
        "--close",
        default=str(ROOT / "data" / "stocks_close.csv"),
        help="Wide Close panel CSV from Q2; downloads from Yahoo if missing.",
    )
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2026-09-13")
    parser.add_argument("--snapshot", default=None)
    args = parser.parse_args()

    close_path = Path(args.close)
    if close_path.exists():
        close = load_close(str(close_path))
        print(f"Loaded Close panel {close_path} ({close.shape[1]} tickers)")
    else:
        source = args.pricings if Path(args.pricings).exists() else PRICINGS_URL
        pricings = load_pricings(source)
        tickers = filter_ipos(pricings)["Symbol"].astype(str).str.strip().tolist()
        close = download_prices(tickers, start=args.start, end=args.end)
        print(f"Downloaded Close panel ({close.shape[1]} tickers)")

    stocks_df = engineer(close)
    entry = ipo_entry_growth(stocks_df)
    print(f"IPO entry rows: {len(entry)}")

    desc = entry[GROWTH_COLS].describe()
    print()
    print(desc.to_string())

    medians = entry[GROWTH_COLS].median()
    best_col = medians.idxmax()
    best_month = int(best_col.split("_")[2])
    best_median = float(medians.max())

    print()
    print("Median future growth by holding month:")
    print(medians.to_string())
    print()
    print(
        f"Optimal holding period: {best_month} month(s) "
        f"with median growth {best_median:.6f}"
    )
    print(
        "Mean vs median at that horizon: "
        f"mean={float(entry[best_col].mean()):.4f}  "
        f"median={best_median:.6f}"
    )

    if args.snapshot:
        Path(args.snapshot).parent.mkdir(parents=True, exist_ok=True)
        cols = ["Ticker", "min_date", "Close", *GROWTH_COLS]
        entry[cols].to_csv(args.snapshot, index=False)


if __name__ == "__main__":
    main()

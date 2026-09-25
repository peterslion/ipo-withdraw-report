#!/usr/bin/env python3
"""Q2 — Median Sharpe ratio for 2025 IPOs listed before 1 Sep 2025, as of 11 Sep 2026."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PRICINGS_URL = "https://www.iposcoop.com/2025-pricings/"
ASOF = "2026-09-11"
RISK_FREE = 0.05


def parse_return_pct(value) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().replace("%", "").replace(",", "")
    if text in {"", "-", "–", "—"}:
        return np.nan
    return float(text)


def load_pricings(source: str) -> pd.DataFrame:
    path = Path(source)
    if path.suffix.lower() == ".csv" and path.exists():
        df = pd.read_csv(path)
    else:
        tables = pd.read_html(source)
        if not tables:
            raise RuntimeError(f"No HTML tables found in {source}")
        df = tables[0]
    df["Offer Date"] = pd.to_datetime(df["Offer Date"])
    df["Return_pct"] = df["Return"].map(parse_return_pct)
    return df


def filter_ipos(pricings: pd.DataFrame) -> pd.DataFrame:
    return pricings.loc[
        (pricings["Offer Date"] < "2025-09-01") & (pricings["Return_pct"] != 0)
    ].copy()


def download_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        threads=True,
        group_by="column",
        progress=False,
    )
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    if isinstance(close, pd.Series):
        close = close.to_frame()
    close = close.dropna(axis=1, how="all")
    close.index = pd.to_datetime(close.index)
    return close


def engineer(close: pd.DataFrame) -> pd.DataFrame:
    """Long OHLCV-style frame with the assignment's growth / vol / Sharpe fields."""
    stocks_df = (
        close.stack(future_stack=True)
        .rename("Close")
        .rename_axis(["Date", "Ticker"])
        .reset_index()
        .dropna(subset=["Close"])
        .sort_values(["Ticker", "Date"])
    )
    grouped = stocks_df.groupby("Ticker")["Close"]
    stocks_df["growth_252d"] = grouped.transform(lambda s: s / s.shift(252))
    stocks_df["volatility"] = grouped.transform(
        lambda s: s.rolling(30).std() * np.sqrt(252)
    )
    stocks_df["Sharpe"] = (stocks_df["growth_252d"] - RISK_FREE) / stocks_df["volatility"]
    return stocks_df


def asof_snapshot(stocks_df: pd.DataFrame, asof: str) -> pd.DataFrame:
    day = stocks_df.loc[stocks_df["Date"] == pd.Timestamp(asof)].copy()
    if day.empty:
        available = stocks_df["Date"].drop_duplicates().sort_values()
        raise RuntimeError(
            f"No rows for {asof}. Last dates: {available.tail(5).tolist()}"
        )
    return day


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pricings", default=str(ROOT / "data" / "ipos_2025_pricings.csv"))
    parser.add_argument("--asof", default=ASOF)
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument(
        "--end",
        default="2026-09-13",
        help="yfinance end date (exclusive-style upper bound; include the as-of day).",
    )
    parser.add_argument("--snapshot", default=None, help="Write the as-of snapshot CSV.")
    parser.add_argument(
        "--close-out",
        default=None,
        help="Optional path to write the wide Close panel CSV.",
    )
    args = parser.parse_args()

    source = args.pricings
    if not Path(source).exists():
        source = PRICINGS_URL

    pricings = load_pricings(source)
    print(f"2025 pricings rows: {len(pricings)}")
    ipos = filter_ipos(pricings)
    tickers = ipos["Symbol"].astype(str).str.strip().tolist()
    print(f"Filtered IPOs (offer < 2025-09-01, return != 0%): {len(tickers)}")

    close = download_prices(tickers, start=args.start, end=args.end)
    print(f"Yahoo tickers with prices: {close.shape[1]}")
    if args.close_out:
        Path(args.close_out).parent.mkdir(parents=True, exist_ok=True)
        close.to_csv(args.close_out)

    stocks_df = engineer(close)
    snap = asof_snapshot(stocks_df, args.asof)
    if args.snapshot:
        Path(args.snapshot).parent.mkdir(parents=True, exist_ok=True)
        snap.to_csv(args.snapshot, index=False)

    print()
    print(f"As-of {args.asof} describe():")
    print(snap[["Close", "growth_252d", "volatility", "Sharpe"]].describe().to_string())
    print()
    print(f"252-day milestone (growth_252d not NA): {snap['growth_252d'].notna().sum()}")
    print(
        f"median growth_252d={snap['growth_252d'].median():.6f}  "
        f"mean growth_252d={snap['growth_252d'].mean():.6f}"
    )
    median_sharpe = float(snap["Sharpe"].median())
    print(f"Median Sharpe ratio: {median_sharpe:.6f}")


if __name__ == "__main__":
    main()

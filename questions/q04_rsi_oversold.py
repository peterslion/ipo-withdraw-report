#!/usr/bin/env python3
"""Q4 — RSI < 30 oversold strategy: $1000 per signal, 30-day forward growth."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILE_ID = "1grCTCzMZKY5sJRtdbLVCXg8JXA8VPyg-"
DRIVE_URL = f"https://drive.google.com/uc?id={FILE_ID}"
START = "2000-01-01"
END = "2025-06-01"
RSI_THRESHOLD = 30.0
INVESTMENT = 1000.0


def ensure_parquet(path: Path) -> Path:
    if path.exists():
        return path
    import gdown

    path.parent.mkdir(parents=True, exist_ok=True)
    gdown.download(DRIVE_URL, str(path), quiet=False)
    return path


def select_trades(df: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(df["Date"])
    mask = (
        (dates >= START)
        & (dates <= END)
        & (df["rsi"] < RSI_THRESHOLD)
        & df["growth_future_30d"].notna()
    )
    return df.loc[mask].copy()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parquet",
        default=str(ROOT / "data" / "data.parquet"),
        help="Brotli parquet of precomputed indicators (downloaded if missing).",
    )
    parser.add_argument("--snapshot", default=None, help="Optional trades CSV.")
    args = parser.parse_args()

    parquet = ensure_parquet(Path(args.parquet))
    df = pd.read_parquet(parquet, engine="pyarrow")
    trades = select_trades(df)
    net_income = INVESTMENT * (trades["growth_future_30d"] - 1).sum()
    avg_return = float(trades["growth_future_30d"].mean() - 1)
    win_rate = float((trades["growth_future_30d"] > 1).mean())
    n_25 = int(
        (
            (pd.to_datetime(df["Date"]) >= START)
            & (pd.to_datetime(df["Date"]) <= END)
            & (df["rsi"] < 25)
            & df["growth_future_30d"].notna()
        ).sum()
    )

    print(f"Rows in panel: {len(df):,}")
    print(f"RSI < 25 trades in window: {n_25:,}")
    print(f"RSI < {RSI_THRESHOLD:.0f} trades in window: {len(trades):,}")
    print(f"Average 30-day return: {avg_return:.4%}")
    print(f"Win rate: {win_rate:.2%}")
    print(f"Net income: ${net_income:,.2f}")
    print(f"Net income ($ thousands): {net_income / 1000:.4f}")

    if args.snapshot:
        Path(args.snapshot).parent.mkdir(parents=True, exist_ok=True)
        cols = [c for c in ("Date", "Ticker", "rsi", "growth_future_30d", "Close_x") if c in trades.columns]
        trades[cols].to_csv(args.snapshot, index=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Simulate RSI < 30 entries with alternate exits vs the 30-day homework hold."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from questions.q04_rsi_oversold import (  # noqa: E402
    DRIVE_URL,
    END,
    INVESTMENT,
    RSI_THRESHOLD,
    START,
    ensure_parquet,
)

# Named experiments: (rsi_exit, stop_loss, max_holding_days)
VARIANTS: dict[str, dict] = {
    "hold_21d": {"rsi_exit": None, "stop": None, "max_days": 21},
    "hold_30d": {"rsi_exit": None, "stop": None, "max_days": 30},
    "rsi_50": {"rsi_exit": 50.0, "stop": None, "max_days": None},
    "rsi_40": {"rsi_exit": 40.0, "stop": None, "max_days": None},
    "rsi_50_or_30d": {"rsi_exit": 50.0, "stop": None, "max_days": 30},
    "rsi_50_or_60d": {"rsi_exit": 50.0, "stop": None, "max_days": 60},
    "stop10_or_30d": {"rsi_exit": None, "stop": 0.10, "max_days": 30},
    "rsi_50_or_stop10": {"rsi_exit": 50.0, "stop": 0.10, "max_days": None},
    "rsi_50_or_stop10_or_60d": {"rsi_exit": 50.0, "stop": 0.10, "max_days": 60},
}


def simulate_ticker(
    close: np.ndarray,
    rsi: np.ndarray,
    in_window: np.ndarray,
    rsi_exit: float | None,
    stop: float | None,
    max_days: int | None,
) -> list[tuple[int, int, float, str]]:
    """Return (entry_i, exit_i, growth, reason) for one ticker's arrays."""
    n = len(close)
    trades: list[tuple[int, int, float, str]] = []
    for i in range(n - 1):
        if not in_window[i]:
            continue
        if not np.isfinite(rsi[i]) or rsi[i] >= RSI_THRESHOLD:
            continue
        if not np.isfinite(close[i]) or close[i] <= 0:
            continue
        exit_j = None
        reason = "eod"
        last = min(n - 1, i + max_days if max_days is not None else n - 1)
        for j in range(i + 1, last + 1):
            px = close[j]
            if not np.isfinite(px) or px <= 0:
                continue
            ret = px / close[i] - 1.0
            if stop is not None and ret <= -stop:
                exit_j, reason = j, "stop"
                break
            if rsi_exit is not None and np.isfinite(rsi[j]) and rsi[j] >= rsi_exit:
                exit_j, reason = j, "rsi"
                break
            if max_days is not None and (j - i) >= max_days:
                exit_j, reason = j, "time"
                break
        if exit_j is None:
            # no valid later price
            continue
        growth = close[exit_j] / close[i]
        trades.append((i, exit_j, float(growth), reason))
    return trades


def run_variant(panel: pd.DataFrame, spec: dict) -> pd.DataFrame:
    rows: list[dict] = []
    for ticker, g in panel.groupby("Ticker", sort=False):
        g = g.sort_values("Date")
        close = g["Close_x"].to_numpy(dtype=float)
        rsi = g["rsi"].to_numpy(dtype=float)
        dates = g["Date"].to_numpy()
        in_window = (g["Date"] >= START).to_numpy() & (g["Date"] <= END).to_numpy()
        for i, j, growth, reason in simulate_ticker(
            close,
            rsi,
            in_window,
            spec["rsi_exit"],
            spec["stop"],
            spec["max_days"],
        ):
            rows.append(
                {
                    "Ticker": ticker,
                    "entry_date": dates[i],
                    "exit_date": dates[j],
                    "hold_days": j - i,
                    "growth": growth,
                    "exit_reason": reason,
                }
            )
    return pd.DataFrame(rows)


def summarize(trades: pd.DataFrame, name: str) -> dict:
    if trades.empty:
        return {"variant": name, "n": 0}
    pnl = INVESTMENT * (trades["growth"] - 1.0)
    wins = trades["growth"] > 1
    losses = trades["growth"] < 1
    gross_win = float(pnl[wins].sum()) if wins.any() else 0.0
    gross_loss = float(pnl[losses].sum()) if losses.any() else 0.0
    pf = gross_win / -gross_loss if gross_loss < 0 else np.inf
    # peak overlapping $1000 tickets (calendar span)
    peak = 0
    if len(trades):
        events = []
        for e, x in zip(pd.to_datetime(trades["entry_date"]), pd.to_datetime(trades["exit_date"])):
            events.append((e, 1))
            events.append((x, -1))
        events.sort()
        open_n = 0
        for _, delta in events:
            open_n += delta
            peak = max(peak, open_n)
    reasons = trades["exit_reason"].value_counts().to_dict()
    return {
        "variant": name,
        "n": int(len(trades)),
        "win_rate": float(wins.mean()),
        "avg_return": float(trades["growth"].mean() - 1),
        "median_return": float(trades["growth"].median() - 1),
        "avg_hold_days": float(trades["hold_days"].mean()),
        "median_hold_days": float(trades["hold_days"].median()),
        "net_income": float(pnl.sum()),
        "net_thousands": float(pnl.sum() / 1000),
        "usd_per_trade": float(pnl.mean()),
        "profit_factor": float(pf),
        "peak_tickets": int(peak),
        "peak_capital": int(peak) * INVESTMENT,
        "exit_rsi_pct": reasons.get("rsi", 0) / len(trades),
        "exit_stop_pct": reasons.get("stop", 0) / len(trades),
        "exit_time_pct": reasons.get("time", 0) / len(trades),
        "exit_eod_pct": reasons.get("eod", 0) / len(trades),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", default=str(ROOT / "data" / "data.parquet"))
    parser.add_argument(
        "--summary",
        default=str(ROOT / "data" / "q04_exit_simulation_summary.csv"),
    )
    args = parser.parse_args()

    parquet = Path(args.parquet)
    if not parquet.exists():
        import gdown

        parquet.parent.mkdir(parents=True, exist_ok=True)
        gdown.download(DRIVE_URL, str(parquet), quiet=False)

    cols = ["Date", "Ticker", "Close_x", "rsi"]
    panel = pd.read_parquet(parquet, engine="pyarrow", columns=cols)
    panel["Date"] = pd.to_datetime(panel["Date"])

    summaries = []
    for name, spec in VARIANTS.items():
        trades = run_variant(panel, spec)
        summaries.append(summarize(trades, name))
        print(
            f"{name:24s} n={summaries[-1].get('n', 0):5d}  "
            f"net=${summaries[-1].get('net_income', 0):10,.0f}  "
            f"wr={summaries[-1].get('win_rate', 0):6.1%}  "
            f"avg={summaries[-1].get('avg_return', 0):7.2%}  "
            f"hold={summaries[-1].get('avg_hold_days', 0):5.1f}d  "
            f"peak=${summaries[-1].get('peak_capital', 0):,.0f}"
        )

    out = pd.DataFrame(summaries)

    # Homework metric (precomputed 30d growth field, not Close path).
    full = pd.read_parquet(parquet, engine="pyarrow", columns=["Date", "rsi", "growth_future_30d"])
    full["Date"] = pd.to_datetime(full["Date"])
    hw = full.loc[
        (full["Date"] >= START)
        & (full["Date"] <= END)
        & (full["rsi"] < RSI_THRESHOLD)
        & full["growth_future_30d"].notna()
    ]
    hw_pnl = INVESTMENT * (hw["growth_future_30d"] - 1.0)
    summaries.insert(
        0,
        {
            "variant": "homework_growth_future_30d",
            "n": int(len(hw)),
            "win_rate": float((hw["growth_future_30d"] > 1).mean()),
            "avg_return": float(hw["growth_future_30d"].mean() - 1),
            "median_return": float(hw["growth_future_30d"].median() - 1),
            "avg_hold_days": 30.0,
            "median_hold_days": 30.0,
            "net_income": float(hw_pnl.sum()),
            "net_thousands": float(hw_pnl.sum() / 1000),
            "usd_per_trade": float(hw_pnl.mean()),
            "profit_factor": np.nan,
            "peak_tickets": np.nan,
            "peak_capital": np.nan,
            "exit_rsi_pct": np.nan,
            "exit_stop_pct": np.nan,
            "exit_time_pct": 1.0,
            "exit_eod_pct": 0.0,
        },
    )
    out = pd.DataFrame(summaries)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.summary, index=False)
    print(f"\nWrote {args.summary}")


if __name__ == "__main__":
    main()

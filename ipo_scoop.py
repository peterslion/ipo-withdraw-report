"""Shared IPOScoop recently-filed table loaders and field parsers."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_URL = "https://www.iposcoop.com/ipos-recently-filed"

COMPANY_TYPE_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("Technologies",), "Technologies"),
    (("Acquisition Corp", "Acquisition Corporation", "Corp"), "Acquisition Corp"),
    (("Inc", "Incorporated"), "Inc."),
    (("Group",), "Group"),
    (("Ltd", "Limited"), "Limited"),
    (("Holdings", "Holding"), "Holdings"),
)


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
    for patterns, label in COMPANY_TYPE_RULES:
        if any(pattern in text for pattern in patterns):
            return label
    return "Other"


def load_recently_filed(source: str = SOURCE_URL) -> pd.DataFrame:
    path = Path(source)
    if path.suffix.lower() == ".csv" and path.exists():
        return pd.read_csv(path)
    tables = pd.read_html(source)
    if not tables:
        raise RuntimeError(f"No HTML tables found in {source}")
    return tables[0]


def add_offered_value(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Avg_price"] = out[["Price Low", "Price High"]].map(parse_price).mean(axis=1)
    shares = out["Shares (millions)"].map(to_numeric)
    est_vol = out["Est $ Vol (millions)"].map(to_numeric)
    offered = shares * out["Avg_price"]
    out["Shares_offered_value"] = np.where(offered.notna(), offered, est_vol)
    return out

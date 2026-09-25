# Answers

IPOScoop question series. Later questions land in `questions/` the same way.

## Q1 — Withdrawn IPOs by company type

**Acquisition Corp — $499.985 million**

Filter: `Expected To Trade == Withdrawn`. Classify each company name with the first matching rule (`Technologies` → `Corp` → `Inc` → `Group` → `Ltd`/`Limited` → `Holdings`/`Holding` → Other). Deal value is shares × average of Price Low/High when that product exists; otherwise estimated $ volume.

Live table on 2026-09-25 had 34 withdrawn rows (the original prompt expected 32). File dates before 2026-09-11 still put Acquisition Corp first at the same total.

| Company Type | Sum ($ millions) |
|---|---|
| Acquisition Corp | 499.985 |
| Inc. | 351.000 |
| Holdings | 311.658 |
| Other | 290.445 |
| Limited | 219.250 |
| Technologies | 184.900 |
| Group | 56.575 |

## Q2 — Median Sharpe for 2025 IPOs (first 8 months)

**0.0501** as of 2026-09-11.

Universe: [2025 pricings](https://www.iposcoop.com/2025-pricings/) (231 IPOs). Keep offer date before 2025-09-01 and drop 0% return (146 names on 2026-09-25; the prompt expected 148). yfinance OHLCV for those tickers: **132** with prices (14 delisted/missing; prompt expected ~134).

Formulas (risk-free 5%):

- `growth_252d = Close / Close.shift(252)` (per ticker)
- `volatility = Close.rolling(30).std() * sqrt(252)`
- `Sharpe = (growth_252d - 0.05) / volatility`

On 2026-09-11, **131** names had a 252-day growth observation. Median `growth_252d` (**0.60**) is below the mean (**1.06**): a few huge winners (e.g. MGRT) pull the average up. Mean Sharpe is not usable (`inf` from zero 30-day price vol); the median is. Names such as HCMAU / CEPF show middling 1-year growth but high Sharpe because price vol is tiny — more attractive on a risk-adjusted basis than raw growth leaders like MGRT or BUUU.

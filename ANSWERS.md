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

## Q3 — Fixed-months holding strategy

**1 month, median growth 0.9354** (price after 21 trading days / first close).

From each ticker’s first Yahoo close, `future_growth_m_m = Close.shift(-21*m) / Close`. Inner-join the panel to `min_date` so every name is measured from IPO, not from a later date.

| Month | Median | Mean |
|---|---|---|
| **1** | **0.935** | 95.75 |
| 2 | 0.893 | 67.98 |
| 3 | 0.827 | 51.25 |
| 4 | 0.730 | 22.70 |
| 5 | 0.691 | 54.24 |
| 6 | 0.726 | 64.01 |
| 7 | 0.662 | 59.27 |
| 8 | 0.604 | 21.46 |
| 9 | 0.580 | 20.01 |
| 10 | 0.533 | 11.26 |
| 11 | 0.482 | 8.90 |
| 12 | 0.492 | 5.82 |

The typical 2025 IPO is already below the first close after one month, and the median keeps sliding toward ~0.48–0.49 by 11–12 months. An investor who buys at the first close and holds a *typical* name loses as the horizon lengthens; there is no median edge in “waiting it out.” Means are huge because of bad ticks / outliers (PPCB’s first close is $0.02, then a 12,500× one-month ratio). The median is the right statistic: the average is not a tradeable IPO experience.

## Q4 — RSI oversold ($1000 per signal)

**$65.8 thousand** net income (`net_income / 1000`).

Buy $1,000 whenever `rsi < 30` between 2000-01-01 and 2025-06-01; exit on `growth_future_30d`. Formula: `1000 * (growth_future_30d - 1).sum()`.

| | RSI < 25 | RSI < 30 |
|---|---|---|
| Trades | 1,568 | **5,206** |
| Avg 30-day return | — | **1.26%** |
| Win rate | — | **55.13%** |
| Net income | — | **$65,806** |

Raising the threshold from 25 to 30 more than triples the number of trades. The edge is modest but the win rate is above 50%, so capital grows over the 25-year window.

## Q4b — Same entries, different exits

Same `RSI < 30` entries and $1,000 tickets. Path P&L uses `Close_x` (the homework `growth_future_30d` field is milder and is **not** equal to a 21- or 30-day close ratio, so compare exits only on the Close path).

| Exit | Trades | Win rate | Avg return | Median hold | Net | Peak capital |
|---|---|---|---|---|---|---|
| Homework field (`growth_future_30d`) | 5,206 | 55.1% | 1.26% | 30d | **$65.8k** | — |
| Hold 21 trading days | 5,206 | 59.9% | 4.11% | 21d | $214k | $255k |
| Hold 30 trading days | 5,200 | 60.0% | 5.17% | 30d | $269k | $266k |
| **Exit when RSI ≥ 50** | 5,206 | **75.5%** | **14.9%** | **17d** | **$776k** | $306k |
| Exit when RSI ≥ 40 | 5,206 | 76.6% | 13.7% | 8d | $714k | $288k |
| RSI ≥ 50 or 30d cap | 5,206 | 69.2% | 4.50% | 17d | $234k | $255k |
| RSI ≥ 50 or 60d cap | 5,206 | 71.1% | 6.04% | 17d | $315k | $263k |
| −10% stop or 30d | 5,200 | 53.7% | 3.67% | 30d | $191k | **$111k** |
| RSI ≥ 50 or −10% stop | 5,206 | 69.0% | 13.2% | 13d | $686k | $301k |
| RSI ≥ 50 or −10% or 60d | 5,206 | 64.6% | 4.37% | 13d | $227k | **$90k** |

Letting the bounce finish (exit at RSI 50, no time cap) is the profitability winner: win rate jumps to ~76% and net becomes **$776k**. A −10% stop **cuts peak capital** (to ~$90–111k) but also cuts total profit because it stops out trades that later recover. Capping the RSI-50 exit at 30 days throws away the long winners and lands near the plain time stop.

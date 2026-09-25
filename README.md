# Withdrawn IPOs by Company Type

Pandas analysis of the [IPOScoop recently filed IPO list](https://www.iposcoop.com/ipos-recently-filed). It classifies withdrawn offerings by company-name pattern and reports which class has the largest withdrawn deal value (in $ millions).

## Answer

**Acquisition Corp** had the highest total withdrawn IPO value: **$499.985 million**.

That result uses the live table with `Expected To Trade == Withdrawn` (34 rows on 2026-09-25). Restricting to file dates before 2026-09-11 still leaves Acquisition Corp first at the same total (the later withdrawals are Group / Limited names).

Classification examples from the assignment:

- `EUPEC International Group Ltd.` → **Group** (Group is checked before Ltd)
- `Xinxu Copper Industry Technology Ltd.` → **Limited** (`Technology` is not `Technologies`)
- `Clear Street Group Inc.` → **Inc.** (`Inc` is checked before Group)
- `Coolbit Technologies Ltd.` → **Technologies**

Deal value is `Shares (millions) × average(Price Low, Price High)` when that product is defined; otherwise `Est $ Vol (millions)`.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python analyze_withdrawn_ipos.py
```

Optional snapshot and date cutoff:

```bash
python analyze_withdrawn_ipos.py --snapshot data/recently_filed.csv --before 2026-09-11
```

Requires network access to iposcoop.com unless you pass a saved HTML/CSV-compatible table via `--source`.

# IPOScoop recently filed — question series

Private GitHub repo: [peterslion/ipo-withdraw-report](https://github.com/peterslion/ipo-withdraw-report).

Pandas solutions for IPOScoop [recently filed IPOs](https://www.iposcoop.com/ipos-recently-filed). Question 1 is implemented; later questions from the same list go in `questions/` and are recorded in [ANSWERS.md](ANSWERS.md).

## Q1 answer

**Acquisition Corp** had the highest withdrawn IPO value: **$499.985 million**.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python questions/q01_withdrawn_by_company_type.py
```

Offline snapshot:

```bash
python questions/q01_withdrawn_by_company_type.py \
  --source data/recently_filed.csv \
  --before 2026-09-11
```

Clone from GitHub:

```bash
git clone https://github.com/peterslion/ipo-withdraw-report.git
cd ipo-withdraw-report
```

## Layout

| Path | Role |
|---|---|
| `ipo_scoop.py` | Shared `read_html` loader, price/volume parsers, company-type rules |
| `questions/q01_withdrawn_by_company_type.py` | Withdrawn value by company class |
| `data/recently_filed.csv` | Snapshot of the recently filed table |
| `ANSWERS.md` | Short answers for each question |

## Company type rules (Q1)

First match wins:

1. `Technologies` → Technologies
2. `Acquisition Corp`, `Acquisition Corporation`, or `Corp` → Acquisition Corp
3. `Inc` or `Incorporated` → Inc.
4. `Group` → Group
5. `Ltd` or `Limited` → Limited
6. `Holdings` or `Holding` → Holdings
7. else → Other

`EUPEC International Group Ltd.` is Group, not Limited. `Xinxu Copper Industry Technology Ltd.` is Limited (`Technology` ≠ `Technologies`).

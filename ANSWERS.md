# Answers

Solved from the [IPOScoop recently filed list](https://www.iposcoop.com/ipos-recently-filed). Later questions in this series land in `questions/` the same way.

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

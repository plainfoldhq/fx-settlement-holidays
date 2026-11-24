# FX settlement holidays and spot value dates 2026-2028 (CSV)

Free CSV files with the settlement holidays of six currencies for 2026, 2027 and 2028, and the T+2 spot value date for every weekday trade date of EURUSD, USDJPY, GBPUSD and EURGBP.

| Currency | Calendar |
|---|---|
| USD | Federal Reserve (Fedwire) holidays |
| EUR | TARGET2 / T2 closing days |
| GBP | England and Wales bank holidays (CHAPS, Bacs) |
| JPY | Japan bank holidays (national holidays + December 31 to January 3) |
| AUD | New South Wales bank holidays, Sydney only (2028 only here: see below) |
| NZD | New Zealand holidays incl. Wellington Anniversary (Wellington only; Auckland Anniversary not included) |

## Files

`data/settlement_holidays_2026_2028.csv`: one row per weekday holiday: `date`, `weekday`, `currency`, `calendar`, `holiday` (English name).

`data/fx_spot_dates_2026_2028.csv`: `trade_date` (every weekday), `pair`, `spot_date`, `calendar_days`.

`data/coverage_2026_2028.csv`: which currency-years are included. AUD 2026 and 2027 are not: the two implementations disagree on the Monday after Anzac Day (2026-04-27, 2027-04-26).

```python
import csv
spot = {(r["pair"], r["trade_date"]): r["spot_date"]
        for r in csv.DictReader(open("data/fx_spot_dates_2026_2028.csv"))}
spot[("USDJPY", "2026-12-29")]  # '2027-01-04': Japanese banks close Dec 31 - Jan 3
```

Load straight from GitHub:

```python
import pandas as pd
url = "https://raw.githubusercontent.com/plainfoldhq/fx-settlement-holidays/main/data/settlement_holidays_2026_2028.csv"
pd.read_csv(url).query("currency == 'EUR'")  # TARGET2 closing days
```

## Spot convention

T+2. For pairs with USD, day 1 is the next business day of the non-USD currency (a USD holiday on day 1 does not count) and day 2 the next day that is a business day in both currencies. For crosses (EURGBP), two business days of both currencies, then forward to the first day that is also a USD business day. Some banks apply other rules: confirm with your counterparty.

## How the data is made and checked

- Holidays: generated with the Python [`holidays`](https://github.com/vacanza/holidays) package (MIT) and kept only for currency-years where [QuantLib](https://www.quantlib.org/) (an independent implementation) agrees on every weekday.
- `tests/` recomputes every holiday and every spot date with QuantLib on each push (CI).

## Limits

Future dates follow current rules; central banks and governments can add holidays (for example a state funeral). Not compared with official central-bank or CLS calendars. Not financial advice; not for use as the only source for settlement decisions. Not affiliated with any central bank, payment system or CLS.

## Full pack: 2000-2050, 15 pairs

The paid pack covers 2000-2050 (296 of 306 currency-years), a day-by-day business-day table per currency, spot value dates for all 15 pairs of these currencies, SQLite, JSON, .ics, a tested PostgreSQL loader and a standard-library helper (`spot_date`, `add_business_days`). $19: [buy on Polar](https://buy.polar.sh/polar_cl_9Rkaup8QpzW7cYaFe9nRx0AEiUSxVLMzYyU1K23uuVP) (checkout and tax by Polar, merchant of record). Also in the [All-Access yearly plan](https://buy.polar.sh/polar_cl_xydfuofU72fdp6xSOHFtihAuniUFagYOwR9zf2M03Gl) with every Plainfold data pack.

More calendars: [stock exchange holidays](https://github.com/plainfoldhq/stock-exchange-holidays), [public holidays by country](https://github.com/plainfoldhq/world-public-holidays), [US federal/NYSE/Fed business days](https://github.com/plainfoldhq/us-federal-calendar). Reference pages: [plainfoldhq.github.io](https://plainfoldhq.github.io/).

## License

Data in `data/`: CC0 1.0 (public domain). Tests: MIT. See LICENSE.

Made by Plainfold, an AI-run business. Issues and corrections: open an issue or email plainfoldhq@proton.me.

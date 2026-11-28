# How to calculate the FX spot date (T+2) in Python

The spot value date of an FX trade is usually two business days after the trade date. "Business day" is the catch: it depends on the holidays of both currencies, and for most pairs on the US dollar as well. This guide shows the rule, a worked example where adding two weekdays gives the wrong date, and a cross-check against QuantLib. It uses `fx-spot-dates` (standard library only, version 0.1.1) and QuantLib 1.44 on Python 3.11:

```
pip install fx-spot-dates QuantLib
```

All output below was produced by running the code in this order, in one session.

## The rule in one paragraph

This is the convention the package implements (T+2):

- For a pair with USD (EURUSD, USDJPY, GBPUSD): day 1 is the next business day of the non-USD currency. A USD holiday on day 1 does not count. Day 2 is the next day that is a business day in both currencies.
- For a cross (EURGBP): two business days of both currencies, then forward to the first day that is also a USD business day.

Some banks apply other rules, so confirm with your counterparty.

## Basic calls

```python
import fx_spot_dates as fx

print(fx.spot_date("EURUSD", "2026-03-04"))
print(fx.spot_date("EUR/USD", "2026-12-23"))
print(fx.is_business_day("USD", "2026-07-03"))
print(fx.holidays("EUR", 2026))
```

```
2026-03-06
2026-12-28
True
[(datetime.date(2026, 1, 1), "New Year's Day"), (datetime.date(2026, 4, 3), 'Good Friday'), (datetime.date(2026, 4, 6), 'Easter Monday'), (datetime.date(2026, 5, 1), 'Labour Day'), (datetime.date(2026, 12, 25), 'Christmas Day')]
```

Pairs are six letters, with or without a slash. Dates can be ISO strings or `datetime.date`. The trade date must be a weekday. July 3, 2026 is a business day because the Fed does not close on the Friday before a Saturday holiday. `holidays` returns weekday holidays only.

## Where "add 2 weekdays" goes wrong

```python
from datetime import date, timedelta

def naive_spot(trade, n=2):
    """Add n weekdays and ignore all holidays."""
    d = date.fromisoformat(trade)
    while n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d

for pair, trade in [("EURUSD", "2026-12-23"), ("GBPUSD", "2026-12-23"), ("USDJPY", "2026-12-29")]:
    print(pair, trade, "naive", naive_spot(trade), "spot_date", fx.spot_date(pair, trade))
```

```
EURUSD 2026-12-23 naive 2026-12-25 spot_date 2026-12-28
GBPUSD 2026-12-23 naive 2026-12-25 spot_date 2026-12-29
USDJPY 2026-12-29 naive 2026-12-31 spot_date 2027-01-04
```

All three trade dates are Wednesdays. Why the dates differ:

- EURUSD: day 1 is Dec 24 (TARGET is open). Day 2 cannot be Dec 25 (Christmas, closed for both), so it is Monday Dec 28.
- GBPUSD: Dec 28 is the observed Boxing Day bank holiday in England and Wales, so the spot date is Tuesday Dec 29.
- USDJPY: Japanese banks close Dec 31 to Jan 3. Day 1 is Dec 30 and spot is Monday Jan 4.

## Why both currencies matter, and the USD rule

```python
print(fx.is_business_day("USD", "2026-06-19"), fx.is_business_day("EUR", "2026-06-19"))
print("EURUSD 2026-06-17", naive_spot("2026-06-17"), fx.spot_date("EURUSD", "2026-06-17"))

# USD holiday on day 1 (Thanksgiving): trade Wed 2026-11-25
print(fx.is_business_day("USD", "2026-11-26"), fx.is_business_day("EUR", "2026-11-26"))
print("day 1:", fx.add_business_days(["EUR"], "2026-11-25", 1))
print("spot: ", fx.spot_date("EURUSD", "2026-11-25"))
```

```
False True
EURUSD 2026-06-17 2026-06-19 2026-06-22
False True
day 1: 2026-11-26
spot:  2026-11-27
```

- Juneteenth (Fri 2026-06-19) is a USD holiday but TARGET is open. A EURUSD trade on Jun 17 cannot settle on Jun 19, because day 2 must be open in both currencies. Spot is Monday Jun 22.
- Thanksgiving (Thu 2026-11-26) falls on day 1 of a trade made Nov 25. Day 1 only needs the EUR calendar, so it is Nov 26 even though USD is closed. Day 2 is then Fri Nov 27.

`add_business_days(currencies, date, n)` takes a list of currencies and moves over days that are closed in any of them. This is the building block `spot_date` uses.

## Crosses

```python
print(fx.spot_date("EURGBP", "2026-06-17"), naive_spot("2026-06-17"))
print(fx.spot_date("EURGBP", "2026-06-16"))
```

```
2026-06-22 2026-06-19
2026-06-18
```

EUR and GBP are both open on Jun 19, so two business days after Jun 17 is Jun 19. That day is a USD holiday, so the date moves forward to Jun 22. A trade on Jun 16 gives Jun 18, which is a business day in all three currencies.

## Cross-check with QuantLib

QuantLib is an independent implementation. `JointCalendar` combines two calendars and `advance` moves by business days. This function applies the same convention:

```python
import QuantLib as ql

cal = {"USD": ql.UnitedStates(ql.UnitedStates.FederalReserve), "EUR": ql.TARGET(),
       "GBP": ql.UnitedKingdom(ql.UnitedKingdom.Settlement), "JPY": ql.Japan()}

def ql_spot(pair, trade):
    a, b = pair[:3], pair[3:]
    t = ql.Date(trade.day, trade.month, trade.year)
    if "USD" in (a, b):
        other = cal[b if a == "USD" else a]
        day1 = other.advance(t, 1, ql.Days)
        joint = ql.JointCalendar(cal[a], cal[b])
        d = joint.advance(day1, 1, ql.Days)
    else:
        joint = ql.JointCalendar(cal[a], cal[b])
        d = joint.advance(t, 2, ql.Days)
        d = ql.JointCalendar(joint, cal["USD"]).adjust(d, ql.Following)
    return date(d.year(), d.month(), d.dayOfMonth())

print(ql_spot("EURUSD", date(2026, 12, 23)), ql_spot("USDJPY", date(2026, 12, 29)),
      ql_spot("EURUSD", date(2026, 6, 17)), ql_spot("EURGBP", date(2026, 6, 17)))
```

```
2026-12-28 2027-01-04 2026-06-22 2026-06-22
```

These match the dates above. To compare every weekday trade date from 2026 to 2028 for five pairs:

```python
bad = total = skipped = 0
d = date(2026, 1, 1)
while d.year <= 2028:
    if d.weekday() < 5:
        for pair in ("EURUSD", "GBPUSD", "USDJPY", "EURGBP", "EURJPY"):
            try:
                ours = fx.spot_date(pair, d)
            except fx.NotCovered:
                skipped += 1  # spot date falls in 2029
                continue
            total += 1
            if ours != ql_spot(pair, d):
                bad += 1
                print("DIFF", pair, d, ours, ql_spot(pair, d))
    d += timedelta(days=1)
print(total, "compared,", bad, "differences,", skipped, "skipped (2029)")
```

```
3900 compared, 0 differences, 10 skipped (2029)
```

The two agree on all 3,900 comparisons. Note that this check uses the same convention on both sides, so it tests the holiday calendars and the date arithmetic, not whether your counterparty uses this convention.

## Limits

- Covered: USD, EUR, GBP, JPY and NZD for 2026-2028, and AUD for 2028 only (AUD 2026 and 2027 are left out because the two data sources disagree on the Monday after Anzac Day). Outside that range the package raises `NotCovered` and never guesses.
- Pairs with currencies outside USD, EUR, GBP, JPY, AUD and NZD are not available, so there is no T+1 handling (for example USD/CAD).
- A trade near the end of 2028 can have a spot date in 2029, which also raises `NotCovered`.

```python
for args in [("EURUSD", "2025-12-30"), ("EURUSD", "2028-12-29"), ("EURUSD", "2026-12-26")]:
    try:
        print(fx.spot_date(*args))
    except Exception as e:
        print(type(e).__name__, "-", e)
try:
    fx.spot_date("AUDUSD", "2026-06-17")
except fx.NotCovered as e:
    print("NotCovered -", e)
print(fx.spot_date("AUDUSD", "2028-06-14"))
```

```
NotCovered - EUR 2025 is not covered (bundled: 2026-2028; AUD 2028 only)
NotCovered - EUR 2029 is not covered (bundled: 2026-2028; AUD 2028 only)
ValueError - trade date 2026-12-26 is a weekend
NotCovered - AUD 2026 is not covered (bundled: 2026-2028; AUD 2028 only)
2028-06-16
```

Future dates follow current rules. Governments can add holidays. The data is not compared with official central-bank or CLS calendars.

## Full pack: 2000-2050, 15 pairs

The [currency settlement holidays + FX spot dates pack](https://buy.polar.sh/polar_cl_9Rkaup8QpzW7cYaFe9nRx0AEiUSxVLMzYyU1K23uuVP?utm_source=github&utm_medium=readme&utm_campaign=Q&utm_content=fx-settlement-holidays) ($19, one-time; Polar is the merchant of record and handles sales tax) covers 2000-2050 (296 of 306 currency-years) with:

- a day-by-day business-day table per currency
- spot value dates for all 15 pairs of these six currencies
- SQLite, JSON, .ics and a tested PostgreSQL loader
- a standard-library helper (`spot_date`, `add_business_days`)

It is also in the [All-Access yearly plan](https://buy.polar.sh/polar_cl_xydfuofU72fdp6xSOHFtihAuniUFagYOwR9zf2M03Gl?utm_source=github&utm_medium=readme&utm_campaign=ALLACCESS&utm_content=fx-settlement-holidays) with every Plainfold data pack. Details: [README](../README.md#full-pack-2000-2050-15-pairs).

---

Made by Plainfold. Written with AI assistance. Not financial advice; confirm settlement dates with your counterparty or CLS.

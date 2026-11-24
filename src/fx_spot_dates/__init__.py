"""FX settlement business days and T+2 spot value dates for USD, EUR, GBP, JPY, AUD, NZD (2026-2028).

    >>> import fx_spot_dates as fx
    >>> fx.spot_date("USDJPY", "2026-12-29")
    datetime.date(2027, 1, 4)
    >>> fx.is_business_day("EUR", "2026-12-24")      # TARGET2 is open on Christmas Eve
    True

Calendars: USD Federal Reserve (Fedwire), EUR TARGET2, GBP England and Wales bank holidays, JPY Japan bank
holidays, AUD New South Wales bank holidays (2028 only), NZD New Zealand incl. Wellington Anniversary.
Dates come from the Python `holidays` package and were kept only where QuantLib agrees on every weekday.
Outside the covered currency-years every function raises NotCovered (it never guesses).

Spot convention (T+2): for pairs with USD, day 1 is the next business day of the non-USD currency and day 2 the
next day that is a business day in both; for crosses, two business days of both currencies, then forward to
the first day that is also a USD business day. Some banks use other rules: confirm with your counterparty.
Not financial advice. Full 2000-2050 data and 15-pair tables: https://github.com/plainfoldhq/fx-settlement-holidays
"""
import csv
import os
from datetime import date, timedelta

__version__ = "0.1.1"
__all__ = ["CURRENCIES", "NotCovered", "is_business_day", "add_business_days", "spot_date", "holidays"]

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CURRENCIES = ("USD", "EUR", "GBP", "JPY", "AUD", "NZD")


class NotCovered(ValueError):
    """The currency-year is not in the bundled data."""


def _load():
    covered, closed = set(), {}
    with open(os.path.join(_DATA, "coverage_2026_2028.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["status"] == "covered":
                covered.add((r["currency"], int(r["year"])))
    with open(os.path.join(_DATA, "settlement_holidays_2026_2028.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            closed[(r["currency"], date.fromisoformat(r["date"]))] = r["holiday"]
    return covered, closed


_COVERED, _CLOSED = _load()


def _d(x):
    return x if isinstance(x, date) else date.fromisoformat(str(x))


def is_business_day(currency, d):
    """True if `d` is a settlement business day for `currency`."""
    c, d = currency.upper(), _d(d)
    if c not in CURRENCIES:
        raise KeyError(f"unknown currency {currency}; available: {', '.join(CURRENCIES)}")
    if (c, d.year) not in _COVERED:
        raise NotCovered(f"{c} {d.year} is not covered (bundled: 2026-2028; AUD 2028 only)")
    return d.weekday() < 5 and (c, d) not in _CLOSED


def holidays(currency, year):
    """[(date, name)] weekday settlement holidays of `currency` in `year`."""
    c = currency.upper()
    is_business_day(c, date(year, 1, 1))  # raises for unknown/uncovered
    return sorted((d, n) for (cc, d), n in _CLOSED.items() if cc == c and d.year == year)


def _joint(ccys, d):
    return all([is_business_day(c, d) for c in ccys])


def add_business_days(currencies, d, n):
    """n >= 0 days that are business days in every currency of `currencies` (n = 0: d or the next such day)."""
    if isinstance(currencies, str):
        currencies = [currencies]
    d = _d(d)
    if n < 0:
        raise ValueError("n must be >= 0")
    if n == 0:
        while not _joint(currencies, d):
            d += timedelta(days=1)
        return d
    for _ in range(n):
        d += timedelta(days=1)
        while not _joint(currencies, d):
            d += timedelta(days=1)
    return d


def spot_date(pair, trade_date):
    """T+2 spot value date for a 6-letter pair such as 'EURUSD' and a weekday trade date."""
    pair = pair.upper().replace("/", "")
    a, b = pair[:3], pair[3:]
    t = _d(trade_date)
    if len(pair) != 6 or a == b:
        raise ValueError(f"not a currency pair: {pair}")
    if t.weekday() >= 5:
        raise ValueError(f"trade date {t} is a weekend")
    if "USD" in (a, b):
        other = b if a == "USD" else a
        return add_business_days([a, b], add_business_days([other], t, 1), 1)
    return add_business_days([a, b, "USD"], add_business_days([a, b], t, 2), 0)


def cli(argv=None):
    import sys
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: fx-spot-dates EURUSD 2026-12-24   |   fx-spot-dates USD 2026-07-03")
        return 2
    try:
        if len(argv[0].replace("/", "")) == 6:
            print(spot_date(argv[0], argv[1]))
        else:
            print("business day" if is_business_day(argv[0], argv[1]) else "holiday/weekend")
    except (NotCovered, KeyError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0

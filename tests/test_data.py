"""Check the CSVs against QuantLib, an implementation independent of the `holidays` package they come from.

    pip install QuantLib
    python -m unittest discover -s tests -v
"""
import csv
import os
import unittest
from datetime import date, timedelta

import QuantLib as ql

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
QL = {"USD": ql.UnitedStates(ql.UnitedStates.FederalReserve), "EUR": ql.TARGET(),
      "GBP": ql.UnitedKingdom(ql.UnitedKingdom.Settlement), "JPY": ql.Japan(),
      "AUD": ql.Australia(ql.Australia.Settlement), "NZD": ql.NewZealand()}


def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def qd(d):
    return ql.Date(d.day, d.month, d.year)


class Data(unittest.TestCase):
    def test_holidays_match_quantlib(self):
        covered = {(r["currency"], int(r["year"])) for r in rows("coverage_2026_2028.csv") if r["status"] == "covered"}
        got = {(r["currency"], r["date"]) for r in rows("settlement_holidays_2026_2028.csv")}
        for c, y in covered:
            d = date(y, 1, 1)
            while d.year == y:
                if d.weekday() < 5:
                    self.assertEqual((c, d.isoformat()) in got, QL[c].isHoliday(qd(d)), (c, d))
                d += timedelta(days=1)
        self.assertTrue(all((c, int(d[:4])) in covered for c, d in got))

    def test_spot_dates(self):
        one = ql.Period(1, ql.Days)
        for r in rows("fx_spot_dates_2026_2028.csv"):
            a, b = r["pair"][:3], r["pair"][3:]
            t = qd(date.fromisoformat(r["trade_date"]))
            j = ql.JointCalendar(QL[a], QL[b], ql.JoinHolidays)
            if "USD" in (a, b):
                s = j.advance(QL[b if a == "USD" else a].advance(t, one), one)
            else:
                s = ql.JointCalendar(j, QL["USD"], ql.JoinHolidays).adjust(j.advance(t, ql.Period(2, ql.Days)), ql.Following)
            self.assertEqual(date(s.year(), s.month(), s.dayOfMonth()).isoformat(), r["spot_date"], r)


if __name__ == "__main__":
    unittest.main()

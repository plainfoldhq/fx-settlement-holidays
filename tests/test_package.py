"""The package (src/fx_spot_dates) against the CSVs in data/. Standard library only.

    PYTHONPATH=src python -m unittest discover -s tests -v
"""
import csv
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import fx_spot_dates as fx  # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


class Package(unittest.TestCase):
    def test_spot_table(self):
        with open(os.path.join(DATA, "fx_spot_dates_2026_2028.csv"), newline="") as f:
            for r in csv.DictReader(f):
                self.assertEqual(fx.spot_date(r["pair"], r["trade_date"]).isoformat(), r["spot_date"], r)

    def test_examples(self):
        self.assertEqual(fx.spot_date("USDJPY", "2026-12-29"), date(2027, 1, 4))
        self.assertEqual(fx.spot_date("eur/usd", "2026-12-24"), date(2026, 12, 29))
        self.assertTrue(fx.is_business_day("USD", "2026-07-03"))
        self.assertIn((date(2026, 12, 28), "Boxing Day (observed)"), fx.holidays("GBP", 2026))

    def test_errors(self):
        with self.assertRaises(fx.NotCovered):
            fx.is_business_day("AUD", "2026-03-02")
        with self.assertRaises(fx.NotCovered):
            fx.spot_date("EURUSD", "2030-01-02")
        with self.assertRaises(ValueError):
            fx.spot_date("EURUSD", "2026-12-26")
        with self.assertRaises(KeyError):
            fx.is_business_day("CAD", "2026-03-02")
        self.assertEqual(fx.cli(["EURUSD", "2026-12-26"]), 1)


if __name__ == "__main__":
    unittest.main()

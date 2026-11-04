import unittest

from backtest_v7 import BAR_MS, aggregate_completed_klines, simulate
from backtest_horizons_v7 import HORIZON_MINUTES


class UtcTimeframeAggregationTests(unittest.TestCase):
    def make_bars(self, count, start=0):
        ts = [start + i * BAR_MS for i in range(count)]
        opens = [100.0 + i for i in range(count)]
        highs = [value + 2 for value in opens]
        lows = [value - 1 for value in opens]
        closes = [value + 1 for value in opens]
        volumes = [10.0] * count
        return ts, opens, highs, lows, closes, volumes

    def test_four_hour_bars_align_to_utc_and_aggregate_ohlcv(self):
        data = self.make_bars(48 + 12)
        rows = aggregate_completed_klines(*data, 59, 240)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 0)
        self.assertEqual(rows[0][1], 100.0)
        self.assertEqual(rows[0][2], 149.0)
        self.assertEqual(rows[0][3], 99.0)
        self.assertEqual(rows[0][4], 148.0)
        self.assertEqual(rows[0][7], 480.0)

    def test_incomplete_utc_bucket_is_not_returned(self):
        data = self.make_bars(47)
        rows = aggregate_completed_klines(*data, 46, 240)
        self.assertEqual(rows, [])

    def test_missing_five_minute_bar_invalidates_bucket(self):
        data = list(self.make_bars(48))
        for values in data:
            del values[12]
        rows = aggregate_completed_klines(*data, 46, 240)
        self.assertEqual(rows, [])


    def test_primary_backtest_timeout_matches_each_opportunity_profile(self):
        expected = {"SCALP": 12, "INTRADAY": 288, "SWING": 2016}
        for kind, bars in expected.items():
            with self.subTest(kind=kind):
                horizon = HORIZON_MINUTES[kind] // 5
                self.assertEqual(horizon, bars)
                prices = [100.0] * bars
                outcome, observed, exit_price = simulate(
                    prices, prices, prices, prices, 0, 50.0, 50.0, horizon
                )
                self.assertEqual(outcome, "TIMEOUT")
                self.assertEqual(observed, bars)
                self.assertEqual(exit_price, 100.0)

    def test_daily_candle_requires_all_288_five_minute_bars(self):
        data = self.make_bars(288 + 1)
        rows = aggregate_completed_klines(*data, 287, 1440)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 0)


if __name__ == "__main__":
    unittest.main()

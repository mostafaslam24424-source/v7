import unittest
from trade_profile_v7 import classify_opportunity


def candles(closes):
    # Binance kline shape; final row is treated as the still-forming candle.
    return [[0, 0, 0, 0, str(close)] for close in closes]


class OpportunityClassificationTests(unittest.TestCase):
    def test_swing_requires_completed_4h_and_daily_confirmation(self):
        candidate = {"5m": 0.2, "15m": 0.8, "1h": 2.0,
                     "acceleration": 1.1, "volume_15m": 2.0,
                     "trend_continuity": 5}
        result = classify_opportunity(
            candidate,
            candles([100, 101, 102, 104, 105, 80]),
            candles([100, 101, 102, 103, 104, 80]),
        )
        self.assertEqual(result["type"], "SWING")

    def test_scalp_classification(self):
        candidate = {"5m": 1.3, "15m": 1.8, "1h": 2.2,
                     "acceleration": 2.1, "volume_15m": 4.0,
                     "trend_continuity": 2}
        self.assertEqual(classify_opportunity(candidate)["type"], "SCALP")

    def test_missing_higher_timeframe_never_guesses_swing(self):
        candidate = {"5m": 0.1, "15m": 1.4, "1h": 2.0,
                     "acceleration": 1.0, "volume_15m": 2.0,
                     "trend_continuity": 4}
        self.assertEqual(classify_opportunity(candidate)["type"], "INTRADAY")

    def test_forming_candle_is_excluded(self):
        candidate = {"5m": 0.1, "15m": 0.8, "1h": 2.0,
                     "acceleration": 1.1, "volume_15m": 2.0,
                     "trend_continuity": 5}
        # Positive completed 4h candles but sharply negative daily closes: not Swing.
        result = classify_opportunity(
            candidate,
            candles([100, 101, 102, 104, 105, 80]),
            candles([110, 109, 108, 107, 106, 150]),
        )
        self.assertNotEqual(result["type"], "SWING")


if __name__ == "__main__":
    unittest.main()

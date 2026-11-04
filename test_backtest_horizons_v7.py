import unittest

from backtest_horizons_v7 import evaluate_signal, summarize_by_profile


class HorizonBacktestTests(unittest.TestCase):
    def setUp(self):
        self.targets = {1: 101.0, 2: 102.0, 3: 103.0}

    def test_target_touch_times_are_recorded(self):
        candles = [
            {"high": 101.2, "low": 100.2, "close": 101.0},
            {"high": 102.2, "low": 101.1, "close": 102.0},
            {"high": 103.2, "low": 101.5, "close": 103.0},
        ]
        r = evaluate_signal(candles, 100, 1, self.targets, "SCALP")
        self.assertEqual([r[f"tp{i}_hit_min"] for i in (1, 2, 3)], [5, 10, 15])
        self.assertEqual(r["status"], "TIMEOUT")

    def test_same_candle_stop_and_target_is_stop_conservatively(self):
        candles = [{"high": 104, "low": 98, "close": 102}]
        r = evaluate_signal(candles, 100, 1, self.targets, "INTRADAY")
        self.assertEqual(r["status"], "SL")
        self.assertIsNone(r["tp1_hit_min"])

    def test_targets_hit_before_later_stop_are_preserved(self):
        candles = [
            {"high": 101.5, "low": 100.2, "close": 101},
            {"high": 102.5, "low": 100.5, "close": 102},
            {"high": 102.6, "low": 98, "close": 99},
        ]
        r = evaluate_signal(candles, 100, 1, self.targets, "SCALP")
        self.assertEqual(r["tp1_hit_min"], 5)
        self.assertEqual(r["tp2_hit_min"], 10)
        self.assertEqual(r["status"], "SL")
        self.assertEqual(r["tp3_status"], "SL_BEFORE_TARGET")

    def test_horizon_and_data_gap(self):
        self.assertEqual(evaluate_signal([], 100, 1, self.targets, "SWING")["status"], "DATA_GAP")
        r = evaluate_signal([{"high": 100.5, "low": 100.1, "close": 100.2}],
                            100, 1, self.targets, "SCALP")
        self.assertEqual(r["horizon_minutes"], 60)
        self.assertEqual(r["status"], "DATA_GAP")

    def test_summary_keeps_data_gaps_visible(self):
        rows = [
            {"opportunity_type": "SCALP", "tp1_hit_min": 5, "tp2_hit_min": None,
             "tp3_hit_min": None, "status": "SL"},
            {"opportunity_type": "SCALP", "tp1_hit_min": None, "tp2_hit_min": None,
             "tp3_hit_min": None, "status": "DATA_GAP"},
        ]
        s = summarize_by_profile(rows)["SCALP"]
        self.assertEqual(s["signals"], 2)
        self.assertEqual(s["tp1_hit_pct"], 50.0)
        self.assertEqual(s["data_gap_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()

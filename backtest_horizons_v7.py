"""Multi-target, horizon-aware OHLC evaluator for offline paper backtests.

Input candles must be chronological and strictly AFTER the signal candle.
No order placement, live trading, or prediction is performed here.
"""
from __future__ import annotations

from collections import defaultdict

HORIZON_MINUTES = {"SCALP": 60, "INTRADAY": 1440, "SWING": 10080}


def evaluate_signal(candles, entry, sl_pct, tp_prices, opportunity_type):
    """Evaluate TP1/2/3 touches until stop or the profile horizon.

    candles: chronological mappings with high, low, close; each represents
    one completed 5-minute candle after entry. Entry is supplied separately.
    When SL and one or more targets occur in the same OHLC candle, SL wins
    conservatively because intrabar ordering cannot be inferred.
    """
    kind = str(opportunity_type or "INTRADAY").upper()
    if kind not in HORIZON_MINUTES:
        kind = "INTRADAY"
    if entry <= 0 or sl_pct <= 0:
        raise ValueError("entry and sl_pct must be positive")
    targets = {int(k): float(v) for k, v in tp_prices.items() if int(k) in (1, 2, 3)}
    stop = entry * (1.0 - sl_pct / 100.0)
    horizon_bars = HORIZON_MINUTES[kind] // 5
    result = {
        "opportunity_type": kind,
        "horizon_minutes": HORIZON_MINUTES[kind],
        "stop_price": stop,
        "status": "TIMEOUT",
        "stop_hit_min": None,
        "bars_observed": 0,
    }
    for level in (1, 2, 3):
        result[f"tp{level}_hit_min"] = None
        result[f"tp{level}_status"] = "NOT_REACHED"
    usable = list(candles[:horizon_bars])
    if not usable:
        result["status"] = "DATA_GAP"
        return result
    for i, candle in enumerate(usable, start=1):
        hi, lo = float(candle["high"]), float(candle["low"])
        result["bars_observed"] = i
        if lo <= stop:
            result["status"] = "SL"
            result["stop_hit_min"] = i * 5
            for level in (1, 2, 3):
                if result[f"tp{level}_hit_min"] is None:
                    result[f"tp{level}_status"] = "SL_BEFORE_TARGET"
            break
        for level, price in targets.items():
            key = f"tp{level}_hit_min"
            if result[key] is None and hi >= price:
                result[key] = i * 5
                result[f"tp{level}_status"] = "HIT"
    else:
        if len(usable) < horizon_bars:
            result["status"] = "DATA_GAP"
        else:
            result["status"] = "TIMEOUT"
    return result


def summarize_by_profile(rows):
    """Return counts and target-touch rates; DATA_GAP is kept visible."""
    groups = defaultdict(list)
    for row in rows:
        groups[str(row.get("opportunity_type", "UNKNOWN")).upper()].append(row)
    summary = {}
    for kind, group in sorted(groups.items()):
        n = len(group)
        item = {"signals": n}
        for level in (1, 2, 3):
            hits = sum(r.get(f"tp{level}_hit_min") is not None for r in group)
            item[f"tp{level}_hit_pct"] = round(100.0 * hits / n, 2) if n else 0.0
            times = [r[f"tp{level}_hit_min"] for r in group
                     if r.get(f"tp{level}_hit_min") is not None]
            item[f"tp{level}_avg_minutes_when_hit"] = (
                round(sum(times) / len(times), 1) if times else None
            )
        for status in ("SL", "TIMEOUT", "DATA_GAP"):
            item[f"{status.lower()}_pct"] = round(
                100.0 * sum(r.get("status") == status for r in group) / n, 2
            ) if n else 0.0
        summary[kind] = item
    return summary

"""Paper-trading metadata for Binance Early-Pump Scanner V7.

This module classifies a detected long-only momentum candidate by an estimated
holding horizon. It does not predict returns or guarantee an outcome.
"""
from __future__ import annotations


def _number(data: dict, key: str, default: float = 0.0) -> float:
    try:
        value = float(data.get(key, default))
        return value if value == value and abs(value) != float("inf") else default
    except (TypeError, ValueError):
        return default


def _completed_closes(rows):
    """Return closes of completed Binance candles (exclude the last, forming bar)."""
    if not isinstance(rows, list) or len(rows) < 5:
        return []
    closes = []
    for row in rows[:-1]:
        try:
            close = float(row[4])
            if close > 0:
                closes.append(close)
        except (TypeError, ValueError, IndexError):
            continue
    return closes


def _trend_pct(closes, lookback: int = 3):
    if len(closes) < lookback + 1 or closes[-lookback - 1] <= 0:
        return None
    return (closes[-1] / closes[-lookback - 1] - 1.0) * 100.0


def classify_opportunity(candidate: dict, klines_4h=None, klines_1d=None) -> dict:
    """Classify a pump candidate as scalp, intraday, or swing when HTF agrees.

    Swing is only assigned when completed 4h and daily candles both confirm.
    If higher-timeframe data is missing, the function deliberately falls back
    to a shorter horizon instead of guessing a multi-day hold.
    """
    g5 = _number(candidate, "5m")
    g15 = _number(candidate, "15m")
    g1h = _number(candidate, "1h")
    accel = _number(candidate, "acceleration")
    vol15 = _number(candidate, "volume_15m")
    continuity = _number(candidate, "trend_continuity")

    closes_4h = _completed_closes(klines_4h)
    closes_1d = _completed_closes(klines_1d)
    trend_4h = _trend_pct(closes_4h, 3)
    trend_1d = _trend_pct(closes_1d, 3)

    if (trend_4h is not None and trend_1d is not None
            and trend_4h > 0.5 and trend_1d > 0.0
            and g1h > 0 and continuity >= 3):
        return {
            "type": "SWING",
            "label": "صفقة قد تستمر أيامًا (Swing)",
            "holding_window": "عدة أيام — تقدير مبدئي",
            "basis": f"اتجاه 4h={trend_4h:+.2f}% و1d={trend_1d:+.2f}% على شموع مكتملة",
        }

    if g5 >= 1.0 and accel >= 1.8 and vol15 >= 3.0:
        return {
            "type": "SCALP",
            "label": "صفقة قصيرة (Scalping)",
            "holding_window": "دقائق إلى أقل من ساعة — تقدير مبدئي",
            "basis": "زخم 5m وتسارع حجم تداول مرتفعان",
        }

    if g15 > 0 and g1h > 0 and continuity >= 3:
        return {
            "type": "INTRADAY",
            "label": "صفقة خلال اليوم (Intraday)",
            "holding_window": "عدة ساعات وحتى نهاية اليوم — تقدير مبدئي",
            "basis": "استمرار إيجابي على 15m و1h",
        }

    return {
        "type": "INTRADAY",
        "label": "فرصة قصيرة/خلال اليوم (Intraday)",
        "holding_window": "تُراجع خلال اليوم — تقدير مبدئي",
        "basis": "لا توجد بيانات إطار أعلى كافية لتصنيفها كفرصة متعددة الأيام",
    }


def holding_timeout_minutes(opportunity_type: str) -> int:
    """Maximum paper-observation window for each displayed opportunity horizon."""
    kind = str(opportunity_type or "INTRADAY").upper()
    if kind == "SCALP":
        return 60
    if kind == "SWING":
        return 7 * 24 * 60
    return 24 * 60

 
def record_target_touches(track: dict, high: float, elapsed_min: float,
                          stop_touched: bool = False) -> None:
    """Record first observed TP touches for paper analysis only.

    If a candle also touches the stop, its intrabar order is unknowable from OHLC
    data, so target touches from that same candle are conservatively not counted.
    """
    if stop_touched:
        return
    for level in (1, 2, 3):
        price = _number(track, f"tp{level}")
        key = f"tp{level}_hit_min"
        if price > 0 and track.get(key) is None and high >= price:
            track[key] = round(float(elapsed_min), 1)

"""
Mock stock service — generates deterministic fake prices/history so the
Investments page works with no network calls and no API keys. Swap for a
real yfinance-backed version later if needed.
"""
import hashlib
from datetime import date, timedelta

import pandas as pd

_KNOWN = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.", "TSLA": "Tesla Inc.", "INFY.NS": "Infosys Ltd.",
    "TCS.NS": "Tata Consultancy Services", "RELIANCE.NS": "Reliance Industries",
}


def _base_price(symbol: str) -> float:
    # Deterministic pseudo-price derived from the symbol so it's stable across reruns.
    h = int(hashlib.md5(symbol.upper().encode()).hexdigest(), 16)
    return 50 + (h % 4500) / 10  # roughly 50 - 500


def search_symbol(query: str):
    q = query.strip().upper()
    if not q:
        return []
    matches = [{"symbol": s, "name": n} for s, n in _KNOWN.items() if q in s or q in n.upper()]
    if not matches:
        matches = [{"symbol": q, "name": f"{q} (mock result)"}]
    return matches[:5]


def get_current_price(symbol: str) -> float:
    if not symbol or not symbol.strip():
        raise RuntimeError("Symbol cannot be empty.")
    return round(_base_price(symbol), 2)


def get_prices_bulk(symbols) -> dict:
    out = {}
    for s in symbols:
        base = _base_price(s)
        # Small deterministic "daily change" so the UI has something to show.
        change_pct = ((int(hashlib.md5((s + "chg").encode()).hexdigest(), 16) % 800) - 400) / 100
        out[s] = {"price": round(base, 2), "changePercent": round(change_pct, 2)}
    return out


def get_historical_data(symbol: str, period: str = "6mo") -> pd.DataFrame:
    days_map = {"1mo": 30, "3mo": 90, "6mo": 182, "1y": 365, "2y": 730, "5y": 1825}
    days = days_map.get(period, 182)
    base = _base_price(symbol)
    rows = []
    price = base * 0.85
    for i in range(days, -1, -1):
        d = date.today() - timedelta(days=i)
        # Deterministic gentle drift so the chart looks like a real price line.
        seed = int(hashlib.md5(f"{symbol}{d.isoformat()}".encode()).hexdigest(), 16)
        drift = ((seed % 200) - 100) / 1000  # +/- 10%
        price = max(price * (1 + drift * 0.05) + (base - price) * 0.01, 0.5)
        rows.append({"date": d, "close": round(price, 2)})
    return pd.DataFrame(rows)

"""
Fetch OHLC candlestick data for a symbol.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

symbol = "BTC-USDT"
result = snx.get_candles(symbol, "1h", limit=5)
candles = result.get("candles", [])
print(f"Last {len(candles)} hourly candles for {symbol}\n")

for c in candles:
    print(
        f"  {c['openTime']}"
        f"  O={c['openPrice']:>12s}"
        f"  H={c['highPrice']:>12s}"
        f"  L={c['lowPrice']:>12s}"
        f"  C={c['closePrice']:>12s}"
        f"  V={c['volume']:>12s}"
    )

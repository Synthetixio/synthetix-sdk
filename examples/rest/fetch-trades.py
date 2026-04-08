"""
Fetch recent public trades for a symbol.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

symbol = "BTC-USDT"
trades = snx.get_last_trades(symbol, limit=10)
print(f"Last {len(trades)} trades for {symbol}\n")

for t in trades:
    print(f"  {t['timestamp']}  {t['side']:4s}  price={t['price']:>12s}  qty={t['quantity']:>12s}")

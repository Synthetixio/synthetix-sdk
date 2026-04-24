"""
Fetch funding rate history for a symbol over the last 24 hours.
"""

import os
import time

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

symbol = "ETH-USDT"
now_ms = int(time.time() * 1000)
one_day_ms = 24 * 60 * 60 * 1000

history = snx.get_funding_rate_history(symbol, now_ms - one_day_ms, now_ms)

rates = history.get("fundingRates", [])
print(f"Funding rate history for {symbol}: {len(rates)} entries\n")

for r in rates[:10]:
    print(f"  {r['fundingTime']}  rate={r['fundingRate']}")

if len(rates) > 10:
    print(f"  ... and {len(rates) - 10} more")

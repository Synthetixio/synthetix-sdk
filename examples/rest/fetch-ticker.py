"""
Fetch current prices for all markets.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

prices = snx.get_market_prices()
print(f"Prices for {len(prices)} markets\n")

for symbol, data in prices.items():
    print(
        f"  {symbol:20s}"
        f"  bid={data['bestBid']:>12s}"
        f"  ask={data['bestAsk']:>12s}"
        f"  mark={data['markPrice']:>12s}"
        f"  24h_vol={data['volume24h']:>12s}"
    )

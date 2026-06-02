"""
Fetch mid prices for all markets using best bid/ask from getMarketPrices.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

prices = snx.get_market_prices()
print(f"Mid prices for {len(prices)} markets\n")

for symbol, data in sorted(prices.items()):
    bid = float(data["bestBid"])
    ask = float(data["bestAsk"])
    mid = (bid + ask) / 2
    print(f"  {symbol:20s}  {mid}")

"""
Fetch orderbook snapshot for a symbol.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

symbol = "ETH-USDT"
ob = snx.get_orderbook(symbol)

bids = ob.get("bids", [])
asks = ob.get("asks", [])

print(f"Orderbook for {symbol}: {len(bids)} bids, {len(asks)} asks\n")

print("  --- Top 5 Asks ---")
for price, size in reversed(asks[:5]):
    print(f"  {price:>14s}  {size:>14s}")

print("  --- Top 5 Bids ---")
for price, size in bids[:5]:
    print(f"  {price:>14s}  {size:>14s}")

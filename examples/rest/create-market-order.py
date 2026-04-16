"""
Place a market order.

Fills at the best available price immediately.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Market buy
result = snx.market_order("ETH-USDT", "buy", "0.01")
print(f"Market order result: {result}")

# Check resulting position
positions = snx.get_positions()
print("\nPositions after market order:")
for p in positions:
    print(f"  {p['symbol']}  {p['side']}  qty={p['quantity']}  entry={p['entryPrice']}")

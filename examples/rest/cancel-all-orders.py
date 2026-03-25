"""
Cancel all open orders for a symbol.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Place a few orders first
for price in ["10000", "10500", "11000"]:
    snx.place_order(
        symbol="BTC-USDT",
        side="buy",
        quantity="0.001",
        price=price,
        order_type="limitGtc",
    )

orders = snx.get_open_orders()
print(f"Open orders before cancel: {len(orders)}")

# Cancel all BTC-USDT orders at once
result = snx.cancel_all_orders("BTC-USDT")
print(f"\nCancel all result: {result}")

remaining = snx.get_open_orders()
print(f"Open orders after cancel: {len(remaining)}")

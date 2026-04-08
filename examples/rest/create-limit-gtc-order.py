"""
Place a limit Good-Til-Cancel (GTC) order.

The order stays on the book until filled or canceled.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Place a limit buy far below market so it rests on the book
result = snx.place_order(
    symbol="BTC-USDT",
    side="buy",
    quantity="0.001",
    price="10000",  # far below market
    order_type="limitGtc",  # good-til-cancel
)
print(f"Limit GTC order result: {result}")

# Verify it's resting
orders = snx.get_open_orders()
print(f"\nOpen orders: {len(orders)}")
for o in orders:
    print(f"  id={o['orderId']}  {o['symbol']}  {o['side']}  price={o['price']}  qty={o['quantity']}")

# Clean up
cancel = snx.cancel_all_orders("BTC-USDT")
print(f"\nCanceled: {cancel}")

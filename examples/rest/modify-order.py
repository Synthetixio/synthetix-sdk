"""
Modify an existing resting order (change price or quantity).

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# First, place an order to modify
snx.place_order(
    symbol="BTC-USDT",
    side="buy",
    quantity="0.001",
    price="10000",
    order_type="limitGtc",
)

orders = snx.get_open_orders()
if not orders:
    print("No open orders to modify")
    exit()

order = orders[0]
print(f"Before: id={order['orderId']}  price={order['price']}  qty={order['quantity']}")

# Modify the price
result = snx.modify_order(
    order_id=int(order["orderId"]),
    price="11000",
    quantity="0.002",
)
print(f"\nModify result: {result}")

# Verify
orders = snx.get_open_orders()
if orders:
    o = orders[0]
    print(f"After:  id={o['orderId']}  price={o['price']}  qty={o['quantity']}")

# Clean up
snx.cancel_all_orders("BTC-USDT")
print("\nCanceled all orders.")

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

# Get current mark price and place 5% below so it rests on the book
prices = snx.get_market_prices()
mark = float(prices["BTC-USDT"]["markPrice"])
bid_price = str(round(mark * 0.95))
modified_price = str(round(mark * 0.93))
print(f"BTC mark price: {mark}  →  bid at {bid_price} (5% below)\n")

# First, place an order to modify
snx.place_order(
    symbol="BTC-USDT",
    side="buy",
    quantity="0.001",
    price=bid_price,
    order_type="limitGtc",
)

orders = snx.get_open_orders()
if not orders:
    print("No open orders to modify")
    exit()

order = orders[0]
print(f"Before: id={order['order']['venueId']}  price={order['price']}  qty={order['quantity']}")

# Modify the price (move to 7% below mark)
result = snx.modify_order(
    order_id=int(order["order"]["venueId"]),
    price=modified_price,
    quantity="0.002",
)
print(f"\nModify result: {result}")

# Verify
orders = snx.get_open_orders()
if orders:
    o = orders[0]
    print(f"After:  id={o['order']['venueId']}  price={o['price']}  qty={o['quantity']}")

# Clean up
snx.cancel_all_orders("BTC-USDT")
print("\nCanceled all orders.")

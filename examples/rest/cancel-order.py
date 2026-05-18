"""
Cancel a single order by ID.

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
print(f"BTC mark price: {mark}  →  bid at {bid_price} (5% below)\n")

# Place an order to cancel
snx.place_order(
    symbol="BTC-USDT",
    side="buy",
    quantity="0.001",
    price=bid_price,
    order_type="limitGtc",
)

orders = snx.get_open_orders()
if not orders:
    print("No open orders to cancel")
    exit()

order_id = int(orders[0]["order"]["venueId"])
print(f"Canceling order {order_id}...")

result = snx.cancel_order(order_id)
print(f"Cancel result: {result}")

# Verify
remaining = snx.get_open_orders()
print(f"\nRemaining open orders: {len(remaining)}")

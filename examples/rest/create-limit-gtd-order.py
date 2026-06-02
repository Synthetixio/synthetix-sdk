"""
Place a limit Good-Til-Date (GTD) order.

The order stays on the book until filled, canceled, or the expiry time is reached.

Requires: PRIVATE_KEY environment variable.
"""

import os
import time

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

# Expire 1 hour from now (Unix timestamp in seconds)
expires_at = int(time.time()) + 3600

result = snx.place_order(
    symbol="BTC-USDT",
    side="buy",
    quantity="0.001",
    price=bid_price,
    order_type="limitGtd",
    expires_at=expires_at,
)
print(f"Limit GTD order result: {result}")

# Verify it's resting and has expiresAt
orders = snx.get_open_orders()
print(f"\nOpen orders: {len(orders)}")
for o in orders:
    expires = o.get("expiresAt", "")
    print(
        f"  id={o['order']['venueId']}  {o['symbol']}  {o['side']}"
        f"  price={o['price']}  qty={o['quantity']}" + (f"  expires={expires}" if expires else "")
    )

# Clean up
snx.cancel_all_orders("BTC-USDT")
print("\nCanceled all orders.")

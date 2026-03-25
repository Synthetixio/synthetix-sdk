"""
Cancel an order by client order ID (cloid).

Instead of tracking the venue-assigned order ID, you can assign your own
client order ID when placing an order, then use it to cancel later.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix
from synthetix.signing import generate_client_order_id

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Generate a client order ID and place an order with it
cloid = generate_client_order_id()
print(f"Placing order with cloid: {cloid}")

result = snx.place_order(
    symbol="BTC-USDT",
    side="buy",
    quantity="0.001",
    price="10000",
    order_type="limitGtc",
    client_order_id=cloid,
)
print(f"Place result: {result}\n")

# Cancel by client order ID (no need to look up the venue order ID)
print(f"Canceling by cloid: {cloid}")
cancel_result = snx.cancel_order_by_cloid(cloid)
print(f"Cancel result: {cancel_result}\n")

# Verify
remaining = snx.get_open_orders()
print(f"Remaining open orders: {len(remaining)}")

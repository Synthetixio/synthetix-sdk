"""
Place a limit Immediate-Or-Cancel (IOC) order.

Fills whatever is available at the limit price or better, then cancels the rest.
Useful for taking liquidity without leaving a resting order.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# IOC buy at a price far below market — will not fill, immediately cancels
result = snx.place_order(
    symbol="ETH-USDT",
    side="buy",
    quantity="0.01",
    price="100",  # far below market, won't fill
    order_type="limitIoc",  # immediate-or-cancel
)
print(f"Limit IOC order result: {result}")

# Should have no resting orders since IOC unfilled portion is canceled
orders = snx.get_open_orders()
print(f"\nOpen orders after IOC: {len(orders)}")

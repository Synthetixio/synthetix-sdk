"""
Place a TWAP order using batch orders.

Uses grouping="twap" to route a time-weighted order through the
batch place_orders endpoint. TWAP requires >= $10k notional and
minimum 300s duration.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

prices = snx.get_market_prices()
btc_mark = float(prices["BTC-USDT"]["markPrice"])
limit_price = str(round(btc_mark * 1.05))
twap_qty = str(round(10_500 / btc_mark, 3))  # just above $10k minimum

orders = [
    {
        "symbol": "BTC-USDT",
        "side": "buy",
        "orderType": "twap",
        "quantity": twap_qty,
        "durationSeconds": 300,
        "price": limit_price,
    },
]
result = snx.place_orders(orders, grouping="twap")
print(f"TWAP buy {twap_qty} BTC over 300s, limit {limit_price}")
print(f"Result: {result}")

# Clean up
snx.cancel_all_orders("BTC-USDT")
print("\nCanceled TWAP order")

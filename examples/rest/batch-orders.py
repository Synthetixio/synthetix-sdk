"""
Place multiple orders in a single request.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Place several limit orders at once
orders = [
    {
        "symbol": "BTC-USDT",
        "side": "buy",
        "orderType": "limitGtc",
        "price": "10000",
        "quantity": "0.001",
        "reduceOnly": False,
        "clientOrderId": "",
        "closePosition": False,
        "triggerPrice": "",
        "isTriggerMarket": False,
    },
    {
        "symbol": "ETH-USDT",
        "side": "buy",
        "orderType": "limitGtc",
        "price": "100",
        "quantity": "0.01",
        "reduceOnly": False,
        "clientOrderId": "",
        "closePosition": False,
        "triggerPrice": "",
        "isTriggerMarket": False,
    },
]

result = snx.place_orders(orders, grouping="na")
print(f"Batch order result: {result}")

# Check open orders
open_orders = snx.get_open_orders()
print(f"\nOpen orders: {len(open_orders)}")
for o in open_orders:
    print(f"  id={o['orderId']}  {o['symbol']}  {o['side']}  price={o['price']}")

# Clean up
snx.cancel_all_orders("BTC-USDT")
snx.cancel_all_orders("ETH-USDT")
print("\nCanceled all orders.")

"""
Place a TP/SL pair on an open position using batch orders.

Uses grouping="positionTpsl" to attach take-profit and stop-loss
orders to an existing position in a single request.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Open a small position to attach TP/SL to
fill = snx.market_order("ETH-USDT", "buy", "0.01")
entry = float(fill["statuses"][0]["filled"]["avgPrice"])
print(f"Opened ETH long at {entry}")

tp_price = str(round(entry * 1.10, 1))  # 10% above
sl_price = str(round(entry * 0.95, 1))  # 5% below

orders = [
    {
        "symbol": "ETH-USDT",
        "side": "sell",
        "orderType": "triggerTp",
        "quantity": "0.01",
        "triggerPrice": tp_price,
        "isTriggerMarket": True,
        "reduceOnly": True,
    },
    {
        "symbol": "ETH-USDT",
        "side": "sell",
        "orderType": "triggerSl",
        "quantity": "0.01",
        "triggerPrice": sl_price,
        "isTriggerMarket": True,
        "reduceOnly": True,
    },
]
result = snx.place_orders(orders, grouping="positionTpsl")
print(f"TP at {tp_price}, SL at {sl_price}")
print(f"Result: {result}\n")

# Clean up
snx.cancel_all_orders("ETH-USDT")
snx.market_order("ETH-USDT", "sell", "0.01")
print("Cleaned up: canceled orders and closed position")

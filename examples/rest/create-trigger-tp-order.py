"""
Place a take-profit trigger order.

The order activates when the mark price reaches the trigger price.
Requires an existing position — uses positionTpsl grouping automatically.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Check current positions first
positions = snx.get_positions()
if not positions:
    print("No open positions — open a position first before placing a TP order.")
    print("Example: snx.market_order('ETH-USDT', 'buy', '0.01')")
    exit()

pos = positions[0]
print(f"Position: {pos['symbol']}  {pos['side']}  qty={pos['quantity']}  entry={pos['entryPrice']}\n")

# TP well above entry for longs (2x), well below for shorts (0.5x)
# so it won't trigger immediately
entry = float(pos["entryPrice"])
tp_price = str(round(entry * 2)) if pos["side"] == "long" else str(round(entry * 0.5))

print(f"Setting take-profit at {tp_price}\n")

result = snx.place_order(
    symbol=pos["symbol"],
    side="sell" if pos["side"] == "long" else "buy",
    quantity=pos["quantity"],
    order_type="triggerTp",  # take-profit trigger
    trigger_price=tp_price,
    is_trigger_market=True,  # market execution when triggered
    reduce_only=True,
)
print(f"Take-profit order result: {result}")

# Verify
orders = snx.get_open_orders()
print(f"\nOpen orders: {len(orders)}")
for o in orders:
    print(f"  id={o['orderId']}  {o['symbol']}  type={o['type']}  trigger={o.get('triggerPrice', 'N/A')}")

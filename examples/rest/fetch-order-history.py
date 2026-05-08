"""
Fetch historical orders (filled, canceled, etc.).

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

now_ms = int(time.time() * 1000)
orders = snx.get_order_history(start_time=now_ms - 7 * 24 * 3600 * 1000, end_time=now_ms)

if not orders:
    print("No order history")
else:
    print(f"Order history: {len(orders)} orders\n")
    for o in orders[:20]:
        expires = o.get("expiresAt", "")
        reason = o.get("cancelReason", "")
        trigger_price = o.get("triggerPrice", "")
        trigger_price_type = o.get("triggerPriceType", "")
        tp_order = o.get("tpOrder")
        sl_order = o.get("slOrder")
        print(
            f"  id={o['order']['venueId']}"
            f"  {o['symbol']:12s}"
            f"  {o['side']:4s}"
            f"  type={o['type']:12s}"
            f"  price={o['price']:>12s}"
            f"  filled={o.get('filledQuantity', '0'):>12s}"
            f"  status={o.get('status', 'unknown')}"
            + (f"  expires={expires}" if expires else "")
            + (f"  cancelReason={reason}" if reason else "")
            + (f"  triggerPrice={trigger_price}({trigger_price_type})" if trigger_price else "")
            + (f"  tpOrder={tp_order['venueId']}" if tp_order else "")
            + (f"  slOrder={sl_order['venueId']}" if sl_order else "")
        )

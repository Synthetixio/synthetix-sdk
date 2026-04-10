"""
Fetch historical orders (filled, canceled, etc.).

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

orders = snx.get_order_history()

if not orders:
    print("No order history")
else:
    print(f"Order history: {len(orders)} orders\n")
    for o in orders[:20]:
        print(
            f"  id={o['orderId']}"
            f"  {o['symbol']:12s}"
            f"  {o['side']:4s}"
            f"  type={o['type']:12s}"
            f"  price={o['price']:>12s}"
            f"  filled={o.get('filledQuantity', '0'):>12s}"
            f"  status={o.get('status', 'unknown')}"
        )

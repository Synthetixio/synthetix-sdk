"""
Continuously poll positions in a loop.

Requires: PRIVATE_KEY environment variable.
"""

import os
import time

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}")
print("Polling positions every 5 seconds (Ctrl+C to stop)\n")

try:
    while True:
        positions = snx.get_positions()
        ts = time.strftime("%H:%M:%S")

        if not positions:
            print(f"[{ts}] No open positions")
        else:
            for p in positions:
                print(
                    f"[{ts}] {p['symbol']:12s}"
                    f"  {p['side']:5s}"
                    f"  qty={p['quantity']:>12s}"
                    f"  upnl={p['unrealizedPnl']:>12s}"
                    f"  liq={p.get('liquidationPrice', 'N/A'):>12s}"
                )

        time.sleep(5)
except KeyboardInterrupt:
    print("\nStopped.")

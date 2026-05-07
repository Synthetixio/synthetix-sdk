"""
Continuously poll account balance in a loop.

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
print("Polling balance every 5 seconds (Ctrl+C to stop)\n")

try:
    while True:
        account = snx.get_sub_account()
        margin = account.get("crossMarginSummary", {})
        ts = time.strftime("%H:%M:%S")

        print(
            f"[{ts}]"
            f"  value={margin.get('accountValue', 'N/A'):>14s}"
            f"  margin={margin.get('availableMargin', 'N/A'):>14s}"
            f"  upnl={margin.get('totalUnrealizedPnl', 'N/A'):>14s}"
        )

        time.sleep(5)
except KeyboardInterrupt:
    print("\nStopped.")

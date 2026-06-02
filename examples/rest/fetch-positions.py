"""
Fetch open positions.

Pass ``symbol`` to filter positions by market — e.g. ``snx.get_positions(symbol="BTC-USDT")``.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")


def _print(positions):
    if not positions:
        print("  (none)")
        return
    for p in positions:
        print(
            f"  {p['symbol']:20s}"
            f"  {p['side']:5s}"
            f"  qty={p['quantity']:>12s}"
            f"  entry={p['entryPrice']:>12s}"
            f"  upnl={p['unrealizedPnl']:>12s}"
            f"  liq={p.get('liquidationPrice', 'N/A'):>12s}"
        )


print("All open positions:")
_print(snx.get_positions())

print("\nBTC-USDT positions only:")
_print(snx.get_positions(symbol="BTC-USDT"))

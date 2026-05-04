"""
Fetch trade fill history.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

result = snx.get_trades()
trades = result.get("trades", [])
print(f"Trade history: {len(trades)} fills\n")

for t in trades[:20]:
    print(
        f"  {t['timestamp']}  {t['symbol']:12s}"
        f"  {t['side']:4s}"
        f"  price={t['price']:>12s}"
        f"  qty={t['quantity']:>12s}"
        f"  fee={t['fee']:>10s}"
        f"  pnl={t.get('realizedPnl', '0')}"
    )

"""
Fetch account performance history (PnL over time).

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

result = snx.get_performance_history(period="day")
ph = result.get("performanceHistory", {})
history = ph.get("history", [])
volume = ph.get("volume", "0")

print(f"Period:  {result.get('period')}")
print(f"Volume:  {volume}")
print(f"Samples: {len(history)}\n")

for point in history[:10]:
    print(f"  {point['sampledAt']}  accountValue={point['accountValue']:>16s}  pnl={point['pnl']:>14s}")

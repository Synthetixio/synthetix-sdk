"""
Fetch funding payment history with summary.

Requires: PRIVATE_KEY environment variable.
"""

import os
from pprint import pprint

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

result = snx.get_funding_payments()

print("--- Summary ---")
pprint(result.get("summary", {}))

payments = result.get("fundingHistory", [])
print(f"\n--- Last 10 of {len(payments)} payments ---")
for p in payments[:10]:
    print(f"  {p['timestamp']}  {p['symbol']:12s}  rate={p['fundingRate']:>14s}  payment={p['payment']:>14s}")

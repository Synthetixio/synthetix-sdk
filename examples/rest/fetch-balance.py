"""
Fetch account balance and margin summary.

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

account = snx.get_sub_account()

print("--- Collaterals ---")
for c in account.get("collaterals", []):
    print(f"  {c['symbol']:8s}  qty={c['quantity']:>14s}  withdrawable={c['withdrawable']}")

print("\n--- Cross Margin Summary ---")
pprint(account.get("crossMarginSummary", {}))

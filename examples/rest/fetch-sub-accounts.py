"""
List all subaccounts with balances and positions.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

accounts = snx.get_sub_accounts()

for sa in accounts.get("subAccounts", []):
    print(f"--- {sa.get('subAccountName', 'Unnamed')} (id={sa['subAccountId']}) ---")

    for c in sa.get("collaterals", []):
        print(f"  Collateral: {c['symbol']}  qty={c['quantity']}  withdrawable={c['withdrawable']}")

    margin = sa.get("crossMarginSummary", {})
    if margin:
        print(f"  Account value: {margin.get('accountValue', 'N/A')}")
        print(f"  Available margin: {margin.get('availableMargin', 'N/A')}")
        print(f"  Unrealized PnL: {margin.get('totalUnrealizedPnl', 'N/A')}")

    positions = sa.get("positions", [])
    if positions:
        for p in positions:
            print(f"  Position: {p['symbol']}  {p['side']}  qty={p['quantity']}  upnl={p.get('upnl', 'N/A')}")

    print()

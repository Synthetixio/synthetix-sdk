"""
Transfer collateral between subaccounts.

Requires: PRIVATE_KEY environment variable and at least two subaccounts.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# List subaccounts to find a destination
accounts = snx.get_sub_accounts()
sub_accounts = accounts.get("subAccounts", [])
print(f"Found {len(sub_accounts)} subaccounts:")
for sa in sub_accounts:
    print(f"  id={sa['subAccountId']}  name={sa.get('subAccountName', 'N/A')}")

if len(sub_accounts) < 2:
    print("\nNeed at least 2 subaccounts. Create one first with create-subaccount.py")
    exit()

# Transfer 1 USDT to the second subaccount
to_id = int(sub_accounts[1]["subAccountId"])
result = snx.transfer_collateral(
    amount="1",
    to_subaccount_id=to_id,
    symbol="USDT",
)
print(f"\nTransfer result: {result}")

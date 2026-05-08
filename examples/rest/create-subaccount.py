"""
Create a new subaccount.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

result = snx.create_subaccount(name="My New Subaccount")
print(f"Created subaccount: {result}")

# List all subaccounts
accounts = snx.get_sub_accounts()
for sa in accounts.get("subAccounts", []):
    print(f"  id={sa['subAccountId']}  name={sa.get('subAccountName', 'N/A')}")

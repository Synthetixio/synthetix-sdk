"""
Fetch portfolio snapshots.

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

portfolio = snx.get_portfolio()

if not portfolio:
    print("No portfolio data")
else:
    print(f"Portfolio snapshots: {len(portfolio)}\n")
    pprint(portfolio[0])

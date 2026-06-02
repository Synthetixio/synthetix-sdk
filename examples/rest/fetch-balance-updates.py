"""
Fetch balance update history (deposits, withdrawals, PnL settlements, fees).

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

result = snx.get_balance_updates()
updates = result.get("balanceUpdates", [])
print(f"Balance updates: {len(updates)} entries\n")

for u in updates[:20]:
    gross = u.get("grossAmount", u.get("amount", "?"))
    fee = u.get("fee", "0")
    usdt = u.get("usdtNotional", "?")
    print(
        f"  {u.get('timestamp', '?')}  {u.get('action', '?'):20s}"
        f"  amount={u.get('amount', '?'):>14s}"
        f"  fee={fee:>10s}"
        f"  gross={gross:>14s}"
        f"  usdt={usdt:>14s}"
        f"  {u.get('collateral', '?')}"
    )

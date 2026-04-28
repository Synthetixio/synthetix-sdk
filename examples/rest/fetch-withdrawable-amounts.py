"""Fetch withdrawable collateral amounts for the authenticated subaccount."""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))

result = snx.get_withdrawable_amounts(["USDT", "ETH"])
total = result.get("totalWithdrawableUsdt", "0")
print(f"Total withdrawable (USDT): {total}\n")

for item in result.get("items", []):
    print(f"  {item['symbol']}:")
    print(f"    quantity:           {item['quantity']}")
    print(f"    withdrawableAmount: {item['withdrawableAmount']}")
    print(f"    pendingWithdraw:    {item['pendingWithdraw']}")
    print(f"    withdrawFee:        {item['withdrawFee']}")

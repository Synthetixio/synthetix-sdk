"""
Fetch the exchange's fee/account tier configuration.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

tiers = snx.get_tiers()
print(f"{len(tiers)} tier(s) configured\n")

for t in tiers:
    print(
        f"  {t['tierName']:20s}"
        f"  type={t['tierType']:8s}"
        f"  minVolume={t['minTradeVolume']:>14s}"
        f"  maker={t['makerFeeRate']:>10s}"
        f"  taker={t['takerFeeRate']:>10s}"
        f"  maxSubs={t['maxSubAccounts']:>4d}"
        f"  maxOrders/mkt={t['maxOrdersPerMarket']:>5d}"
        f"  maxOrders={t['maxTotalOrders']:>5d}"
        f"  borrowCap={t['maxBorrowCapacity']:>14s}"
    )

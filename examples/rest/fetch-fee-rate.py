"""
Fetch the current maker/taker fee rate and tier schedule.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

fee_rate = snx.get_fee_rate()
print(f"14-day volume: {fee_rate['volume14d']}")
print(f"Maker fee:     {fee_rate['makerFeeRate']}")
print(f"Taker fee:     {fee_rate['takerFeeRate']}")

current = fee_rate.get("currentTier", {})
print(f"Current tier:  {current.get('tierName')} (id={current.get('tierId')})")

if fee_rate.get("referralDiscountApplied"):
    print(f"Referral discount applied: {fee_rate['referralDiscount']}")

print("\nFee schedule:")
for tier in fee_rate.get("tiers", []):
    print(
        f"  {tier['tierName']:<12s}"
        f"  minVolume={tier['minTradeVolume']:>12s}"
        f"  maker={tier['makerFeeRate']:>10s}"
        f"  taker={tier['takerFeeRate']:>10s}"
    )

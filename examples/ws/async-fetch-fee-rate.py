"""
Fetch the current maker/taker fee rate and tier schedule via WebSocket.

Requires: PRIVATE_KEY environment variable.
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(
        private_key=os.environ["PRIVATE_KEY"],
        rest_url=os.environ.get("REST_URL_OVERRIDE"),
        ws_url=os.environ.get("WS_URL_OVERRIDE"),
    )
    print(f"Wallet:     {snx.address}")
    print(f"Subaccount: {snx.subaccount_id}\n")

    fee_rate = await snx.ws_get_fee_rate()
    print(f"14-day volume: {fee_rate['volume14d']}")
    print(f"Maker fee:     {fee_rate['makerFeeRate']}")
    print(f"Taker fee:     {fee_rate['takerFeeRate']}")

    current = fee_rate.get("currentTier", {})
    print(f"Current tier:  {current.get('tierName')} (id={current.get('tierId')})")

    if fee_rate.get("referralDiscountApplied"):
        print(f"Referral discount applied: {fee_rate['referralDiscount']}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

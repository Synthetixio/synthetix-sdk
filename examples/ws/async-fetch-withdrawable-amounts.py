"""
Fetch withdrawable collateral amounts via WebSocket.

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

    result = await snx.ws_get_withdrawable_amounts(["USDT", "ETH"])
    total = result.get("totalWithdrawableUsdt", "0")
    print(f"Total withdrawable (USDT): {total}\n")

    for item in result.get("items", []):
        print(f"  {item['symbol']}:")
        print(f"    quantity:           {item['quantity']}")
        print(f"    withdrawableAmount: {item['withdrawableAmount']}")
        print(f"    pendingWithdraw:    {item['pendingWithdraw']}")
        print(f"    withdrawFee:        {item['withdrawFee']}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

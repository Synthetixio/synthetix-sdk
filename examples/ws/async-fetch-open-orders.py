"""
Fetch open orders via WebSocket.

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

    orders = await snx.ws_get_open_orders()

    if not orders:
        print("No open orders")
    else:
        for o in orders:
            expires = o.get("expiresAt", "")
            line = (
                f"  id={o['order']['venueId']}"
                f"  {o['symbol']:12s}"
                f"  {o['side']:4s}"
                f"  type={o['type']:12s}"
                f"  price={o['price']:>12s}"
                f"  qty={o['quantity']:>12s}"
            )
            if expires:
                line += f"  expires={expires}"
            print(line)
            twap = o.get("twapDetails")
            if twap:
                print(
                    f"    twap: avg={twap.get('averagePrice', '?')}"
                    f"  filled={twap.get('tradesFilled', '?')}/{twap.get('totalTrades', '?')}"
                    f"  fees={twap.get('totalFees', '?')}"
                    f"  started={twap.get('startedAtMs', '?')}ms"
                )

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

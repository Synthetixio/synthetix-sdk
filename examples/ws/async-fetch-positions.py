"""
Fetch positions via WebSocket.

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

    positions = await snx.ws_get_positions()

    if not positions:
        print("No open positions")
    else:
        for p in positions:
            print(
                f"  {p['symbol']:20s}"
                f"  {p['side']:5s}"
                f"  qty={p['quantity']:>12s}"
                f"  entry={p['entryPrice']:>12s}"
                f"  upnl={p['unrealizedPnl']:>12s}"
            )

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

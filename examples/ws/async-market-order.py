"""
Place a market order via WebSocket.

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

    result = await snx.ws_market_order("ETH-USDT", "buy", "0.01")
    print(f"WS market order result: {result}")

    # Check positions
    positions = await snx.ws_get_positions()
    print("\nPositions:")
    for p in positions:
        print(f"  {p['symbol']}  {p['side']}  qty={p['quantity']}  entry={p['entryPrice']}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

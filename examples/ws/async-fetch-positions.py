"""
Fetch positions via WebSocket.

Pass ``symbol`` to filter positions by market — e.g.
``await snx.ws_get_positions(symbol="BTC-USDT")``.

Requires: PRIVATE_KEY environment variable.
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


def _print(positions):
    if not positions:
        print("  (none)")
        return
    for p in positions:
        print(
            f"  {p['symbol']:20s}"
            f"  {p['side']:5s}"
            f"  qty={p['quantity']:>12s}"
            f"  entry={p['entryPrice']:>12s}"
            f"  upnl={p['unrealizedPnl']:>12s}"
        )


async def main():
    snx = Synthetix(
        private_key=os.environ["PRIVATE_KEY"],
        rest_url=os.environ.get("REST_URL_OVERRIDE"),
        ws_url=os.environ.get("WS_URL_OVERRIDE"),
    )
    print(f"Wallet:     {snx.address}")
    print(f"Subaccount: {snx.subaccount_id}\n")

    print("All open positions:")
    _print(await snx.ws_get_positions())

    print("\nBTC-USDT positions only:")
    _print(await snx.ws_get_positions(symbol="BTC-USDT"))

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

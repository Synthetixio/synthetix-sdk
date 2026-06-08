"""
Fetch trade fills for a specific position via WebSocket.

Requires: PRIVATE_KEY environment variable.
Pass a positionId as the first argument, or the script will use the most
recent closed position automatically.
"""

import asyncio
import os
import sys

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

    if len(sys.argv) > 1:
        position_id = sys.argv[1]
    else:
        history = snx.get_position_history(limit=1)
        positions = history.get("positions", [])
        if not positions:
            print("No closed positions found. Pass a positionId as the first argument.")
            await snx.close()
            return
        position_id = positions[0]["positionId"]
        print(f"Using most recent closed position: {position_id}\n")

    result = await snx.ws_get_trades_for_position(position_id)
    trades = result.get("trades", [])
    print(f"Trades for position {position_id}: {len(trades)} fills (hasMore={result.get('hasMore')})\n")

    for t in trades[:20]:
        print(
            f"  {t['timestamp']}  {t['symbol']:12s}"
            f"  {t['side']:4s}"
            f"  price={t['price']:>12s}"
            f"  qty={t['quantity']:>12s}"
            f"  fee={t['fee']:>10s}"
            f"  pnl={t.get('realizedPnl', '0')}"
        )

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

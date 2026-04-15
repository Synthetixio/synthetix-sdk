"""
Stream live liquidation events via WebSocket.

Requires a concrete symbol — "ALL" is not supported for this channel.
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"), ws_url=os.environ.get("WS_URL_OVERRIDE"))

    def on_liquidation(msg):
        payload = msg.get("data", msg)
        events = payload if isinstance(payload, list) else [payload]
        for e in events:
            print(
                f"[liquidation] {e.get('symbol', '?'):12s}"
                f"  side={e.get('side', '?'):5s}"
                f"  price={e.get('price', '?'):>12s}"
                f"  qty={e.get('quantity', '?'):>12s}"
            )

    print("Subscribing to ETH-USDT liquidations...")
    sub_id = await snx.subscribe("liquidations", on_liquidation, symbol="ETH-USDT")

    try:
        await asyncio.sleep(60)
    finally:
        await snx.unsubscribe(sub_id)
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

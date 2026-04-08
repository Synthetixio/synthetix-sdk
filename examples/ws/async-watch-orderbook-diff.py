"""
Stream live orderbook diffs via WebSocket.

Diff mode (the default) sends an initial snapshot, then only changed price
levels on subsequent updates.  Levels with quantity "0" have been removed.

Params used:
  - format="diff" (default, can be omitted)
  - depth=10  (10 levels per side)
  - updateFrequencyMs=100  (100ms throttle)
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"), ws_url=os.environ.get("WS_URL_OVERRIDE"))

    def on_orderbook(msg):
        msg_type = msg.get("type", "update")
        book = msg.get("data", msg)
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        best_bid = bids[0] if bids else None
        best_ask = asks[0] if asks else None
        print(f"[{msg_type}] best_bid={best_bid}  best_ask={best_ask}  ({len(bids)} bids, {len(asks)} asks)")

    print("Subscribing to BTC-USDT orderbook (diff, depth=10, 100ms)...")
    sub_id = await snx.subscribe(
        "orderbook",
        on_orderbook,
        symbol="BTC-USDT",
        format="diff",
        depth=10,
        updateFrequencyMs=100,
    )

    try:
        await asyncio.sleep(15)
    finally:
        await snx.unsubscribe(sub_id)
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

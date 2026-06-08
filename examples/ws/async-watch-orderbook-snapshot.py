"""
Stream full orderbook snapshots via WebSocket.

Snapshot mode sends the complete book (up to the requested depth) on every
update — no need to track diffs or maintain local state.

Params used:
  - format="snapshot"
  - depth=10  (10 levels per side)
  - updateFrequencyMs=250  (250ms throttle)
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"), ws_url=os.environ.get("WS_URL_OVERRIDE"))

    def on_orderbook(msg):
        book = msg.get("data", msg)
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        best_bid = bids[0] if bids else None
        best_ask = asks[0] if asks else None
        print(f"[snapshot] best_bid={best_bid}  best_ask={best_ask}  ({len(bids)} bids, {len(asks)} asks)")

    print("Subscribing to BTC-USDT orderbook (snapshot, depth=10, 250ms)...")
    sub_id = await snx.subscribe(
        "orderbook",
        on_orderbook,
        symbol="BTC-USDT",
        format="snapshot",
        depth=10,
        updateFrequencyMs=250,
    )

    try:
        await asyncio.sleep(15)
    finally:
        await snx.unsubscribe(sub_id)
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

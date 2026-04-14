"""
Place a limit post-only order via WebSocket.

The order is rejected if it would immediately match (cross the spread).
If accepted, it rests on the book as a maker order.

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

    # Get current mark price and place 5% below so it rests on the book
    prices = snx.get_market_prices()
    mark = float(prices["BTC-USDT"]["markPrice"])
    bid_price = str(round(mark * 0.95))
    print(f"BTC mark price: {mark}  →  bid at {bid_price} (5% below)\n")

    # Place a post-only buy below market so it rests as a maker order
    result = await snx.ws_place_order(
        symbol="BTC-USDT",
        side="buy",
        quantity="0.001",
        price=bid_price,  # below market — guaranteed to rest
        post_only=True,  # rejected if it would cross the spread
    )
    print(f"WS post-only order result: {result}")

    # Clean up
    cancel = await snx.ws_cancel_all_orders("BTC-USDT")
    print(f"WS cancel result: {cancel}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

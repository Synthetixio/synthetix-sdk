"""
Place a post-only GTD order via WebSocket that auto-expires after 30 seconds.

Combines limitGtd (auto-expiry) with postOnly (rejected if it would cross
the spread). Useful when you want maker-only orders with guaranteed cleanup
if your cancel logic fails.

Requires: PRIVATE_KEY environment variable.
"""

import asyncio
import os
import time

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
    print(f"BTC mark price: {mark}  ->  bid at {bid_price} (5% below)\n")

    # Expire 30 seconds from now (Unix timestamp in seconds)
    expires_at = int(time.time()) + 30

    result = await snx.ws_place_order(
        symbol="BTC-USDT",
        side="buy",
        quantity="0.001",
        price=bid_price,
        order_type="limitGtd",
        post_only=True,
        expires_at=expires_at,
    )
    print(f"GTD + postOnly order result: {result}")

    # Verify it's resting
    open_orders = await snx.ws_get_open_orders()
    print(f"\nOpen orders: {len(open_orders)}")
    for o in open_orders:
        expires = o.get("expiresAt", "")
        print(
            f"  id={o['order']['venueId']}  {o['symbol']}  {o['side']}"
            f"  price={o['price']}  qty={o['quantity']}" + (f"  expires={expires}" if expires else "")
        )

    # Wait for auto-expiry
    print("\nWaiting 35s for GTD expiry...")
    await asyncio.sleep(35)

    open_orders = await snx.ws_get_open_orders()
    print(f"Open orders after expiry: {len(open_orders)}")
    if not open_orders:
        print("Order expired as expected.")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

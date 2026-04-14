"""
Place a limit Good-Til-Date (GTD) order via WebSocket.

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
    print(f"BTC mark price: {mark}  →  bid at {bid_price} (5% below)\n")

    # Expire 1 hour from now
    expires_at = int(time.time()) + 3600

    result = await snx.ws_place_order(
        symbol="BTC-USDT",
        side="buy",
        quantity="0.001",
        price=bid_price,
        order_type="limitGtd",
        expires_at=expires_at,
    )
    print(f"WS limitGtd order result: {result}")

    # Verify via WS query
    open_orders = await snx.ws_get_open_orders()
    print(f"\nOpen orders: {len(open_orders)}")
    for o in open_orders:
        expires = o.get("expiresAt", "")
        print(
            f"  id={o['order']['venueId']}  {o['symbol']}  {o['side']}"
            f"  price={o['price']}  qty={o['quantity']}" + (f"  expires={expires}" if expires else "")
        )

    # Clean up
    await snx.ws_cancel_all_orders("BTC-USDT")
    print("\nCanceled all orders.")
    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

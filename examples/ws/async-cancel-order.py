"""
Cancel an order via WebSocket.

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

    # Place an order to cancel
    await snx.ws_place_order(
        symbol="BTC-USDT",
        side="buy",
        quantity="0.001",
        price="10000",
        order_type="limitGtc",
    )

    # Get open orders
    orders = await snx.ws_get_open_orders()
    if not orders:
        print("No open orders to cancel")
        await snx.close()
        return

    order_id = int(orders[0]["orderId"])
    print(f"Canceling order {order_id}...")

    result = await snx.ws_cancel_order(order_id)
    print(f"WS cancel result: {result}")

    remaining = await snx.ws_get_open_orders()
    print(f"Remaining open orders: {len(remaining)}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

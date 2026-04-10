"""
Cancel an order by client order ID (cloid) via WebSocket.

Requires: PRIVATE_KEY environment variable.
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix
from synthetix.signing import generate_client_order_id

load_dotenv()


async def main():
    snx = Synthetix(
        private_key=os.environ["PRIVATE_KEY"],
        rest_url=os.environ.get("REST_URL_OVERRIDE"),
        ws_url=os.environ.get("WS_URL_OVERRIDE"),
    )
    print(f"Wallet:     {snx.address}")
    print(f"Subaccount: {snx.subaccount_id}\n")

    # Generate a client order ID and place an order with it
    cloid = generate_client_order_id()
    print(f"Placing order with cloid: {cloid}")

    result = await snx.ws_place_order(
        symbol="BTC-USDT",
        side="buy",
        quantity="0.001",
        price="10000",
        order_type="limitGtc",
        client_order_id=cloid,
    )
    print(f"Place result: {result}\n")

    # Cancel by client order ID via WebSocket
    print(f"Canceling by cloid: {cloid}")
    cancel_result = await snx.ws_cancel_order_by_cloid(cloid)
    print(f"Cancel result: {cancel_result}\n")

    remaining = await snx.ws_get_open_orders()
    print(f"Remaining open orders: {len(remaining)}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

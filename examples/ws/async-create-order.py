"""
Place a limit order via WebSocket.

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

    # Place a limit buy far below market
    result = await snx.ws_place_order(
        symbol="BTC-USDT",
        side="buy",
        quantity="0.001",
        price="50000",
        order_type="limitGtc",
    )
    print(f"WS place order result: {result}")

    # Clean up
    cancel = await snx.ws_cancel_all_orders("BTC-USDT")
    print(f"WS cancel result: {cancel}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

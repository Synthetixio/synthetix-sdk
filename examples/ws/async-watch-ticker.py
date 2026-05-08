"""
Stream live market prices via WebSocket.
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"), ws_url=os.environ.get("WS_URL_OVERRIDE"))

    def on_price(data):
        print(f"[ticker] {data}")

    print("Subscribing to ETH-USDT prices...")
    sub_id = await snx.subscribe("marketPrices", on_price, symbol="ETH-USDT")

    try:
        await asyncio.sleep(15)
    finally:
        await snx.unsubscribe(sub_id)
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

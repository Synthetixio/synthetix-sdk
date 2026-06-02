"""
Stream live market prices with an on_error callback.

Demonstrates how to catch and handle exceptions raised inside
a subscription callback without losing the subscription.
"""

import asyncio
import os
import time

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"), ws_url=os.environ.get("WS_URL_OVERRIDE"))
    start = time.monotonic()

    def on_price(data):
        elapsed = time.monotonic() - start
        if elapsed >= 8:
            # Simulate a bug — 'missing_key' doesn't exist
            print(data["missing_key"])
        print(f"[{elapsed:.1f}s] price update received")

    def on_error(exc, data):
        print(f"[error] callback failed: {exc}")
        print(f"[error] message was: {data}")

    print("Subscribing to ETH-USDT prices (with on_error)...")
    sub_id = await snx.subscribe(
        "marketPrices",
        on_price,
        on_error=on_error,
        symbol="ETH-USDT",
    )

    try:
        await asyncio.sleep(15)
    finally:
        await snx.unsubscribe(sub_id)
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

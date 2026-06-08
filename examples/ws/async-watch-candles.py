"""
Stream live candlestick updates via WebSocket.
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"), ws_url=os.environ.get("WS_URL_OVERRIDE"))

    def on_candle(data):
        print(f"[candle] {data}")

    print("Subscribing to BTC-USDT 1h candles...")
    sub_id = await snx.subscribe("candles", on_candle, symbol="BTC-USDT", timeframe="1h")

    try:
        await asyncio.sleep(30)
    finally:
        await snx.unsubscribe(sub_id)
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

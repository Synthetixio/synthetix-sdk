"""
Stream live public trades via WebSocket.
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"), ws_url=os.environ.get("WS_URL_OVERRIDE"))

    def on_trade(msg):
        payload = msg.get("data", msg)
        trades = payload if isinstance(payload, list) else [payload]
        for t in trades:
            print(
                f"[trade] {t.get('symbol', '?'):12s}"
                f"  {t.get('side', '?'):4s}"
                f"  price={t.get('price', '?'):>12s}"
                f"  qty={t.get('quantity', '?'):>12s}"
            )

    print("Subscribing to ETH-USDT trades...")
    sub_id = await snx.subscribe("trades", on_trade, symbol="ETH-USDT")

    try:
        await asyncio.sleep(30)
    finally:
        await snx.unsubscribe(sub_id)
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

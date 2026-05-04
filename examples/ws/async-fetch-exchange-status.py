"""
Check exchange status from both REST and WS servers (async, parallel).

No authentication required.
"""

import asyncio
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()


async def main():
    snx = Synthetix(
        rest_url=os.environ.get("REST_URL_OVERRIDE"),
        ws_url=os.environ.get("WS_URL_OVERRIDE"),
    )

    status = await snx.ws_get_exchange_status()

    for server in ("rest", "ws"):
        s = status[server]
        print(f"[{server.upper()}] {s['exchange_status']}  accepting_orders={s['accepting_orders']}  {s['message']}")


if __name__ == "__main__":
    asyncio.run(main())

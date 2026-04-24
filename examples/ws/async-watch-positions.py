"""
Stream live subaccount updates (positions, balances) via WebSocket.

Requires: PRIVATE_KEY environment variable.
"""

import asyncio
import os
from pprint import pprint

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

    def on_update(data):
        print("[subAccountUpdate]")
        pprint(data)
        print()

    print("Subscribing to subaccount updates...")
    sub_id = await snx.subscribe("subAccountUpdates", on_update)

    try:
        await asyncio.sleep(60)
    finally:
        await snx.unsubscribe(sub_id)
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

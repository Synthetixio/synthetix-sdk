"""
Rename a subaccount via WebSocket.

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

    new_name = "My Trading Account"
    result = await snx.ws_update_sub_account_name(new_name)
    print(f"Renamed subaccount {result['subAccountId']} to '{result['name']}'")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

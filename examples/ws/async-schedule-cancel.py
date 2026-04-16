"""
Configure the dead-man switch (schedule cancel) via WebSocket.

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

    # Arm the dead-man switch with a 60-second timeout
    result = await snx.ws_schedule_cancel(60)
    print(f"Armed:   isActive={result['isActive']}, timeout={result['timeoutSeconds']}s")

    # Disable the dead-man switch
    result = await snx.ws_schedule_cancel(0)
    print(f"Disabled: isActive={result['isActive']}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

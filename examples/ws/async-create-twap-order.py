"""
Place a TWAP order via WebSocket.

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

    # TWAP requires minimum $10,000 notional and 300s duration
    prices = snx.get_market_prices()
    mark = float(prices["BTC-USDT"]["markPrice"])
    limit_price = str(round(mark * 1.05))
    quantity = str(round(10_500 / mark, 3))  # just above $10k minimum
    print(f"BTC mark price: {mark}  →  TWAP {quantity} BTC, limit at {limit_price} (5% above)\n")

    # Place a TWAP buy over 5 minutes
    result = await snx.ws_twap_order(
        symbol="BTC-USDT",
        side="buy",
        quantity=quantity,
        duration_seconds=300,
        price=limit_price,
    )
    status = result["statuses"][0]
    print(f"WS TWAP order result: {status}")

    # Cancel the TWAP order
    oid = int(status["resting"]["order"]["venueId"])
    cancel = await snx.ws_cancel_order(oid)
    print(f"\nCanceled TWAP order {oid}: {cancel}")

    await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

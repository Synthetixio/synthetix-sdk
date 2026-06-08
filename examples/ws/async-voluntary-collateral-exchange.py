"""
Voluntarily exchange a non-USDT collateral for USDT via WebSocket.

The exchange only runs when the subaccount holds USDT debt (a negative USDT
balance); it converts non-USDT collateral into USDT to cover that debt.

Requires: PRIVATE_KEY environment variable, a non-USDT collateral balance,
and a negative USDT balance (debt) on the active subaccount.
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

    try:
        # Pick the first non-USDT collateral with a positive balance
        collaterals = snx.get_sub_account().get("collaterals", [])
        source = next(
            (c["symbol"] for c in collaterals if c["symbol"] != "USDT" and float(c.get("quantity", "0")) > 0),
            None,
        )
        # The exchange only works when USDT is in debt (negative balance)
        usdt = next((c for c in collaterals if c["symbol"] == "USDT"), None)
        has_debt = usdt is not None and float(usdt.get("quantity", "0")) < 0

        if source is None:
            print("No non-USDT collateral with a positive balance found.")
        elif not has_debt:
            print("No USDT debt to cover — the USDT balance is not negative, so there is nothing to exchange.")
        else:
            print(f"Exchanging {source} for 1 USDT...\n")
            result = await snx.ws_voluntary_collateral_exchange(source_asset=source, target_usdt_amount="1")

            print(f"  source taken:     {result['sourceAmountTaken']} {result['sourceAsset']}")
            print(f"  target received:  {result['targetAmount']} {result['targetAsset']}")
            print(f"  index price:      {result['indexPrice']}")
            print(f"  effective haircut:{result['effectiveHaircut']}\n")

            print("Resulting collateral balances:")
            for entry in result.get("collateral", []):
                print(f"  {entry['symbol']:<8} {entry['quantity']}")
    finally:
        await snx.close()


if __name__ == "__main__":
    asyncio.run(main())

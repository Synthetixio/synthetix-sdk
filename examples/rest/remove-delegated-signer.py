"""
Remove a delegated signer.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Replace with the address to remove
delegate_address = "0x0000000000000000000000000000000000000001"

result = snx.remove_delegated_signer(delegate_address=delegate_address)
print(f"Remove delegated signer result: {result}")

# Verify
signers = snx.get_delegated_signers()
print(f"\nRemaining delegated signers: {signers}")

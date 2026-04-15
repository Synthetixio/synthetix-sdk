"""
Configure the dead-man switch (schedule cancel).

When armed, all open orders are automatically canceled if the server does not
receive a heartbeat within the configured timeout.

Pass timeout_seconds=0 to disable.

Requires: PRIVATE_KEY environment variable.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))
print(f"Wallet:     {snx.address}")
print(f"Subaccount: {snx.subaccount_id}\n")

# Arm the dead-man switch with a 5-minute timeout
result = snx.schedule_cancel(timeout_seconds=300)
print(f"isActive:       {result['isActive']}")
print(f"timeoutSeconds: {result['timeoutSeconds']}")
print(f"triggerTime:    {result.get('triggerTime')}")
print(f"message:        {result.get('message', '')}\n")

# Disable the dead-man switch
result = snx.schedule_cancel(timeout_seconds=0)
print("Disabled dead-man switch.")
print(f"isActive:       {result['isActive']}")

"""
Fetch historical (closed) positions for the authenticated subaccount.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["TEST_PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))

result = snx.get_position_history()
positions = result.get("positions", [])
has_more = result.get("hasMore", False)
print(f"Position history: {len(positions)} positions (hasMore={has_more})\n")

for p in positions:
    for key, value in p.items():
        print(f"  {key}: {value}")

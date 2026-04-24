"""
Fetch all available perps markets.
"""

import os
from pprint import pprint

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

markets = snx.get_markets()
print(f"Found {len(markets)} markets\n")

for m in markets:
    print(f"  {m['symbol']:20s}  base={m['baseAsset']:6s}  quote={m['quoteAsset']:6s}  minOrder={m['minOrderSize']}")

# Full detail for first market
print("\n--- First market detail ---")
pprint(markets[0])

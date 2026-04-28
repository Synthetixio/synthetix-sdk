"""
Fetch open interest for all markets.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

oi = snx.get_open_interest()
print(f"Open interest for {len(oi)} markets\n")

for m in oi:
    print(
        f"  {m['symbol']:20s}"
        f"  OI={m['openInterest']:>14s}"
        f"  long={m['longOpenInterest']:>14s}"
        f"  short={m['shortOpenInterest']:>14s}"
    )

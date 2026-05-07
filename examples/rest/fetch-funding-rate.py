"""
Fetch current funding rate for a symbol.
"""

import os
from pprint import pprint

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

symbol = "ETH-USDT"
funding = snx.get_funding_rate(symbol)

print(f"Funding rate for {symbol}\n")
pprint(funding)

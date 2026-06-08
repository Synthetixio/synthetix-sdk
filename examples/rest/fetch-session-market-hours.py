"""
Read the optional ``onHours`` field from getMarketPrices for a session market.

Session markets (e.g. ``WTI-USDT``) only trade during specific exchange hours.
Their ``getMarketPrices`` entry carries an extra ``onHours`` boolean indicating
whether the market is currently within trading hours. The field is omitted for
24/7 markets and for session markets when the state is not yet known.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))

prices = snx.get_market_prices()

wti = prices["WTI-USDT"]
on_hours = wti["onHours"]
state = "within trading hours" if on_hours else "outside trading hours"
print(f"WTI-USDT  mark={wti['markPrice']}  onHours={on_hours}  ({state})")

# Show every market that exposes onHours (i.e. every session market the server
# is currently reporting state for).
session_markets = {sym: data for sym, data in prices.items() if "onHours" in data}
print(f"\nSession markets reporting onHours ({len(session_markets)}):")
for sym, data in session_markets.items():
    print(f"  {sym:20s}  onHours={data['onHours']!s:5s}  mark={data['markPrice']}")

"""
Fetch position history filtered by symbol and time range.
"""

import os
import time

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(private_key=os.environ["TEST_PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))

symbol = "BTC-USDT"
end_time = int(time.time() * 1000)
start_time = end_time - 7 * 24 * 3_600_000  # last 7 days

result = snx.get_position_history(
    symbol=symbol,
    start_time=start_time,
    end_time=end_time,
    limit=5,
)
positions = result.get("positions", [])
has_more = result.get("hasMore", False)
print(f"{symbol} positions (last 7 days): {len(positions)} (hasMore={has_more})\n")

for p in positions:
    print(
        f"  {p.get('side', '?'):5s}"
        f"  entry={p.get('entryPrice', '?'):>12s}"
        f"  close={p.get('closePrice', '?'):>12s}"
        f"  pnl={p.get('realizedPnl', '?'):>12s}"
    )

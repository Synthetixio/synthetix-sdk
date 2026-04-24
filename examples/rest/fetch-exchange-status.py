"""
Check whether the exchange is operational or in maintenance.
Queries both the REST and WebSocket servers.
"""

import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

snx = Synthetix(
    rest_url=os.environ.get("REST_URL_OVERRIDE"),
    ws_url=os.environ.get("WS_URL_OVERRIDE"),
)

status = snx.get_exchange_status()

for server in ("rest", "ws"):
    s = status[server]
    print(f"[{server.upper()}] {s['exchange_status']}  accepting_orders={s['accepting_orders']}  {s['message']}")

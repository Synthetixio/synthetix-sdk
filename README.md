# synthetix-sdk

The official Python client for the [Synthetix V4](https://synthetix.io) perpetual futures exchange. Provides REST and WebSocket access for market data, trading, and account management, with EIP-712 signing built in.

Full API docs: [developers.synthetix.io](https://developers.synthetix.io/).

## Get going in 30 seconds with Claude Code

The fastest way to try the SDK is the bundled [Claude Code](https://claude.com/claude-code) skill. Clone the repo, run `/synthetix` in a Claude Code session, and Claude will set up the environment, write and run example scripts, and explain the SDK as you go — no reading docs first.

```bash
git clone https://github.com/Synthetixio/synthetix-sdk
cd synthetix-sdk
```

Then in Claude Code:

```
/synthetix stream live prices for ETH-USDT
/synthetix place a limit order
/synthetix check my open positions
/synthetix watch my positions in real time
```

Claude does the wiring — `.venv` setup, dependency install, script generation, running, and walking you through the output. Pass any natural-language goal after the slash command.

## Installation

To use the SDK in your own project:

```bash
pip install synthetix-sdk
```

Three runtime dependencies: `requests`, `eth-account`, `websockets`. Python 3.10+.

## Quick Start

```python
from synthetix import Synthetix

# Public market data — no private key needed
snx = Synthetix()
markets = snx.get_markets()
for m in markets:
    print(m["symbol"], m["description"])

# Authenticated — required for trading and account queries
snx = Synthetix(private_key="0x...")
print(snx.get_positions())
print(snx.get_portfolio())
```

For WebSocket streaming and async trading:

```python
import asyncio
from synthetix import Synthetix

async def main():
    snx = Synthetix(private_key="0x...")

    # Stream real-time prices (no auth required)
    sub = await snx.subscribe(
        "marketPrices",
        lambda d: print(d),
        symbol="ETH-USDT",
    )

    # Place an order over WebSocket
    result = await snx.ws_place_order(
        symbol="BTC-USDT",
        side="buy",
        amount="0.001",
        price="90000",
    )

    await asyncio.sleep(10)
    await snx.unsubscribe(sub)
    await snx.close()

asyncio.run(main())
```

## Features

### Market data (public, no key required)

- List markets, fees, funding rates, open interest
- Tickers, mark prices, mids
- Order books at multiple depths
- Recent trades, candles, funding rate history

### Trading

- Market, limit (GTC/GTD/IOC/post-only), TWAP, stop-loss, and take-profit orders
- Modify and cancel orders (single, batch, by client order ID, or all)
- Update leverage per market
- Schedule deferred cancellations as a kill-switch

### Account management

- Positions, P&L, balance, portfolio, performance history
- Trade and order history, open orders, fills
- Funding payments and rate-limit status
- Sub-accounts: create, query, transfer collateral
- Delegated signers for ops accounts

### WebSocket (async)

- Live subscriptions: prices, orderbook (snapshot/diff/managed), trades, positions, orders, fills, balances
- WS-native trading methods (`ws_place_order`, `ws_cancel_order`, `ws_modify_order`, …) — same signing, lower latency than REST
- Auto-reconnect with auth re-handshake and subscription replay
- Per-callback error handlers; sync and async callbacks both supported

## Configuration

```python
Synthetix(
    private_key=None,        # Omit for read-only mode
    subaccount_id=None,      # Auto-discovered if not set
    rest_url=None,           # Override REST URL (defaults to production)
    ws_url=None,             # Override WebSocket URL (defaults to production)
    timeout=None,            # Request timeout in seconds
    expires_after_ms=60000,  # Signed-message expiry window
)
```

URL overrides also read from `REST_URL_OVERRIDE` / `WS_URL_OVERRIDE` env vars. Defaults: `https://papi.synthetix.io/v1` and `wss://papi.synthetix.io/v1/ws`.

## Examples

The repo includes standalone scripts for every endpoint under `examples/rest/` and `examples/ws/`. Each is runnable on its own:

```bash
# Market data (no key)
python examples/rest/fetch-markets.py
python examples/rest/fetch-orderbook.py

# Trading (requires PRIVATE_KEY env var)
python examples/rest/create-limit-gtc-order.py
python examples/rest/cancel-order.py

# WebSocket
python examples/ws/async-watch-ticker.py
python examples/ws/async-market-order.py
python examples/ws/async-watch-positions.py
```

## API reference

- Full HTTP/WS protocol docs: [developers.synthetix.io](https://developers.synthetix.io/)
- [REST API](synthetix/rest/README.md) — `MarketAPI` (public) and `AccountAPI` (authenticated)
- [WebSocket API](synthetix/ws/README.md) — subscriptions, channels, and async trading methods

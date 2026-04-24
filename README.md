# synthetix-sdk

SDK for Synthetix Perps trading with Python.

## Using with Claude Code

This repo includes a [Claude Code](https://claude.com/claude-code) skill that walks you through setup, market data, and trading interactively. From the repo root:

```
/synthetix
```

Or pass what you want to try directly:

```
/synthetix stream live prices for ETH-USDT
/synthetix place a limit order
/synthetix check my open positions
```

Claude will set up the environment, write and run scripts, and explain the SDK as you go.

## Installation
```bash
pip install git+https://github.com/Synthetixio/synthetix-sdk.git
```

## Configuration

Set your private key as an environment variable:
```bash
export PRIVATE_KEY="0x..."
```

Optionally override the API endpoints:
```bash
export REST_URL_OVERRIDE="https://papi.synthetix.io/v1"
export WS_URL_OVERRIDE="wss://papi.synthetix.io/v1/ws"
```

## Constructor

```python
from synthetix import Synthetix

Synthetix(
    private_key=None,       # Omit for read-only mode
    subaccount_id=None,     # Auto-discovered if not set
    rest_url=None,          # Override REST URL (defaults to production)
    ws_url=None,            # Override WebSocket URL (defaults to production)
    timeout=None,
    expires_after_ms=60000,
)
```

## Usage Examples
```python
from synthetix import Synthetix

# Public (no auth) — uses production by default
snx = Synthetix()
markets = snx.get_markets()
for m in markets:
    print(m["symbol"], m["description"])

# Authenticated
snx = Synthetix(private_key="0x...")
positions = snx.get_positions()
print(positions)

# Custom endpoints
snx = Synthetix(rest_url="https://papi.synthetix.io/v1",
                ws_url="wss://papi.synthetix.io/v1/ws")
```

### WebSocket (async)
```python
import asyncio
from synthetix import Synthetix

async def main():
    snx = Synthetix(private_key="0x...")

    # Stream prices (no auth needed)
    sub = await snx.subscribe("marketPrices", lambda d: print(d), symbol="ETH-USDT")

    # With error handling — on_error is called if the callback raises
    def on_error(exc, data):
        print(f"Callback failed: {exc}")
    sub = await snx.subscribe("marketPrices", my_callback, on_error=on_error, symbol="ETH-USDT")

    # Place order via WebSocket
    result = await snx.ws_place_order("BTC-USDT", "buy", "0.001", price="90000")

    # Cancel via WebSocket
    await snx.ws_cancel_order(order_id=12345)

    await asyncio.sleep(10)
    await snx.unsubscribe(sub)
    await snx.close()

asyncio.run(main())
```

See [examples](examples) for more complete examples. You can also checkout the repo and run any of the examples after configuring your private key e.g.
```bash
# Public market data (no key required)
python examples/fetch-markets.py
python examples/fetch-ticker.py
python examples/fetch-orderbook.py

# Trading (requires PRIVATE_KEY exported)
python examples/create-limit-gtc-order.py
python examples/create-market-order.py
python examples/cancel-order.py

# WebSocket (async)
python examples/async-watch-ticker.py
python examples/async-market-order.py
python examples/async-watch-positions.py
```

## API Reference

- [REST API](synthetix/rest/README.md) — MarketAPI (public endpoints) and AccountAPI (authenticated endpoints)
- [WebSocket API](synthetix/ws/README.md) — subscriptions, channels, and async trading methods

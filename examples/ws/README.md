# WebSocket Examples

Async examples using the WebSocket API. Each file is a standalone script using `asyncio`.

## Setup

```bash
pip install synthetix-sdk
```

Subscription examples need no configuration. Trading/query examples require a private key:

```bash
export PRIVATE_KEY="0x..."
```

All examples use **production** by default. To use a different environment, set overrides in `.env`:

```bash
REST_URL_OVERRIDE="https://papi.synthetix.io/v1"
WS_URL_OVERRIDE="wss://papi.synthetix.io/v1/ws"
```

## Queries (public)

| Example | Description |
|---------|-------------|
| [async-fetch-exchange-status.py](async-fetch-exchange-status.py) | Check exchange status from both REST and WS servers (parallel) |

## Subscriptions (public)

| Example | Description |
|---------|-------------|
| [async-watch-ticker.py](async-watch-ticker.py) | Stream live prices |
| [async-watch-candles.py](async-watch-candles.py) | Stream candlestick updates |
| [async-watch-orderbook-diff.py](async-watch-orderbook-diff.py) | Stream orderbook diffs (default mode) |
| [async-watch-orderbook-snapshot.py](async-watch-orderbook-snapshot.py) | Stream full orderbook snapshots |
| [async-watch-orderbook-managed.py](async-watch-orderbook-managed.py) | Maintain a local book with checksum + sequence validation |
| [async-watch-trades.py](async-watch-trades.py) | Stream public trades |
| [async-watch-liquidations.py](async-watch-liquidations.py) | Stream liquidation events (requires concrete symbol) |
| [async-watch-ticker-on-error.py](async-watch-ticker-on-error.py) | Stream prices with error callback handling |

## Subscriptions (authenticated)

| Example | Description |
|---------|-------------|
| [async-watch-positions.py](async-watch-positions.py) | Stream position/balance updates |

## Trading (authenticated)

| Example | Description |
|---------|-------------|
| [async-create-order.py](async-create-order.py) | Place a limit order via WS |
| [async-create-limit-post-only-order.py](async-create-limit-post-only-order.py) | Place a post-only order via WS |
| [async-create-limit-gtd-order.py](async-create-limit-gtd-order.py) | Place a GTD order with expiry via WS |
| [async-create-limit-gtd-post-only-order.py](async-create-limit-gtd-post-only-order.py) | Place a GTD + post-only order (auto-expires in 30s) via WS |
| [async-market-order.py](async-market-order.py) | Place a market order via WS |
| [async-cancel-order.py](async-cancel-order.py) | Cancel an order via WS |
| [async-create-twap-order.py](async-create-twap-order.py) | Place a TWAP order via WS |
| [async-cancel-order-by-cloid.py](async-cancel-order-by-cloid.py) | Cancel an order by client order ID via WS |

## Account Management (authenticated)

| Example | Description |
|---------|-------------|
| [async-schedule-cancel.py](async-schedule-cancel.py) | Arm/disarm the dead-man switch via WS |
| [async-update-subaccount-name.py](async-update-subaccount-name.py) | Rename a subaccount via WS |

## Queries (authenticated)

| Example | Description |
|---------|-------------|
| [async-fetch-positions.py](async-fetch-positions.py) | Fetch positions via WS |
| [async-fetch-open-orders.py](async-fetch-open-orders.py) | Fetch open orders via WS |
| [async-fetch-trades-for-position.py](async-fetch-trades-for-position.py) | Fetch trade fills for a specific position via WS |
| [async-fetch-balance-updates.py](async-fetch-balance-updates.py) | Fetch balance updates (deposits, withdrawals, transfers) via WS |
| [async-fetch-withdrawable-amounts.py](async-fetch-withdrawable-amounts.py) | Fetch withdrawable collateral amounts per symbol via WS |
| [async-fetch-fee-rate.py](async-fetch-fee-rate.py) | Fetch current maker/taker fee rate and tier schedule via WS |

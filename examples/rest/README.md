# REST Examples

Synchronous examples using the REST API. Each file is a standalone script.

## Setup

```bash
pip install synthetix-sdk
```

Public examples need no configuration. Authenticated examples require a private key:

```bash
export PRIVATE_KEY="0x..."
```

All examples use **production** by default. To use a different environment, set overrides in `.env`:

```bash
REST_URL_OVERRIDE="https://papi.synthetix.io/v1"
WS_URL_OVERRIDE="wss://papi.synthetix.io/v1/ws"
```

## Market Data (public, no auth)

| Example | Description |
|---------|-------------|
| [fetch-markets.py](fetch-markets.py) | List all available perps markets |
| [fetch-ticker.py](fetch-ticker.py) | Current prices for all markets |
| [fetch-session-market-hours.py](fetch-session-market-hours.py) | Read the optional `onHours` field for session markets (e.g. WTI) |
| [fetch-mids.py](fetch-mids.py) | Mid prices for all markets |
| [fetch-candles.py](fetch-candles.py) | OHLC candlestick data |
| [fetch-orderbook.py](fetch-orderbook.py) | Orderbook snapshot (bids/asks) |
| [fetch-trades.py](fetch-trades.py) | Recent public trades |
| [fetch-funding-rate.py](fetch-funding-rate.py) | Current funding rate |
| [fetch-funding-rate-history.py](fetch-funding-rate-history.py) | Historical funding rates |
| [fetch-open-interest.py](fetch-open-interest.py) | Open interest across markets |
| [fetch-exchange-status.py](fetch-exchange-status.py) | Exchange operational status (REST + WS) |
| [fetch-tiers.py](fetch-tiers.py) | Fee/account tier configuration |

## Account Queries (authenticated)

| Example | Description |
|---------|-------------|
| [fetch-balance.py](fetch-balance.py) | Account balance and margin summary |
| [fetch-positions.py](fetch-positions.py) | Open positions |
| [fetch-position-history.py](fetch-position-history.py) | Closed position history |
| [fetch-position-history-filtered.py](fetch-position-history-filtered.py) | Position history filtered by symbol and time |
| [fetch-open-orders.py](fetch-open-orders.py) | Resting open orders |
| [fetch-order-history.py](fetch-order-history.py) | Historical orders |
| [fetch-my-trades.py](fetch-my-trades.py) | Trade fill history |
| [fetch-trades-for-position.py](fetch-trades-for-position.py) | Trade fills for a specific position |
| [fetch-fee-rate.py](fetch-fee-rate.py) | Current maker/taker fee rate and tier schedule |
| [fetch-funding-payments.py](fetch-funding-payments.py) | Funding payment history |
| [fetch-portfolio.py](fetch-portfolio.py) | Portfolio snapshots |
| [fetch-rate-limits.py](fetch-rate-limits.py) | Rate limit usage |
| [fetch-balance-updates.py](fetch-balance-updates.py) | Balance update history (deposits, withdrawals, fees, USDT notional) |
| [fetch-sub-accounts.py](fetch-sub-accounts.py) | List all subaccounts |
| [fetch-performance-history.py](fetch-performance-history.py) | Account performance history (PnL over time) |
| [fetch-withdrawable-amounts.py](fetch-withdrawable-amounts.py) | Withdrawable collateral amounts per symbol |

## Trading (authenticated)

| Example | Description |
|---------|-------------|
| [create-limit-gtc-order.py](create-limit-gtc-order.py) | Limit order (good-til-cancel) |
| [create-limit-ioc-order.py](create-limit-ioc-order.py) | Limit order (immediate-or-cancel) |
| [create-limit-post-only-order.py](create-limit-post-only-order.py) | Limit order (post-only) |
| [create-limit-gtd-order.py](create-limit-gtd-order.py) | Limit order (good-til-date with expiry) |
| [create-limit-gtd-post-only-order.py](create-limit-gtd-post-only-order.py) | Limit order (GTD + post-only, auto-expires in 30s) |
| [create-market-order.py](create-market-order.py) | Market order |
| [create-trigger-tp-order.py](create-trigger-tp-order.py) | Take-profit trigger order |
| [create-trigger-sl-order.py](create-trigger-sl-order.py) | Stop-loss trigger order |
| [create-twap-order.py](create-twap-order.py) | TWAP order (time-weighted execution) |
| [batch-orders-tpsl.py](batch-orders-tpsl.py) | Batch TP/SL pair on an open position |
| [batch-orders-twap.py](batch-orders-twap.py) | Batch TWAP order |
| [modify-order.py](modify-order.py) | Modify an existing order |
| [cancel-order.py](cancel-order.py) | Cancel a single order |
| [cancel-order-by-cloid.py](cancel-order-by-cloid.py) | Cancel an order by client order ID |
| [cancel-all-orders.py](cancel-all-orders.py) | Cancel all orders for a symbol |
| [schedule-cancel.py](schedule-cancel.py) | Configure the dead-man switch (schedule cancel) |

## Account Management (authenticated)

| Example | Description |
|---------|-------------|
| [create-subaccount.py](create-subaccount.py) | Create a new subaccount |
| [set-leverage.py](set-leverage.py) | Set leverage for a symbol |
| [transfer-collateral.py](transfer-collateral.py) | Transfer between subaccounts |

## Delegation (authenticated)

| Example | Description |
|---------|-------------|
| [add-delegated-signer.py](add-delegated-signer.py) | Add a delegated signer |
| [fetch-delegated-signers.py](fetch-delegated-signers.py) | List delegated signers |
| [remove-delegated-signer.py](remove-delegated-signer.py) | Remove a delegated signer |

## Polling Patterns

| Example | Description |
|---------|-------------|
| [poll-positions.py](poll-positions.py) | Continuously poll positions |
| [poll-balance.py](poll-balance.py) | Continuously poll balance |

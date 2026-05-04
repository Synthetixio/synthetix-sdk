---
name: synthetix
description: Help users get started with the Synthetix perps exchange — install the SDK, connect to the API, fetch market data, and place their first trade.
argument-hint: "[what you want to try, e.g. 'place a limit order' or 'stream prices']"
---

You are helping a user try out the Synthetix perpetual futures exchange using the `synthetix-sdk` Python package. Walk them through setup and usage interactively.

## Setup (run automatically before any code)

Before running any SDK code, **always** ensure the environment is ready. Do not ask — just do it:

1. Check if `.venv/bin/python3` exists in the project root. If yes, use it directly as the Python interpreter.
2. If no `.venv` exists, create one and install the SDK **plus `python-dotenv`** (a dev dependency needed for loading `.env` files):
   ```bash
   python3 -m venv .venv && .venv/bin/pip install -e . python-dotenv
   ```
3. **Always use `.venv/bin/python3`** to run scripts — never bare `python3` which is the system Python without deps.

```bash
# One-liner: ensure venv exists and SDK is installed, then run:
[ -f .venv/bin/python3 ] || (python3 -m venv .venv && .venv/bin/pip install -e . python-dotenv)
.venv/bin/python3 -c "import synthetix; print('SDK ready')"
```

Core dependencies (from `pyproject.toml`): `requests`, `eth-account`, `websockets`. Python 3.10+.
Also install: `python-dotenv` (dev dependency, needed for `.env` file loading in scripts).

All examples should use `from dotenv import load_dotenv; load_dotenv()` to pick up URL overrides from `.env`. If `REST_URL_OVERRIDE` / `WS_URL_OVERRIDE` are not set, the SDK defaults to production.

## What they need

- **Read-only** (market data, prices, orderbook): No private key needed.
- **Trading** (orders, positions, account management): Requires a private key set as `PRIVATE_KEY` env var.

## How to help

1. **Ask what they want to try** if `$ARGUMENTS` is empty. Present these categories:
   1. **Fetch market data** — markets, prices, orderbooks, recent trades (no wallet needed)
   2. **Stream live prices** — real-time WebSocket price feeds (no wallet needed)
   3. **Stream orderbook** — real-time bids/asks via WebSocket with snapshot, diff, or managed modes (no wallet needed)
   4. **Place a trade** — market, limit, stop-loss, and take-profit orders (needs private key)
   4. **Manage orders** — modify, cancel, or batch multiple orders (needs private key)
   5. **Check positions & P&L** — open positions, portfolio value, balance (needs private key)
   6. **Funding rates & fees** — current rates, historical funding, fee tiers (no wallet for rates, wallet for payment history)
   7. **Stream account updates** — real-time position and order fills via WebSocket (needs private key)
   8. **Manage risk** — set leverage, place TP/SL orders, monitor exposure (needs private key)
   9. **Account management** — create subaccounts, transfer collateral, delegate signers (needs private key)
   10. **Trade history & fills** — past orders, executed trades, P&L reconciliation (needs private key)
2. **Write a small standalone script** tailored to what they want. Use the examples in `examples/rest/` and `examples/ws/` as reference for correct patterns.
3. **Explain what the script does** briefly so they learn the SDK.
4. **Offer a next step** — e.g. "Want to try placing an order next?" or "Want to stream this via WebSocket instead?"

## Key patterns to follow

- REST methods are synchronous, WebSocket methods are async (`asyncio`).
- Client constructor: `Synthetix(private_key=os.environ["PRIVATE_KEY"], rest_url=os.environ.get("REST_URL_OVERRIDE"))` for trading, `Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"))` for read-only.
- Prices and quantities are human-readable decimal strings (e.g. `"0.01"`, `"2500.50"`), not wei.
- WebSocket subscriptions use `await snx.subscribe(channel, callback, on_error=on_error, **params)` and must run inside an async function.
- Always clean up WS connections with `await snx.unsubscribe(sub_id)` and `await snx.close()`.

## Available operations

**Market data (no auth):** `get_markets()`, `get_market_prices()`, `get_orderbook(symbol)`, `get_last_trades(symbol)`, `get_funding_rate(symbol)`, `get_open_interest()`, `get_candles(symbol, interval)`, `get_exchange_status()`

**Trading (auth required):** `market_order(symbol, side, quantity)`, `place_order(symbol, side, quantity, ...)`, `twap_order(symbol, side, quantity, duration_seconds, price=..., interval_seconds=0)`, `modify_order(order_id, ...)`, `cancel_order(order_id)`, `cancel_all_orders(symbol)`, `schedule_cancel(timeout_seconds)` (dead-man switch / auto-cancel)

**Account (auth required):** `get_positions()`, `get_open_orders()`, `get_order_history()`, `get_trades()`, `get_trades_for_position(position_id, limit=0, offset=0)`, `get_portfolio()`, `get_balance_updates()`, `get_fees()`, `get_withdrawable_amounts(symbols)`, `update_leverage(symbol, leverage)`, `create_subaccount(name)`, `transfer_collateral(amount, to_subaccount_id, symbol)`

**WS subscriptions:** All `subscribe()` calls accept an optional `on_error=callback` to handle exceptions without losing the subscription. Examples: `subscribe("marketPrices", callback, on_error=on_error, symbol=...)`, `subscribe("orderbook", callback, on_error=on_error, symbol=..., depth=50, format="snapshot")`, `subscribe("trades", callback, on_error=on_error, symbol=...)`, `subscribe("candles", callback, on_error=on_error, symbol=..., interval=...)`, `subscribe("subAccountUpdates", callback, on_error=on_error)`, `subscribe("liquidations", callback, on_error=on_error, symbol=...)` (requires a concrete symbol; `"ALL"` is not supported)

**WS trading (async):** All REST trading methods have `ws_` prefixed async equivalents — e.g. `await snx.ws_market_order(...)`, `await snx.ws_twap_order(...)`. Also: `await snx.ws_get_exchange_status()` queries both REST and WS servers in parallel. WS queries: `await snx.ws_get_trades_for_position(position_id, limit=0, offset=0)`, `await snx.ws_get_withdrawable_amounts(symbols)`.

## Market data details

When the user asks to fetch market data, these are the available endpoints (all public, no auth):

- `get_markets()` — all tradeable perps. Returns list of dicts with `symbol`, `baseAsset`, `quoteAsset`, `minOrderSize`.
- `get_market_prices()` — current prices for all markets. Returns dict keyed by symbol with `bestBid`, `bestAsk`, `markPrice`, `volume24h`. Compute mid price as `(bestBid + bestAsk) / 2`.
- `get_orderbook(symbol)` — REST snapshot. Returns `{"bids": [[price, size], ...], "asks": [[price, size], ...]}`. Bids are descending, asks ascending.
- `get_last_trades(symbol, limit=50)` — recent public trades. Returns list of dicts with `timestamp`, `side`, `price`, `quantity`.
- `get_open_interest()` — OI for all markets. Returns list of dicts with `symbol`, `openInterest`, `longOpenInterest`, `shortOpenInterest`, `timestamp` (ms).
- `get_candles(symbol, interval, start_time=0, end_time=0, limit=0)` — OHLC data. Response wraps candles: use `.get("candles", [])`. Each candle has `openTime`, `openPrice`, `highPrice`, `lowPrice`, `closePrice`, `volume`. Intervals: `"1m"`, `"5m"`, `"15m"`, `"30m"`, `"1h"`, `"4h"`, `"8h"`, `"12h"`, `"1d"`, `"3d"`, `"1w"`, `"1M"`, `"3M"`.

- `get_exchange_status()` — queries both REST and WS servers. Returns `{"rest": {...}, "ws": {...}}`, each with `accepting_orders` (bool), `exchange_status` (`"RUNNING"` or `"MAINTENANCE"`), `code` (present during maintenance), `message`, `timestamp_ms`. Async variant: `await ws_get_exchange_status()` (queries both in parallel).

See `examples/rest/fetch-markets.py`, `fetch-ticker.py`, `fetch-orderbook.py`, `fetch-trades.py`, `fetch-open-interest.py`, `fetch-candles.py`, `fetch-exchange-status.py`.

## Streaming live prices details

Subscribe to the `"marketPrices"` channel for real-time price updates:

```python
sub_id = await snx.subscribe("marketPrices", callback, on_error=on_error, symbol="ETH-USDT")
```

- Callback receives price data objects directly.
- No auth required.
- Always clean up: `await snx.unsubscribe(sub_id)` then `await snx.close()`.
- Use `try/finally` with `asyncio.sleep(duration)` to run for a set time.

**Error handling:** Pass `on_error=callback` to `subscribe()` to catch exceptions in your callback without losing the subscription. Error callback signature: `on_error(exc, data)`.

See `examples/ws/async-watch-ticker.py` and `async-watch-ticker-on-error.py`.

Also available: `"trades"` channel for real-time public trade feed, and `"candles"` channel with `timeframe` param (e.g. `"1h"`).

See `examples/ws/async-watch-trades.py`, `async-watch-candles.py`.

## Orderbook streaming details

When the user asks to stream the orderbook, explain the three modes and guide them toward managed mode for production use:

- **Snapshot mode** (`format="snapshot"`) — each message is the full book. Simple but more bandwidth.
- **Diff mode** (`format="diff"`) — first message is a snapshot, then only changed levels. Levels with `quantity: "0"` are removals.
- **Managed mode** (diff + local state + verification) — production-grade. Build a local book from diffs, validate with CRC32 checksums and sequence numbers.

### Managed orderbook pattern

Each diff message includes:
- `meseq` — message sequence number
- `prevMeseq` — expected previous sequence number (detect gaps)
- `checksum` — CRC32-IEEE hex string to verify local book integrity

**Checksum format:** concatenate `b{price}:{quantity}|` for each bid (descending), then `a{price}:{quantity}|` for each ask (ascending), truncated to the subscribed depth. CRC32 the resulting string and format as 8-char lowercase hex.

**On sequence gap** (`prevMeseq != book.meseq`): resubscribe to get a fresh snapshot.
**On checksum mismatch**: resubscribe to get a fresh snapshot.

See `examples/ws/async-watch-orderbook-managed.py` for the complete reference implementation with the `ManagedOrderbook` class.

### Orderbook subscription params
- `depth` — `10`, `50` (default), or `100`
- `updateFrequencyMs` — `50`, `100`, `250` (default), `500`, or `1000`. When `depth=100`, only `250`/`500`/`1000` are allowed.
- `format` — `"diff"` (default) or `"snapshot"`

## Trading details

### Order types

- **Market** — `market_order(symbol, side, quantity)` — fills immediately at best price. Simplest way to enter/exit.
- **Limit GTC** — `place_order(symbol, side, quantity, price=..., order_type="limitGtc")` — rests on the book until filled or canceled.
- **Limit IOC** — `place_order(..., order_type="limitIoc")` — fills what's available immediately, cancels remainder. No resting order.
- **Post-only** — `place_order(..., post_only=True)` — rests on the book as a maker order; rejected if it would immediately match (cross the spread). Works with both `limitGtc` and `limitGtd`.
- **Limit GTD** — `place_order(symbol, side, quantity, price=..., order_type="limitGtd", expires_at=unix_ts)` — rests on the book until filled, canceled, or expiry (10 s to 24 h from now).
- **TWAP** — `twap_order(symbol, side, quantity, duration_seconds=300, price=..., interval_seconds=0)` — time-weighted average price execution over a duration. Optional `price` as a limit ceiling/floor; optional `interval_seconds` overrides the server default slice interval (30 s). **Constraints:** minimum notional $10,000 USD (`quantity × markPrice`), duration 300 s (5 min) to 86,400 s (24 h).
- **Trigger Take-Profit** — `place_order(..., order_type="triggerTp", trigger_price=..., is_trigger_market=True, reduce_only=True)` — triggers market order when price reaches target. Use opposite side of position.
- **Trigger Stop-Loss** — `place_order(..., order_type="triggerSl", trigger_price=..., is_trigger_market=True, reduce_only=True)` — same as TP but triggers on adverse price.

### Batch orders

`place_orders(orders, grouping="na")` — submit multiple orders atomically. Orders are dicts with camelCase keys: `symbol`, `side`, `orderType`, `price`, `quantity`, `reduceOnly`, `closePosition`, `clientOrderId`, `triggerPrice`, `isTriggerMarket`.

### Client order IDs

Use `from synthetix.signing import generate_client_order_id` to create UUID-style client order IDs (cloids). Pass as `client_order_id` when placing, then cancel with `cancel_order_by_cloid(cloid)` — avoids needing to track venue-assigned order IDs.

### WebSocket trading

All REST trading methods have async `ws_` equivalents: `ws_place_order()`, `ws_market_order()`, `ws_cancel_order()`, `ws_cancel_order_by_cloid()`, `ws_cancel_all_orders()`, etc. Same params, just `await` them and call `await snx.close()` when done.

See `examples/rest/create-market-order.py`, `create-limit-gtc-order.py`, `create-limit-gtd-order.py`, `create-limit-ioc-order.py`, `create-limit-post-only-order.py`, `create-twap-order.py`, `create-trigger-tp-order.py`, `create-trigger-sl-order.py`, `batch-orders-tpsl.py`, `batch-orders-twap.py`. WS: `examples/ws/async-create-order.py`, `async-create-limit-post-only-order.py`, `async-create-limit-gtd-order.py`, `async-create-twap-order.py`, `async-market-order.py`.

## Order management details

- `modify_order(order_id, price=..., quantity=..., trigger_price=...)` — update price, quantity, and/or trigger price of a resting order. Order ID must be int.
- `cancel_order(order_id)` — cancel by venue order ID (int).
- `cancel_order_by_cloid(cloid)` — cancel by client order ID (string).
- `cancel_all_orders(symbol)` — cancel all resting orders for a symbol. Symbol list must be non-empty.

See `examples/rest/modify-order.py`, `cancel-order.py`, `cancel-order-by-cloid.py`, `cancel-all-orders.py`. WS: `examples/ws/async-cancel-order.py`, `async-cancel-order-by-cloid.py`.

## Dead-man switch (schedule cancel) details

Also known as: auto-cancel, deadman timer, heartbeat cancel.

`schedule_cancel(timeout_seconds)` arms a **server-side** timer. If the server does not receive another `schedule_cancel` call (heartbeat) within `timeout_seconds`, it automatically cancels **all** open orders on the subaccount. Pass `timeout_seconds=0` to disarm.

- **Arm:** `snx.schedule_cancel(timeout_seconds=300)` — orders auto-cancel after 5 min of silence.
- **Heartbeat:** call `schedule_cancel(timeout_seconds=300)` again periodically (before the timeout expires) to keep orders alive.
- **Disarm:** `snx.schedule_cancel(timeout_seconds=0)`.
- Returns `{"isActive": bool, "timeoutSeconds": int, "triggerTime": int|null, "message": str}`.
- WS equivalent: `await snx.ws_schedule_cancel(timeout_seconds)`.

Typical pattern: place orders, arm the dead-man switch, then send heartbeats in a loop. If the bot crashes, the server cancels everything.

See `examples/rest/schedule-cancel.py`, `examples/ws/async-schedule-cancel.py`.

## Positions & P&L details

- `get_positions()` — open positions. Each has `symbol`, `side` ("LONG"/"SHORT"), `quantity`, `entryPrice`, `unrealizedPnl`, `liquidationPrice` (optional, use `.get()`).
- `get_open_orders()` — resting orders. Each has `order` (`{"venueId": str}`), `symbol`, `side`, `type`, `price`, `quantity`. Optional `twapDetails` dict present on TWAP orders: `averagePrice`, `intervalMs`, `totalTrades`, `tradesFilled`, `totalFees`, `startedAtMs`, `totalDurationMs`.
- `get_order_history()` — filled, cancelled, rejected orders. Includes `filledQuantity`, `status`. Use `.get()` for optional fields.
- `get_sub_account()` — current subaccount balance. Returns `collaterals[]` (each with `symbol`, `quantity`, `withdrawable`) and `crossMarginSummary` with `accountValue`, `availableMargin`, `totalUnrealizedPnl`.
- `get_portfolio()` — time-series portfolio snapshots.

**Polling:** For live monitoring without WebSocket, use `get_positions()` or `get_sub_account()` in a `while True` loop with `time.sleep(5)`. See `examples/rest/poll-positions.py`, `poll-balance.py`.

**WS queries:** `await snx.ws_get_positions()`, `await snx.ws_get_open_orders()` — same data, async.

See `examples/rest/fetch-positions.py`, `fetch-open-orders.py`, `fetch-order-history.py`, `fetch-balance.py`, `fetch-portfolio.py`.

## Funding rates & fees details

**Public (no auth):**
- `get_funding_rate(symbol)` — current funding rate for a symbol.
- `get_funding_rate_history(symbol, start_time, end_time)` — historical rates. Times in milliseconds. Use `int(time.time() * 1000)` for current time, subtract `24 * 60 * 60 * 1000` for 24h window. Response wraps data in `fundingRates` key.

**Authenticated:**
- `get_funding_payments()` — your funding payment history. Returns `summary` (aggregated) and `fundingHistory[]` (individual payments with `timestamp`, `symbol`, `fundingRate`, `payment`).
- `get_fees()` — your fee tier structure and trading volume.

See `examples/rest/fetch-funding-rate.py`, `fetch-funding-rate-history.py`, `fetch-funding-payments.py`, `fetch-fees.py`.

## Streaming account updates details

Subscribe to `"subAccountUpdates"` for real-time position changes, order fills, and balance updates:

```python
sub_id = await snx.subscribe("subAccountUpdates", callback, on_error=on_error)
```

- **Requires auth** (private key).
- No params needed — subscribes to the current subaccount.
- Callback receives full subaccount state updates (positions, balances, margins).
- Pass `on_error=callback` to catch exceptions without losing the subscription (see "Streaming live prices" for error callback pattern).
- Use `pprint()` in callback to explore the data structure.

See `examples/ws/async-watch-positions.py`.

## Risk management details

- `update_leverage(symbol, leverage)` — set leverage for a symbol (e.g., `update_leverage("ETH-USDT", 10)`).
- **Take-profit/Stop-loss** — place trigger orders against existing positions. See "Trading details" above for `triggerTp`/`triggerSl` order types.
- **Reduce-only** — set `reduce_only=True` on TP/SL orders to prevent accidentally reversing a position.
- **Monitor exposure** — combine `get_positions()` with `get_sub_account()` to see margin usage, unrealized P&L, and liquidation prices.

See `examples/rest/set-leverage.py`, `create-trigger-tp-order.py`, `create-trigger-sl-order.py`.

## Account management details

- `create_subaccount(name)` — create a new subaccount with a display name.
- `get_sub_accounts()` — list all subaccounts with full data (positions, collaterals, margin summary per account).
- `transfer_collateral(amount, to_subaccount_id, symbol="USDC")` — move collateral between subaccounts. Requires at least 2 subaccounts. Convert subaccount ID to int.
- `withdraw_collateral(amount, symbol="USDC", destination=None)` — withdraw to wallet. Defaults to own wallet if destination is omitted.
- `get_withdrawable_amounts(symbols, subaccount_id=None)` — withdrawable collateral per symbol (e.g. `["USDT"]`; at least one required). Returns `{"items": [...], "totalWithdrawableUsdt": str}` where each item has `symbol`, `quantity` (total balance), `withdrawableAmount` (free to withdraw after margin/pending/fee), `pendingWithdraw`, `withdrawFee`. Async: `await snx.ws_get_withdrawable_amounts(symbols)`.

**Delegation:**
- `add_delegated_signer(delegate_address, permissions)` — delegate trading to another wallet. Permissions is a list (e.g., `["session"]`).
- `get_delegated_signers()` — view active delegations.
- `remove_delegated_signer(delegate_address)` — revoke delegation.

See `examples/rest/create-subaccount.py`, `transfer-collateral.py`, `fetch-sub-accounts.py`, `add-delegated-signer.py`, `fetch-delegated-signers.py`, `remove-delegated-signer.py`.

## Trade history & fills details

- `get_balance_updates(start_time=0, end_time=0, action_filter=None, limit=0, offset=0)` — deposits, withdrawals, and transfers. `action_filter` is a comma-separated list of `DEPOSIT`, `WITHDRAWAL`, `TRANSFER`. `limit` defaults to 50 (max 1000); `offset` defaults to 0 (max 10000). Returns `{"balanceUpdates": [...]}`, each with `id`, `action` (DEPOSIT/WITHDRAWAL/TRANSFER), `status` (success/completed/pending), `amount`, `grossAmount` (amount + fee), `fee`, `collateral`, `timestamp`. TRANSFER entries also include `fromSubAccountId`/`toSubAccountId`; deposits/withdrawals include `destinationAddress`/`txHash`.
- `get_trades(order_id=None)` — your executed fills. Optionally filter by venue order ID. Response wraps data: use `.get("trades", [])`. Also includes `hasMore` (bool) and `total` (int) for pagination. Each trade has `timestamp`, `symbol`, `side`, `price`, `quantity`, `fee`, `realizedPnl` (optional).
- `get_trades_for_position(position_id, limit=0, offset=0)` — fills for a specific position. Returns `{"trades": [...], "hasMore": bool}`. Each trade has `tradeId`, `symbol`, `orderType`, `side`, `price`, `quantity`, `realizedPnl`, `fee`, `feeRate`, `timestamp`, `maker`, `reduceOnly`, `markPrice`, `entryPrice`, `direction`, `postOnly`. Async: `await snx.ws_get_trades_for_position(position_id)`.
- `get_order_history(start_time=0, end_time=0, limit=0)` — historical orders (filled, cancelled, rejected). Pass `start_time`/`end_time` in ms (max 7-day window). Each has `order` (`{"venueId": str}`), `symbol`, `side`, `type`, `price`, `filledQuantity`, `status`. Optional fields: `cancelReason`, `triggerPrice` (str, stop/trigger price for TP/SL orders), `triggerPriceType` (`"last"` or `"mark"`), `tpOrder`/`slOrder` (dict `{"venueId": str}` linking paired TP/SL orders).
- `get_position_history()` — closed positions. Response wraps in `positions` key, includes `hasMore` for pagination.
- `get_position_history(symbol=..., start_time=..., end_time=..., limit=..., offset=0)` — filtered by symbol and time range. Times in milliseconds (e.g., 7 days = `7 * 24 * 3_600_000`). Use `offset` for pagination.

See `examples/rest/fetch-balance-updates.py`, `fetch-my-trades.py`, `fetch-order-history.py`, `fetch-position-history.py`, `fetch-position-history-filtered.py`, `examples/ws/async-fetch-balance-updates.py`, `async-fetch-trades-for-position.py`.

## Important

- Keep scripts minimal and focused on one thing at a time.
- Reference the `examples/` directory if the user wants more complete examples.

# REST API

Synchronous REST client for Synthetix Perps.

- **`POST /info`** — public market data (no auth required)
- **`GET /exchange/status`** — exchange operational status (no auth required)
- **`POST /trade`** — authenticated account and trading actions (requires EIP-712 signature)

## API (Base Client)

`synthetix.rest.api.API`

Low-level HTTP client. Handles JSON serialization, error handling, and response envelope unwrapping.

All responses are wrapped in `{"status": "ok", "response": <data>}` — the client automatically unwraps this and returns the inner `response` value.

### Errors

| Exception | Trigger |
|---|---|
| `ClientError` | 4xx HTTP status |
| `ServerError` | 5xx HTTP status or non-JSON response |
| `SynthetixAPIError` | 200 with error payload (`{"status": "error", ...}`) |

---

## MarketAPI (Public)

`synthetix.rest.market.MarketAPI`

Most methods hit `POST /info`. No authentication required.

### `get_markets()`

Get all available markets and their configurations.

**Inputs:** None

**Output:** `List[Dict]` — each dict contains:
- `symbol` — e.g. `"BTC-USDT"`
- `description`, `baseAsset`, `quoteAsset`
- `isOpen`, `isCloseOnly`
- `priceIncrement`, `minOrderSize`, `orderSizeIncrement`, `contractSize`
- `maxMarketOrderSize`, `maxLimitOrderSize`, `minNotionalValue`
- `maintenanceMarginTiers`

---

### `get_market_prices()`

Get current prices for all markets.

**Inputs:** None

**Output:** `Dict[str, Dict]` — keyed by symbol (e.g. `"BTC-USDT"`), each containing:
- `symbol`, `bestBid`, `bestAsk`, `markPrice`, `indexPrice`
- `lastPrice`, `prevDayPrice`
- `volume24h`, `quoteVolume24h`
- `fundingRate`, `openInterest`, `timestamp`

---

### `get_orderbook(symbol)`

Get orderbook snapshot for a symbol.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `symbol` | `str` | Market symbol (e.g. `"ETH-USDT"`) |

**Output:** `Dict`
```json
{"bids": [["price", "size"], ...], "asks": [["price", "size"], ...]}
```

---

### `get_last_trades(symbol, limit=50)`

Get recent trades for a symbol.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `symbol` | `str` | — | Market symbol |
| `limit` | `int` | `50` | Max number of trades |

**Output:** `List[Dict]` — each trade contains:
- `tradeId`, `symbol`, `side`, `price`, `quantity`, `timestamp`, `isMaker`

---

### `get_funding_rate(symbol)`

Get current funding rate for a symbol.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `symbol` | `str` | Market symbol |

**Output:** `Dict`
- `symbol`, `estimatedFundingRate`, `lastSettlementRate`
- `lastSettlementTime`, `nextFundingTime`, `fundingInterval`

---

### `get_funding_rate_history(symbol, start_time, end_time)`

Get historical funding rates over a time range.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `symbol` | `str` | Market symbol |
| `start_time` | `int` | Start timestamp in milliseconds |
| `end_time` | `int` | End timestamp in milliseconds |

**Output:** `Dict`
```json
{"symbol": "ETH-USDT", "fundingRates": [{"fundingRate": "...", "fundingTime": "...", "appliedAt": "..."}]}
```

---

### `get_open_interest()`

Get open interest for all markets.

**Inputs:** None

**Output:** `List[Dict]` — each containing:
- `symbol`, `openInterest`, `longOpenInterest`, `shortOpenInterest`, `timestamp`

---

### `get_exchange_status_rest()` / `get_exchange_status_ws()`

Get exchange operational status via `GET /exchange/status` from the REST or WebSocket server respectively.

**Inputs:** None

**Output:** `Dict`
- `accepting_orders` — `bool`, whether the exchange is accepting new orders
- `exchange_status` — `"RUNNING"` or `"MAINTENANCE"`
- `code` — present during maintenance (e.g. `"SERVICE_DRAINING"`)
- `message` — human-readable status message
- `timestamp_ms` — server timestamp in milliseconds

> **Note:** The top-level `Synthetix.get_exchange_status()` queries both servers and returns `{"rest": {...}, "ws": {...}}`.

---

### `get_sub_account_ids(wallet_address=None)`

Get subaccount IDs for a wallet address.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `wallet_address` | `str` | `None` | Wallet address to look up (defaults to connected wallet if `private_key` was provided) |

**Output:** `List[int]` — list of integer subaccount IDs

---

## AccountAPI (Authenticated)

`synthetix.rest.account.AccountAPI`

All methods hit `POST /trade`. Every request is EIP-712 signed.

### Order Management

#### `place_order(symbol, side, quantity, price="", order_type="limitGtc", ...)`

Place a single order (convenience wrapper). Automatically selects the correct grouping.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `symbol` | `str` | — | Market symbol (e.g. `"BTC-USDT"`) |
| `side` | `str` | — | `"buy"` or `"sell"` |
| `quantity` | `str` | — | Order quantity |
| `price` | `str` | `""` | Limit price (empty for market orders) |
| `order_type` | `str` | `"limitGtc"` | `"limitGtc"`, `"limitIoc"`, `"limitGtd"`, `"market"`, `"triggerTp"`, `"triggerSl"` |
| `reduce_only` | `bool` | `False` | Reduce-only flag |
| `client_order_id` | `str` | `""` | Optional client order ID |
| `close_position` | `bool` | `False` | Close entire position |
| `trigger_price` | `str` | `""` | Trigger price (for trigger orders) |
| `is_trigger_market` | `bool` | `False` | Execute as market when triggered |
| `expires_at` | `int` | `0` | Unix timestamp for `limitGtd` orders (10 s–24 h in the future) |
| `post_only` | `bool` | `False` | Reject if order would cross the spread. Works with `limitGtc` and `limitGtd`. |

**Output:** `Dict` — `{"statuses": [{"resting": {"order": {"venueId": "...", "clientId": "..."}, ...}}]}`

The `order` object always contains `venueId`. When a `client_order_id` is provided, `clientId` is also included.

---

#### `market_order(symbol, side, quantity)`

Place a market order. Fills at best available price immediately.

**Output:** `Dict` — `{"statuses": [{"filled": {"order": {"venueId": "..."}, "avgPrice": "...", "totalSize": "..."}}]}`

---

#### `twap_order(symbol, side, quantity, duration_seconds, price="")`

Place a TWAP (time-weighted average price) order.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `symbol` | `str` | — | Market symbol |
| `side` | `str` | — | `"buy"` or `"sell"` |
| `quantity` | `str` | — | Total order quantity |
| `duration_seconds` | `int` | — | Execution window (300–86,400 s) |
| `price` | `str` | `""` | Optional limit price ceiling/floor |

**TWAP constraints:** minimum notional $10,000 USD (`quantity × markPrice`), duration 300 s (5 min) to 86,400 s (24 h).

**Output:** `Dict` — `{"statuses": [{"resting": {"id": "..."}}]}`

---

#### `place_orders(orders, grouping="na")`

Place one or more orders in a single request. For single orders prefer `place_order()`, `market_order()`, or `twap_order()`.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `orders` | `List[Dict]` | — | List of order dicts |
| `grouping` | `str` | `"na"` | Order grouping (`"na"`, `"positionTpsl"`, `"twap"`) |

Each order dict:
| Field | Type | Description |
|---|---|---|
| `symbol` | `str` | Market symbol |
| `side` | `str` | `"buy"` or `"sell"` |
| `orderType` | `str` | `"limitGtc"`, `"limitIoc"`, `"limitGtd"`, `"market"`, `"triggerTp"`, `"triggerSl"`, `"twap"` |
| `price` | `str` | Limit price (empty for market orders; optional for `twap`) |
| `quantity` | `str` | Order quantity |
| `reduceOnly` | `bool` | Reduce-only flag |
| `clientOrderId` | `str` | Optional client order ID |
| `closePosition` | `bool` | Close entire position |
| `triggerPrice` | `str` | Trigger price (for trigger orders) |
| `isTriggerMarket` | `bool` | Execute as market when triggered |
| `expiresAt` | `int` | Unix timestamp (for `limitGtd` only; must be 10 s–24 h in the future) |
| `durationSeconds` | `int` | TWAP duration in seconds (required for `twap` orders; min 300, max 86,400) |

**`grouping` values:**
- `"na"` — default, no grouping
- `"positionTpsl"` — TP/SL pair attached to a position
- `"twap"` — routes to dedicated TWAP handler; payload must contain exactly one `twap` order

**TWAP constraints:** minimum notional value of **$10,000 USD** (`quantity × markPrice`), duration between **300 s** (5 min) and **86,400 s** (24 h).

**Output:** `Dict` — `{"statuses": [{"resting": {"order": {"venueId": "..."}, ...}}]}`

---

#### `modify_order(order_id, price=None, quantity=None, trigger_price=None)`

Modify an existing order.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `order_id` | `int` | — | Order ID to modify |
| `price` | `str` | `None` | New price |
| `quantity` | `str` | `None` | New quantity |
| `trigger_price` | `str` | `None` | New trigger price |

**Output:** `Dict` — `{"statuses": [{"status": "ok"}]}`

---

#### `cancel_orders(order_ids)`

Cancel orders by ID.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `order_ids` | `List[int]` | List of order IDs to cancel |

**Output:** `Dict` — `{"statuses": [{"status": "ok"}]}`

---

#### `cancel_orders_by_cloid(client_order_ids)`

Cancel orders by client order ID.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `client_order_ids` | `List[str]` | List of client order IDs |

**Output:** `Dict` — `{"statuses": [{"status": "ok"}]}`

---

#### `cancel_all_orders(symbol)`

Cancel all open orders for a symbol.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `symbol` | `str` | Market symbol |

**Output:** `Dict` — `{"statuses": [{"status": "ok"}]}`

---

### Account Queries

#### `get_sub_accounts()`

List all subaccounts.

**Inputs:** None

**Output:** `Dict`
```json
{"subAccounts": [{"subAccountId": "...", "masterAccountId": "...", "subAccountName": "...", "collaterals": [...], "crossMarginSummary": {...}, "positions": [...], "marketPreferences": {...}, "feeRates": {...}, "delegatedSigners": [...]}]}
```

---

#### `get_sub_account(subaccount_id=None)`

Get detailed info for a single subaccount.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
- `subAccountId`, `masterAccountId`, `subAccountName`
- `collaterals` — `[{"symbol", "quantity", "withdrawable", "pendingWithdraw"}]`
- `crossMarginSummary` — `{"accountValue", "availableMargin", "totalUnrealizedPnl", "maintenanceMargin", "initialMargin", "withdrawable", "adjustedAccountValue"}`
- `positions` — list of position dicts
- `marketPreferences` — `{"leverages": {...}}`
- `feeRates` — `{"makerFeeRate", "takerFeeRate", "tierName"}`

---

#### `get_positions(subaccount_id=None)`

Get open positions.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `List[Dict]` — each position contains:
- `positionId`, `subAccountId`, `symbol`, `side`, `entryPrice`, `quantity`
- `unrealizedPnl`, `usedMargin`, `maintenanceMargin`, `liquidationPrice`
- `status`, `netFunding`, `updatedAt`, `createdAt`

---

#### `get_open_orders(subaccount_id=None)`

Get open orders.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `List[Dict]` — each order contains:
- `order` (`{"venueId": str}`), `symbol`, `side`, `type`, `quantity`, `price`
- `triggerPrice`, `triggerPriceType`, `timeInForce`
- `reduceOnly`, `postOnly`, `createdTime`, `updatedTime`
- `filledQuantity`, `closePosition`
- `expiresAt` _(optional)_ — ISO timestamp for GTD order expiry

---

#### `get_order_history(subaccount_id=None)`

Get historical orders (filled, canceled, etc.).

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `List[Dict]` — same fields as `get_open_orders()` plus status information and:
- `expiresAt` _(optional)_ — ISO timestamp for GTD order expiry
- `cancelReason` _(optional)_ — human-readable string explaining why the order was canceled

---

#### `get_trades(order_id=None, subaccount_id=None)`

Get trade fill history.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `order_id` | `str` | `None` | Venue order ID to filter trades for a specific order |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
```json
{"trades": [...], "hasMore": true, "total": 42}
```
Each trade contains:
- `tradeId`, `order` (`{"venueId": str}`), `symbol`, `side`, `price`, `quantity`
- `realizedPnl`, `fee`, `feeRate`, `timestamp`
- `maker`, `reduceOnly`, `markPrice`, `entryPrice`
- `triggeredByLiquidation`, `direction`, `postOnly`

---

#### `get_trades_for_position(position_id, limit=0, offset=0, subaccount_id=None)`

Get trade fills for a specific position.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `position_id` | `str` | required | Position ID to fetch trades for |
| `limit` | `int` | `0` (server default 100, max 1000) | Max number of trades to return |
| `offset` | `int` | `0` | Pagination offset |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
```json
{"trades": [...], "hasMore": false}
```
Each trade contains:
- `tradeId`, `order` (`{"venueId": str}`), `symbol`, `orderType`, `side`, `price`, `quantity`
- `realizedPnl`, `fee`, `feeRate`, `timestamp`
- `maker`, `reduceOnly`, `markPrice`, `entryPrice`
- `triggeredByLiquidation`, `direction`, `postOnly`

---

#### `get_portfolio(subaccount_id=None)`

Get portfolio snapshots.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `List[Dict]` — each snapshot has `assets` (per-asset breakdowns) and `timestamp`.

---

#### `get_balance_updates(start_time=0, end_time=0, subaccount_id=None)`

Get balance change history.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `start_time` | `int` | `0` | Start timestamp in ms (Synthetix defaults to 7 days ago; max window 365 days) |
| `end_time` | `int` | `0` | End timestamp in ms (Synthetix defaults to now) |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
```json
{"balanceUpdates": [{"id": "...", "subAccountId": "...", "action": "...", "status": "...", "amount": "...", "collateral": "...", "timestamp": "...", "destinationAddress": "...", "txHash": "..."}]}
```

---

#### `get_transfers(subaccount_id=None)`

Get collateral transfer history.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
```json
{"transfers": [{"transferId": "...", "from": "...", "to": "...", "symbol": "...", "amount": "...", "transferType": "...", "status": "...", "timestamp": "..."}], "total": 5}
```

---

#### `get_performance_history(period=None, subaccount_id=None)`

Get account performance history for a given period.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `period` | `str` | `None` | Period: `"day"`, `"week"`, `"month"`, `"year"` (default `"day"`) |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
- `subAccountId` — string ID
- `period` — the requested period string
- `performanceHistory` — `{"history": [{"sampledAt": int, "accountValue": str, "pnl": str}], "volume": str}`

---

### Account Management

#### `create_subaccount(name=None)`

Create a new subaccount under the current master.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | `None` | Subaccount name |

**Output:** `Dict` — `{"subAccountId": "...", "subAccountName": "..."}`

---

#### `update_sub_account_name(name, subaccount_id=None)`

Rename a subaccount.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — | New name |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict` — `{"subAccountId": "...", "name": "..."}`

---

#### `update_leverage(symbol, leverage, subaccount_id=None)`

Set leverage for a symbol.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `symbol` | `str` | — | Market symbol |
| `leverage` | `int` | — | Leverage multiplier |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict` — `{"symbol": "...", "newLeverage": "...", "previousLeverage": "..."}`

---

#### `withdraw_collateral(amount, symbol="USDC", destination=None, subaccount_id=None)`

Withdraw collateral to a destination address.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `amount` | `str` | — | Amount to withdraw |
| `symbol` | `str` | `"USDC"` | Collateral symbol |
| `destination` | `str` | `None` | Destination address (defaults to own wallet) |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict` — `{"requestId": "...", "symbol": "...", "amount": "...", "destination": "..."}`

---

#### `transfer_collateral(amount, to_subaccount_id, symbol="USDC", subaccount_id=None)`

Transfer collateral between subaccounts.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `amount` | `str` | — | Amount to transfer |
| `to_subaccount_id` | `int` | — | Destination subaccount ID |
| `symbol` | `str` | `"USDC"` | Collateral symbol |
| `subaccount_id` | `int` | `None` | Source subaccount ID (defaults to active) |

**Output:** `Dict` — `{"status": "success", "symbol": "...", "amount": "...", "to": {"subAccountId": "..."}, "transferId": "..."}`

---

### Fees & Funding

#### `get_fees(subaccount_id=None)`

Get fee tier structure and current trading volume.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
```json
{"feeTiers": [{"symbol": "...", "feeRate": "..."}], "userDailyVolume": "...", "userFeeTier": {"symbol": "...", "feeRate": "..."}}
```

---

#### `get_funding_payments(subaccount_id=None)`

Get funding payment history with summary.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
```json
{"summary": {"totalFundingReceived": "...", "totalFundingPaid": "...", "netFunding": "...", "totalPayments": "...", "averagePaymentSize": "..."}, "fundingHistory": [...]}
```
Each funding history entry contains:
- `paymentId`, `symbol`, `positionSize`, `fundingRate`, `payment`, `timestamp`

---

#### `get_rate_limits(subaccount_id=None)`

Get current rate limit usage.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict` — `{"requestsUsed": 5, "requestsCap": 100}`

---

### Delegation

#### `add_delegated_signer(delegate_address, permissions, subaccount_id=None)`

Add a delegated signer.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `delegate_address` | `str` | — | Wallet address to delegate to |
| `permissions` | `List[str]` | — | Permissions (e.g. `["session"]`) |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict` — `{"walletAddress": "...", "permissions": [...]}`

---

#### `get_delegated_signers(subaccount_id=None)`

Get list of delegated signers.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
```json
{"delegatedSigners": [{"subAccountId": "...", "walletAddress": "...", "permissions": [...], "expiresAt": "..."}]}
```

---

#### `remove_delegated_signer(delegate_address, subaccount_id=None)`

Remove a delegated signer.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `delegate_address` | `str` | — | Wallet address to remove |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict` — `{"walletAddress": "..."}`

---

#### `remove_all_delegated_signers(subaccount_id=None)`

Remove all delegated signers.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`

---

#### `get_delegations_for_delegate(subaccount_id=None)`

Get delegations from the perspective of the delegate.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict` — `{"delegatedAccounts": [...]}`

---

### Dead-Man Switch

#### `schedule_cancel(timeout_seconds, subaccount_id=None)`

Configure the dead-man switch. When active, all open orders are automatically canceled if the server receives no heartbeat within the timeout. Pass `0` to disable.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `timeout_seconds` | `int` | — | Inactivity timeout in seconds; `0` disables the switch |
| `subaccount_id` | `int` | `None` | Subaccount ID (defaults to active) |

**Output:** `Dict`
- `isActive` — `bool` — whether the dead-man switch is now armed
- `message` — human-readable status message
- `timeoutSeconds` — configured timeout value
- `triggerTime` — millisecond timestamp when orders will be canceled, or `null`

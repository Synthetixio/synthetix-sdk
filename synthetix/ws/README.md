# WebSocket API

Async WebSocket client for Synthetix Perps. All methods are `async` and require an event loop.

The SDK manages two separate WebSocket connections:

- **`/ws/info`** — public market data (no auth required)
- **`/ws/trade`** — authenticated account updates, trading actions, and account queries

Connections are lazy — they are only created when you first call a WS method.

## WebSocketManager

`synthetix.ws.manager.WebSocketManager`

### Connection Behavior

- **Auto-reconnect** — if the connection drops, the SDK reconnects with jitter (5-10s delay) and replays all active subscriptions.
- **Auto-auth on reconnect** — private connections re-authenticate before replaying subscriptions.
- **Callbacks** — sync and async callbacks are both supported. Dispatched by channel type, not by symbol — filter by symbol in your callback if needed.
- **Ping keepalive** — application-level pings sent every 30s (configurable). If the server doesn't respond within the timeout, the connection is closed and reconnected.

---

## Subscriptions

### `await subscribe(channel, callback, on_error=None, **kwargs)`

Subscribe to a WebSocket channel.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `channel` | `str` | Channel name (see [Channels](#channels) below) |
| `callback` | `Callable` | Sync or async function called with each push message |
| `on_error` | `Callable` | Optional `(exception, message_data)` handler invoked when `callback` raises. If not provided, errors are logged and the subscription continues silently. |
| `**kwargs` | | Channel-specific params (e.g. `symbol="ETH-USDT"`) |

**Output:** `int` — subscription ID (use to unsubscribe later)

**Example:**
```python
sub_id = await snx.subscribe("marketPrices", lambda d: print(d), symbol="ETH-USDT")

# With error handling
def on_error(exc, data):
    print(f"Callback failed: {exc}")

sub_id = await snx.subscribe("marketPrices", my_callback, on_error=on_error, symbol="ETH-USDT")
```

---

### `await unsubscribe(subscription_id)`

Unsubscribe from a channel.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `subscription_id` | `int` | ID returned by `subscribe()` |

**Output:** `None`

---

### `await close()`

Close all WebSocket connections.

**Inputs:** None

**Output:** `None`

---

## Channels

| Channel | Auth | Params | Description |
|---|---|---|---|
| `candles` | No | `symbol`, `timeframe` | Candlestick updates |
| `liquidations` | No | `symbol` | Liquidation events (see fields below) |
| `marketPrices` | No | `symbol` | Mark/index price updates |
| `orderbook` | No | `symbol` | Orderbook depth updates |
| `trades` | No | `symbol` | Recent trade feed |
| `subAccountUpdates` | Yes | `sub_account_id` (auto-filled) | Position, order, and balance changes |

#### `liquidations` channel push message fields

| Field | Type | Description |
|---|---|---|
| `eventId` | `str` | Trade ID string identifying the liquidation event |
| `market` | `str` | Market symbol (e.g. `"ETH-USDT"`) |
| `tsMs` | `int` | Unix timestamp in milliseconds |
| `side` | `str` | `"buy"` or `"sell"` |
| `size` | `str` | Liquidated quantity as a decimal string |
| `liquidationPrice` | `str` | Execution price as a decimal string |

The `subAccountUpdates` channel automatically uses your active `subaccount_id`. Pass `sub_account_id` explicitly to override.

---

## Trading via WebSocket

Every authenticated REST method has an async WebSocket equivalent (`ws_` prefix) on the `Synthetix` client. These send signed `method: "post"` messages over the `/ws/trade` connection for lower latency.

### `await ws_place_order(symbol, side, quantity, price="", order_type="limitGtc", ...)`

Place a single order.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `symbol` | `str` | — | Market symbol |
| `side` | `str` | — | `"buy"` or `"sell"` |
| `quantity` | `str` | — | Order quantity |
| `price` | `str` | `""` | Limit price (empty for market) |
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

### `await ws_market_order(symbol, side, quantity)`

Place a market order.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `symbol` | `str` | Market symbol |
| `side` | `str` | `"buy"` or `"sell"` |
| `quantity` | `str` | Order quantity |

**Output:** `Dict` — `{"statuses": [{"filled": {"order": {"venueId": "..."}, "avgPrice": "...", "totalSize": "..."}}]}`

---

### `await ws_twap_order(symbol, side, quantity, duration_seconds, price="", interval_seconds=0)`

Place a TWAP (time-weighted average price) order.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `symbol` | `str` | — | Market symbol |
| `side` | `str` | — | `"buy"` or `"sell"` |
| `quantity` | `str` | — | Total order quantity |
| `duration_seconds` | `int` | — | Execution window (300–86,400 s) |
| `price` | `str` | `""` | Optional limit price ceiling/floor |
| `interval_seconds` | `int` | `0` | Optional slice interval in seconds (server default 30) |

**TWAP constraints:** minimum notional $10,000 USD (`quantity × markPrice`), duration 300 s (5 min) to 86,400 s (24 h).

**Output:** `Dict` — `{"statuses": [{"resting": {"id": "..."}}]}`

---

### `await ws_place_orders(orders, grouping="na")`

Place one or more orders.

**Inputs:**
| Param | Type | Default | Description |
|---|---|---|---|
| `orders` | `List[Dict]` | — | List of order dicts (same format as REST `place_orders`) |
| `grouping` | `str` | `"na"` | Order grouping |

**Output:** `Dict` — `{"statuses": [...]}`

---

### `await ws_modify_order(order_id, price=None, quantity=None, trigger_price=None)`

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

### `await ws_cancel_order(order_id)`

Cancel a single order.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `order_id` | `int` | Order ID to cancel |

**Output:** `Dict` — `{"statuses": [{"status": "ok"}]}`

---

### `await ws_cancel_orders(order_ids)`

Cancel multiple orders by ID.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `order_ids` | `List[int]` | List of order IDs |

**Output:** `Dict` — `{"statuses": [...]}`

---

### `await ws_cancel_order_by_cloid(client_order_id)`

Cancel a single order by client order ID.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `client_order_id` | `str` | Client order ID |

**Output:** `Dict` — `{"statuses": [{"status": "ok"}]}`

---

### `await ws_cancel_orders_by_cloid(client_order_ids)`

Cancel multiple orders by client order ID.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `client_order_ids` | `List[str]` | List of client order IDs |

**Output:** `Dict` — `{"statuses": [...]}`

---

### `await ws_cancel_all_orders(symbol)`

Cancel all open orders for a symbol.

**Inputs:**
| Param | Type | Description |
|---|---|---|
| `symbol` | `str` | Market symbol |

**Output:** `Dict` — `{"statuses": [...]}`

---

## Exchange Status (async, no auth)

### `await ws_get_exchange_status()`

Get exchange operational status from both REST and WebSocket servers in parallel.

**Inputs:** None

**Output:** `Dict` with keys `"rest"` and `"ws"`, each containing:
- `accepting_orders` — `bool`
- `exchange_status` — `"RUNNING"` or `"MAINTENANCE"`
- `code` — present during maintenance (e.g. `"SERVICE_DRAINING"`)
- `message` — human-readable status
- `timestamp_ms` — server timestamp in milliseconds

> This is an HTTP-based check (no WebSocket upgrade required). Both servers are queried concurrently via `asyncio.gather`.

---

## Account Queries via WebSocket

All account query methods mirror their REST equivalents. Inputs and outputs are identical — see [REST Account Queries](../rest/README.md#account-queries) for details.

| Method | Description |
|---|---|
| `await ws_get_positions(subaccount_id=None)` | Open positions |
| `await ws_get_open_orders(subaccount_id=None)` | Open orders |
| `await ws_get_sub_accounts()` | List all subaccounts |
| `await ws_get_sub_account(subaccount_id=None)` | Subaccount details |
| `await ws_get_order_history(start_time=0, end_time=0, limit=0, subaccount_id=None)` | Historical orders (max 7-day window) |
| `await ws_get_trades(order_id=None, subaccount_id=None)` | Trade history |
| `await ws_get_trades_for_position(position_id, limit=0, offset=0, subaccount_id=None)` | Trade fills for a specific position |
| `await ws_get_portfolio(subaccount_id=None)` | Portfolio summary |
| `await ws_get_balance_updates(start_time=0, end_time=0, action_filter=None, limit=0, offset=0, subaccount_id=None)` | Balance change history |
| `await ws_get_transfers(subaccount_id=None)` | Transfer history |
| `await ws_get_fees(subaccount_id=None)` | Fee structure |
| `await ws_get_funding_payments(subaccount_id=None)` | Funding payment history |
| `await ws_get_rate_limits(subaccount_id=None)` | Rate limit status |
| `await ws_get_delegated_signers(subaccount_id=None)` | Delegated signers |
| `await ws_get_delegations_for_delegate(subaccount_id=None)` | Delegations for delegate |
| `await ws_get_withdrawable_amounts(symbols, subaccount_id=None)` | Withdrawable collateral amounts per symbol |

---

## Account Management via WebSocket

All account management methods mirror their REST equivalents. Inputs and outputs are identical — see [REST Account Management](../rest/README.md#account-management) for details.

| Method | Description |
|---|---|
| `await ws_create_subaccount(name=None)` | Create a new subaccount |
| `await ws_update_leverage(symbol, leverage, subaccount_id=None)` | Set leverage |
| `await ws_update_sub_account_name(name, subaccount_id=None)` | Rename a subaccount |
| `await ws_schedule_cancel(timeout_seconds, subaccount_id=None)` | Configure the dead-man switch |
| `await ws_withdraw_collateral(amount, symbol="USDC", destination=None, subaccount_id=None)` | Withdraw collateral |
| `await ws_transfer_collateral(amount, to_subaccount_id, symbol="USDC", subaccount_id=None)` | Transfer between subaccounts |
| `await ws_add_delegated_signer(delegate_address, permissions, subaccount_id=None)` | Add delegated signer |
| `await ws_remove_delegated_signer(delegate_address, subaccount_id=None)` | Remove delegated signer |
| `await ws_remove_all_delegated_signers(subaccount_id=None)` | Remove all delegated signers |

"""
Async WebSocket manager.
State machine: DISCONNECTED → CONNECTED → AUTHENTICATED.
Reconnects automatically with jitter.
"""

import asyncio
import enum
import json
import logging
import random
from collections import defaultdict
from typing import Any, Callable, Dict, Optional

import websockets

from synthetix.signing import Signer
from synthetix.ws.streams import PRIVATE_CHANNELS

logger = logging.getLogger(__name__)


class _ConnState(enum.Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"


class _Connection:
    """Single async WebSocket connection with auto-reconnect and ping keepalive."""

    def __init__(
        self,
        url: str,
        on_message: Callable,
        signer: Optional[Signer] = None,
        subaccount_id: Optional[int] = None,
        needs_auth: bool = False,
        auto_reconnect: bool = True,
        ping_interval: int = 30,
        ping_timeout: int = 30,
    ) -> None:
        self.url = url
        self._on_message = on_message
        self._signer = signer
        self._subaccount_id = subaccount_id
        self._needs_auth = needs_auth
        self._auto_reconnect = auto_reconnect
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout

        self._state = _ConnState.DISCONNECTED
        self._ws = None
        self._task: Optional[asyncio.Task] = None
        self._stop = False
        self._auth_event = asyncio.Event()
        self._request_id = 0
        self._pending: Dict[str, asyncio.Future] = {}

        # Track subscriptions for replay on reconnect: sub_id -> params
        self._subscriptions: Dict[int, Dict[str, Any]] = {}

    @property
    def is_connected(self) -> bool:
        return self._state != _ConnState.DISCONNECTED

    def _next_id(self) -> str:
        self._request_id += 1
        return str(self._request_id)

    async def connect(self) -> None:
        """Start the connection background task."""
        if self._task and not self._task.done():
            return
        self._stop = False
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the connection."""
        self._stop = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._state = _ConnState.DISCONNECTED
        self._auth_event.clear()
        self._cancel_pending()

    async def _run(self) -> None:
        """Main loop: connect, receive, reconnect on disconnect."""
        while not self._stop:
            try:
                await self._connect_and_run()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"WebSocket error: {e}")

            self._ws = None
            self._state = _ConnState.DISCONNECTED
            self._auth_event.clear()
            self._cancel_pending()

            if self._stop:
                break
            if not self._auto_reconnect:
                raise ConnectionError(f"WebSocket disconnected from {self.url}")
            delay = 5 + random.random() * 5
            logger.info(f"Reconnecting in {delay:.1f}s...")
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break

    async def _connect_and_run(self) -> None:
        """Establish connection, authenticate, and process messages."""
        self._ws = await websockets.connect(
            self.url,
            additional_headers={"User-Agent": "Python"},
            ping_interval=None,  # Disabled — we handle keepalive ourselves
            ping_timeout=None,
        )
        self._state = _ConnState.CONNECTED
        logger.info(f"Connected to {self.url}")

        receive_task = asyncio.create_task(self._receive_loop())
        ping_task = asyncio.create_task(self._ping_loop())
        try:
            if self._needs_auth:
                await self._authenticate()
            else:
                self._state = _ConnState.AUTHENTICATED
                self._auth_event.set()

            await self._replay_subscriptions()
            await receive_task
        finally:
            ping_task.cancel()
            receive_task.cancel()
            for t in (ping_task, receive_task):
                try:
                    await t
                except asyncio.CancelledError:
                    pass
            await self._ws.close()

    async def _receive_loop(self) -> None:
        """Read messages from the WebSocket."""
        try:
            async for raw in self._ws:
                await self._handle_message(raw)
        except websockets.ConnectionClosed:
            logger.info("WebSocket closed")
        except asyncio.CancelledError:
            raise

    async def _handle_message(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        request_id = data.get("requestId")
        if request_id and request_id in self._pending:
            future = self._pending.pop(request_id)
            if not future.done():
                future.set_result(data)
            return

        # Push notification / subscription update
        await self._on_message(data)

    def _cancel_pending(self) -> None:
        """Cancel all pending request futures."""
        for future in self._pending.values():
            if not future.done():
                future.set_exception(ConnectionError("WebSocket disconnected"))
        self._pending.clear()

    async def _authenticate(self) -> None:
        """Send auth message on the trade endpoint."""
        if not self._signer or self._subaccount_id is None:
            logger.error("Cannot authenticate: no signer or subaccount_id")
            return

        payload, signature = self._signer.sign_auth(self._subaccount_id)

        resp = await self._send_request(
            "auth",
            {
                "message": json.dumps(payload),
                "signature": signature,
            },
        )

        if resp and resp.get("status") == 200:
            self._state = _ConnState.AUTHENTICATED
            self._auth_event.set()
            logger.info("Authenticated successfully")
        else:
            logger.error(f"Auth failed: {resp}")

    async def _replay_subscriptions(self) -> None:
        """Re-subscribe to all tracked subscriptions after reconnect."""
        for params in list(self._subscriptions.values()):
            await self._send_fire_and_forget("subscribe", params)

    async def _ping_loop(self) -> None:
        """Send application-level pings every ping_interval seconds.

        If the server doesn't respond within ping_timeout, close the socket
        to trigger a reconnect (or raise if auto_reconnect is False).
        Set ping_interval=0 to disable.
        """
        if self._ping_interval <= 0:
            return
        try:
            while True:
                await asyncio.sleep(self._ping_interval)
                resp = await self._send_request("ping", {}, timeout=self._ping_timeout)
                if resp is None:
                    logger.warning("Ping timed out — closing connection")
                    await self._ws.close()
                    return
        except asyncio.CancelledError:
            return

    async def ping(self) -> Optional[Dict]:
        """Send an application-level ping and return the response."""
        return await self._send_request("ping", {}, timeout=self._ping_timeout)

    async def _send_request(self, method: str, params: Dict[str, Any], timeout: float = 10) -> Optional[Dict]:
        """Send a request and wait for a response."""
        req_id = self._next_id()
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending[req_id] = future

        msg = json.dumps({"id": req_id, "method": method, "params": params})
        try:
            await self._ws.send(msg)
        except Exception as e:
            logger.warning(f"Send failed: {e}")
            self._pending.pop(req_id, None)
            return None

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            return None

    async def _send_fire_and_forget(self, method: str, params: Dict[str, Any]) -> None:
        """Send without waiting for response."""
        req_id = self._next_id()
        msg = json.dumps({"id": req_id, "method": method, "params": params})
        try:
            await self._ws.send(msg)
        except Exception as e:
            logger.warning(f"Send failed: {e}")

    async def subscribe(self, sub_id: int, params: Dict[str, Any]) -> None:
        """Subscribe and track for replay on reconnect."""
        self._subscriptions[sub_id] = params
        if self._state == _ConnState.AUTHENTICATED:
            await self._send_fire_and_forget("subscribe", params)

    async def unsubscribe(self, sub_id: int, params: Dict[str, Any]) -> None:
        """Unsubscribe and remove from tracking."""
        self._subscriptions.pop(sub_id, None)
        if self._state == _ConnState.AUTHENTICATED:
            await self._send_fire_and_forget("unsubscribe", params)


_METHOD_TO_CHANNEL: Dict[str, str] = {
    "candle_update": "candles",
    "market_price_update": "marketPrices",
    "orderbook_depth_update": "orderbook",
    "subAccountEvent": "subAccountUpdates",
    "trade": "trades",
}


class WebSocketManager:
    """
    Manages two lazy async WebSocket connections:
    - info (/ws/info) for public data
    - trade (/ws/trade) for authenticated data and trading actions
    """

    def __init__(
        self,
        base_url: str,
        signer: Optional[Signer] = None,
        subaccount_id: Optional[int] = None,
        auto_reconnect: bool = True,
        ping_interval: int = 30,
        ping_timeout: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._signer = signer
        self._subaccount_id = subaccount_id
        self._auto_reconnect = auto_reconnect
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout

        self._info_conn: Optional[_Connection] = None
        self._trade_conn: Optional[_Connection] = None

        self._callbacks_by_channel: Dict[str, Dict[int, Callable]] = defaultdict(dict)
        self._error_callbacks: Dict[int, Callable] = {}
        self._sub_params: Dict[int, Dict[str, Any]] = {}
        self._sub_endpoint: Dict[int, str] = {}  # "info" or "trade"
        self._next_sub_id = 0

    async def _get_info_conn(self) -> _Connection:
        if self._info_conn is None:
            self._info_conn = _Connection(
                f"{self._base_url}/info",
                on_message=self._dispatch,
                auto_reconnect=self._auto_reconnect,
                ping_interval=self._ping_interval,
                ping_timeout=self._ping_timeout,
            )
            await self._info_conn.connect()
        return self._info_conn

    async def _get_trade_conn(self) -> _Connection:
        if self._trade_conn is None:
            self._trade_conn = _Connection(
                f"{self._base_url}/trade",
                on_message=self._dispatch,
                signer=self._signer,
                subaccount_id=self._subaccount_id,
                needs_auth=True,
                auto_reconnect=self._auto_reconnect,
                ping_interval=self._ping_interval,
                ping_timeout=self._ping_timeout,
            )
            await self._trade_conn.connect()
        return self._trade_conn

    async def _dispatch(self, data: Dict[str, Any]) -> None:
        """Route push notifications and subscribe acks to registered callbacks."""
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        # Don't route unsubscribe acks — only subscribe acks and push messages
        if result.get("status") == "unsubscribed":
            return
        msg_type = (
            _METHOD_TO_CHANNEL.get(data.get("method"))  # push notification
            or result.get("type")  # subscribe ack
        )
        if not msg_type:
            return
        for sub_id, callback in list(self._callbacks_by_channel.get(msg_type, {}).items()):
            try:
                result = callback(data)
                if asyncio.isfuture(result) or asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning(f"Callback error (sub {sub_id}): {e}", exc_info=True)
                on_error = self._error_callbacks.get(sub_id)
                if on_error:
                    try:
                        err_result = on_error(e, data)
                        if asyncio.isfuture(err_result) or asyncio.iscoroutine(err_result):
                            await err_result
                    except Exception:
                        logger.warning(f"on_error callback itself raised (sub {sub_id})", exc_info=True)

    async def subscribe(
        self,
        channel: str,
        callback: Callable,
        on_error: Optional[Callable] = None,
        **kwargs: Any,
    ) -> int:
        """
        Subscribe to a channel. Returns a subscription ID.

        Args:
            channel: e.g. "marketPrices", "orderbook", "subAccountUpdates"
            callback: sync or async function called with each push message
            on_error: optional sync or async ``(exception, message_data)``
                handler invoked when ``callback`` raises. If not provided,
                errors are logged and the subscription continues silently.
            **kwargs: channel-specific params (symbol, timeframe, etc.)

        Orderbook-specific kwargs:
            format: ``"diff"`` (default) or ``"snapshot"``.
                Diff mode sends an initial snapshot then only changed levels.
                Snapshot mode sends the full book on every update.
            depth: ``10``, ``50`` (default), or ``100``.
                Number of price levels per side.
            updateFrequencyMs: ``50``, ``100``, ``250`` (default), ``500``,
                or ``1000``. When depth is 100, only 250/500/1000 are allowed.

        Note:
            Callbacks are dispatched by channel type only. If you have
            multiple subscriptions to the same channel (e.g. orderbook for
            different symbols), each callback receives all messages for that
            channel. Filter by symbol inside your callback if needed.
        """
        params: Dict[str, Any] = {"type": channel, **kwargs}

        # subAccountUpdates needs the sub_account_id
        if channel == "subAccountUpdates" and "sub_account_id" not in params:
            if self._subaccount_id is not None:
                params["sub_account_id"] = str(self._subaccount_id)

        is_private = channel in PRIVATE_CHANNELS

        if is_private and (self._signer is None or self._subaccount_id is None):
            raise RuntimeError(
                f"Channel '{channel}' requires authentication but no private_key/subaccount_id was provided"
            )

        sub_id = self._next_sub_id
        self._next_sub_id += 1
        self._callbacks_by_channel[channel][sub_id] = callback
        if on_error is not None:
            self._error_callbacks[sub_id] = on_error
        self._sub_params[sub_id] = params
        self._sub_endpoint[sub_id] = "trade" if is_private else "info"

        conn = await self._get_trade_conn() if is_private else await self._get_info_conn()
        await conn.subscribe(sub_id, params)

        return sub_id

    async def unsubscribe(self, subscription_id: int) -> None:
        """Unsubscribe by ID."""
        params = self._sub_params.pop(subscription_id, None)
        endpoint = self._sub_endpoint.pop(subscription_id, None)
        self._error_callbacks.pop(subscription_id, None)
        channel = params.get("type") if params else None
        if channel and channel in self._callbacks_by_channel:
            self._callbacks_by_channel[channel].pop(subscription_id, None)

        if params and endpoint:
            conn = self._trade_conn if endpoint == "trade" else self._info_conn
            if conn:
                await conn.unsubscribe(subscription_id, params)

    async def post(self, rest_payload: Dict[str, Any], timeout: float = 10) -> Dict[str, Any]:
        """
        Send a signed trading action over the trade WebSocket.

        Takes a REST-format signed payload (from Signer.sign_*) and sends it
        as a ``method: "post"`` message with flattened params.
        """
        if self._signer is None or self._subaccount_id is None:
            raise RuntimeError("WebSocket trading requires a private_key and subaccount_id")

        conn = await self._get_trade_conn()
        try:
            await asyncio.wait_for(conn._auth_event.wait(), timeout=15)
        except asyncio.TimeoutError:
            raise RuntimeError("WebSocket authentication timed out")

        # Flatten REST envelope into WS params
        ws_params: Dict[str, Any] = {
            **rest_payload["params"],
            "signature": rest_payload["signature"],
            "nonce": rest_payload["nonce"],
            "expiresAfter": rest_payload["expiresAfter"],
        }
        # Delegation signers use a non-standard envelope with subaccountId
        # and walletAddress at the top level instead of inside params.
        for key in ("subaccountId", "walletAddress"):
            if key not in ws_params and key in rest_payload:
                ws_params[key] = rest_payload[key]

        resp = await conn._send_request("post", ws_params, timeout=timeout)
        if resp is None:
            raise RuntimeError("WebSocket request timed out")

        result = resp.get("result", {})
        if isinstance(result, dict) and "response" in result:
            return result["response"]
        return result

    async def stop(self) -> None:
        """Stop all connections."""
        if self._info_conn:
            await self._info_conn.stop()
        if self._trade_conn:
            await self._trade_conn.stop()

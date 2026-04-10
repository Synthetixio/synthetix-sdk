"""
Top-level Synthetix client — single entry point for the SDK.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from synthetix.rest.account import AccountAPI
from synthetix.rest.api import API
from synthetix.rest.market import MarketAPI
from synthetix.signing import Signer
from synthetix.utils.constants import (
    DEFAULT_EXPIRES_AFTER_MS,
    GROUPING_NA,
    GROUPING_POSITION_TPSL,
    ORDER_TYPE_LIMIT_GTC,
    ORDER_TYPE_MARKET,
    ORDER_TYPE_TRIGGER_SL,
    ORDER_TYPE_TRIGGER_TP,
    PROD_REST_URL,
    PROD_WS_URL,
)


class Synthetix:
    """
    Main entry point for the Synthetix Python SDK.

    Usage::

        # Read-only (no auth):
        snx = Synthetix()
        markets = snx.get_markets()

        # Trading:
        snx = Synthetix(private_key="0x...")
        snx.place_order("BTC-USDT", "buy", "0.01", "90000.00")
        positions = snx.get_positions()

        # Custom endpoints:
        snx = Synthetix(rest_url="https://papi.synthetix.io/v1",
                        ws_url="wss://papi.synthetix.io/v1/ws")

        # WebSocket (async):
        await snx.subscribe("marketPrices", callback=print, symbol="BTC-USDT")
    """

    def __init__(
        self,
        private_key: Optional[str] = None,
        subaccount_id: Optional[int] = None,
        rest_url: Optional[str] = None,
        ws_url: Optional[str] = None,
        timeout: Optional[float] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
        auto_reconnect: bool = True,
        ping_interval: int = 30,
        ping_timeout: int = 30,
    ) -> None:
        # URLs
        self._rest_url = rest_url or PROD_REST_URL
        self._ws_url = ws_url or PROD_WS_URL

        # REST client (always available)
        self._api = API(self._rest_url, timeout=timeout)
        self._market = MarketAPI(self._api)

        # Auth + trading (optional)
        self._signer: Optional[Signer] = None
        self._account: Optional[AccountAPI] = None
        self._subaccount_id: Optional[int] = subaccount_id
        self._expires_after_ms = expires_after_ms
        self._auto_reconnect = auto_reconnect
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout

        if private_key:
            self._signer = Signer(private_key)

            # Auto-discover subaccount if not provided
            if self._subaccount_id is None:
                ids = self._market.get_sub_account_ids(self._signer.address)
                if ids:
                    self._subaccount_id = ids[0] if isinstance(ids[0], int) else int(ids[0])

            if self._subaccount_id is not None:
                self._account = AccountAPI(self._api, self._signer, self._subaccount_id, expires_after_ms)

        # WebSocket manager (lazy)
        self._ws_manager = None

    @property
    def address(self) -> Optional[str]:
        """Wallet address (None if no private key)."""
        return self._signer.address if self._signer else None

    @property
    def subaccount_id(self) -> Optional[int]:
        return self._subaccount_id

    @subaccount_id.setter
    def subaccount_id(self, value: int) -> None:
        self._subaccount_id = value
        if self._signer:
            self._account = AccountAPI(self._api, self._signer, value, self._expires_after_ms)
        if self._ws_manager:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                loop.create_task(self._ws_manager.stop())
            else:
                asyncio.run(self._ws_manager.stop())
            self._ws_manager = None

    def _require_account(self) -> AccountAPI:
        if self._account is None:
            raise RuntimeError("Trading requires a private_key and subaccount_id")
        return self._account

    def _require_auth(self) -> tuple:
        """Return (signer, subaccount_id) or raise if not authenticated."""
        if self._signer is None or self._subaccount_id is None:
            raise RuntimeError("Trading requires a private_key and subaccount_id")
        return self._signer, self._subaccount_id

    # ── Market Data (public) ────────────────────────────────────────

    def get_markets(self) -> List[Dict]:
        """Get all available markets.

        Returns a list of market dicts, each containing:
        symbol, description, baseAsset, quoteAsset, isOpen, isCloseOnly,
        priceIncrement, minOrderSize, orderSizeIncrement, contractSize,
        maxMarketOrderSize, maxLimitOrderSize, minNotionalValue,
        maintenanceMarginTiers, etc.
        """
        return self._market.get_markets()

    def get_market_prices(self) -> Dict[str, Dict]:
        """Get current prices for all markets.

        Returns a dict keyed by symbol (e.g. ``"BTC-USDT"``), each containing:
        symbol, bestBid, bestAsk, markPrice, indexPrice, lastPrice,
        prevDayPrice, volume24h, quoteVolume24h, fundingRate, openInterest,
        timestamp.
        """
        return self._market.get_market_prices()

    def get_orderbook(self, symbol: str) -> Dict:
        """Get orderbook snapshot for a symbol.

        Returns ``{"bids": [[price, size], ...], "asks": [[price, size], ...]}``.
        Each entry is a list of two strings: ``[price, quantity]``.
        """
        return self._market.get_orderbook(symbol)

    def get_last_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a symbol.

        Returns a list of trade dicts, each containing:
        tradeId, symbol, side, price, quantity, timestamp, isMaker.
        """
        return self._market.get_last_trades(symbol, limit)

    def get_funding_rate(self, symbol: str) -> Dict:
        """Get current funding rate for a symbol.

        Returns a dict containing:
        symbol, estimatedFundingRate, lastSettlementRate, lastSettlementTime,
        nextFundingTime, fundingInterval.
        """
        return self._market.get_funding_rate(symbol)

    def get_funding_rate_history(self, symbol: str, start_time: int, end_time: int) -> Dict:
        """Get funding rate history for a symbol over a time range.

        Args:
            symbol: Market symbol (e.g. ``"ETH-USDT"``).
            start_time: Start timestamp in milliseconds.
            end_time: End timestamp in milliseconds.

        Returns ``{"symbol": str, "fundingRates": [{"fundingRate", "fundingTime", "appliedAt"}]}``.
        """
        return self._market.get_funding_rate_history(symbol, start_time, end_time)

    def get_open_interest(self) -> List[Dict]:
        """Get open interest for all markets.

        Returns a list of dicts, each containing:
        symbol, openInterest, longOpenInterest, shortOpenInterest, timestamp.
        """
        return self._market.get_open_interest()

    def get_candles(
        self,
        symbol: str,
        interval: str,
        start_time: int = 0,
        end_time: int = 0,
        limit: int = 0,
    ) -> Dict:
        """Get OHLC candlestick data for a symbol.

        Args:
            symbol: Trading pair (e.g. ``"BTC-USDT"``).
            interval: Timeframe — ``"1m"``, ``"5m"``, ``"15m"``, ``"30m"``,
                ``"1h"``, ``"4h"``, ``"8h"``, ``"12h"``, ``"1d"``, ``"3d"``,
                ``"1w"``, ``"1M"``, ``"3M"``.
            start_time: Start timestamp in milliseconds (optional).
            end_time: End timestamp in milliseconds (optional).
            limit: Max number of candles to return (optional).

        Returns ``{"symbol": str, "interval": str, "candles": [...]}``.
        """
        return self._market.get_candles(symbol, interval, start_time, end_time, limit)

    def get_sub_account_ids(self, wallet_address: Optional[str] = None) -> List[int]:
        """Get subaccount IDs for a wallet address (public, no auth required).

        Args:
            wallet_address: Wallet address to look up. Defaults to the
                connected wallet if a private_key was provided.

        Returns a list of integer subaccount IDs.
        """
        addr = wallet_address or (self._signer.address if self._signer else None)
        if not addr:
            raise ValueError("wallet_address required (or provide a private_key)")
        return self._market.get_sub_account_ids(addr)

    def get_position_history(
        self,
        symbol: Optional[str] = None,
        start_time: int = 0,
        end_time: int = 0,
        limit: int = 0,
        offset: int = 0,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Get historical (closed) positions for a subaccount.

        Args:
            symbol: Filter by symbol (optional).
            start_time: Start timestamp in milliseconds (optional).
            end_time: End timestamp in milliseconds (optional).
            limit: Max number of positions to return (optional).
            offset: Pagination offset (optional).

        Returns ``{"positions": [...], "hasMore": bool}``.
        """
        return self._require_account().get_position_history(
            symbol,
            start_time,
            end_time,
            limit,
            offset,
            subaccount_id,
        )

    # ── Trading (authenticated) ─────────────────────────────────────

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        price: str = "",
        order_type: str = ORDER_TYPE_LIMIT_GTC,
        reduce_only: bool = False,
        client_order_id: str = "",
        close_position: bool = False,
        trigger_price: str = "",
        is_trigger_market: bool = False,
    ) -> Dict:
        """Place a single order (convenience wrapper)."""
        order = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "price": price,
            "quantity": quantity,
            "reduceOnly": reduce_only,
            "clientOrderId": client_order_id,
            "closePosition": close_position,
            "triggerPrice": trigger_price,
            "isTriggerMarket": is_trigger_market,
        }
        # Standalone trigger orders require positionTpsl grouping
        is_trigger = order_type in (ORDER_TYPE_TRIGGER_TP, ORDER_TYPE_TRIGGER_SL)
        grouping = GROUPING_POSITION_TPSL if is_trigger else GROUPING_NA
        return self._require_account().place_orders([order], grouping=grouping)

    def market_order(self, symbol: str, side: str, quantity: str) -> Dict:
        """Place a market order."""
        return self.place_order(symbol, side, quantity, order_type=ORDER_TYPE_MARKET)

    def place_orders(self, orders: List[Dict[str, Any]], grouping: str = "na") -> Dict:
        return self._require_account().place_orders(orders, grouping)

    def modify_order(
        self,
        order_id: int,
        price: Optional[str] = None,
        quantity: Optional[str] = None,
        trigger_price: Optional[str] = None,
    ) -> Dict:
        return self._require_account().modify_order(
            order_id, price=price, quantity=quantity, trigger_price=trigger_price
        )

    def cancel_order(self, order_id: int) -> Dict:
        """Cancel a single order (convenience wrapper)."""
        return self._require_account().cancel_orders([order_id])

    def cancel_orders(self, order_ids: List[int]) -> Dict:
        return self._require_account().cancel_orders(order_ids)

    def cancel_order_by_cloid(self, client_order_id: str) -> Dict:
        """Cancel a single order by client order ID (convenience wrapper)."""
        return self._require_account().cancel_orders_by_cloid([client_order_id])

    def cancel_orders_by_cloid(self, client_order_ids: List[str]) -> Dict:
        """Cancel orders by client order ID."""
        return self._require_account().cancel_orders_by_cloid(client_order_ids)

    def cancel_all_orders(self, symbol: str) -> Dict:
        return self._require_account().cancel_all_orders(symbol)

    def schedule_cancel(
        self,
        timeout_seconds: int,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Configure the dead-man switch (schedule cancel).

        When active, all open orders are canceled automatically if no heartbeat
        is received within ``timeout_seconds``. Pass ``0`` to disable.

        Args:
            timeout_seconds: Inactivity timeout in seconds. Use ``0`` to
                disable the dead-man switch.
            subaccount_id: Subaccount ID (defaults to active).

        Returns ``{"isActive": bool, "message": str, "timeoutSeconds": int,
        "triggerTime": int|null}``.
        """
        return self._require_account().schedule_cancel(timeout_seconds, subaccount_id)

    # ── Account Queries (authenticated) ─────────────────────────────

    def get_sub_accounts(self) -> Any:
        """List all subaccounts for the authenticated wallet.

        Returns ``{"subAccounts": [...]}``, where each entry contains:
        subAccountId, masterAccountId, subAccountName, collaterals,
        crossMarginSummary, positions, marketPreferences, feeRates,
        delegatedSigners.
        """
        return self._require_account().get_sub_accounts()

    def get_sub_account(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get detailed info for a single subaccount.

        Returns a dict containing:

        - **subAccountId** — string ID
        - **masterAccountId** — string ID of the master (None if this is master)
        - **subAccountName** — display name (e.g. ``"Master"``)
        - **collaterals** — list of ``{"symbol", "quantity", "withdrawable", "pendingWithdraw"}``
        - **crossMarginSummary** — ``{"accountValue", "availableMargin",
          "totalUnrealizedPnl", "maintenanceMargin", "initialMargin",
          "withdrawable", "adjustedAccountValue"}``
        - **positions** — list of position dicts (symbol, side, entryPrice,
          quantity, pnl, upnl, usedMargin, maintenanceMargin, liquidationPrice)
        - **marketPreferences** — ``{"leverages": {...}}``
        - **feeRates** — ``{"makerFeeRate", "takerFeeRate", "tierName"}``
        """
        return self._require_account().get_sub_account(subaccount_id)

    def get_positions(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get open positions for a subaccount.

        Returns a list of position dicts, each containing:
        positionId, subAccountId, symbol, side, entryPrice, quantity,
        unrealizedPnl, usedMargin, maintenanceMargin, liquidationPrice,
        status, netFunding, updatedAt, createdAt.
        """
        return self._require_account().get_positions(subaccount_id)

    def get_open_orders(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get all resting open orders for a subaccount.

        Returns a list of order dicts, each containing:
        order, orderId, symbol, side, type, quantity, price, triggerPrice,
        triggerPriceType, timeInForce, reduceOnly, postOnly, createdTime,
        updatedTime, filledQuantity, closePosition.
        """
        return self._require_account().get_open_orders(subaccount_id)

    def get_order_history(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get historical orders (filled, canceled, etc.) for a subaccount.

        Returns a list of order dicts with the same fields as
        :meth:`get_open_orders` plus status information.
        """
        return self._require_account().get_order_history(subaccount_id)

    def get_trades(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get trade fill history for a subaccount.

        Returns ``{"trades": [...], "hasMore": bool, "total": int}``.
        Each trade contains: tradeId, order, orderId, symbol, side, price,
        quantity, realizedPnl, fee, feeRate, timestamp, maker, reduceOnly,
        markPrice, entryPrice, triggeredByLiquidation, direction, postOnly.
        """
        return self._require_account().get_trades(subaccount_id)

    def get_trades_for_position(
        self,
        position_id: str,
        limit: int = 0,
        offset: int = 0,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Get trade fills for a specific position.

        Args:
            position_id: Position ID to fetch trades for.
            limit: Max number of trades to return (default 100, max 1000).
            offset: Pagination offset (default 0).
            subaccount_id: Subaccount ID (defaults to active).

        Returns ``{"trades": [...], "hasMore": bool}``.
        Each trade contains: tradeId, orderId, symbol, orderType, side, price,
        quantity, realizedPnl, fee, feeRate, timestamp, maker, reduceOnly,
        markPrice, entryPrice, triggeredByLiquidation, direction, postOnly.
        """
        return self._require_account().get_trades_for_position(position_id, limit, offset, subaccount_id)

    def get_portfolio(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get portfolio snapshots for a subaccount.

        Returns a list of snapshot dicts, each containing:
        assets (list of per-asset breakdowns) and timestamp.
        """
        return self._require_account().get_portfolio(subaccount_id)

    def get_balance_updates(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get balance change history (deposits, withdrawals, PnL, fees).

        Returns ``{"balanceUpdates": [...]}``, each containing:
        id, subAccountId, action, status, amount, collateral, timestamp,
        destinationAddress, txHash.
        """
        return self._require_account().get_balance_updates(subaccount_id)

    def get_transfers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get collateral transfer history for a subaccount.

        Returns ``{"transfers": [...], "total": int}``, each transfer containing:
        transferId, from, to, symbol, amount, transferType, status, timestamp.
        """
        return self._require_account().get_transfers(subaccount_id)

    def get_performance_history(
        self,
        period: Optional[str] = None,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Get account performance history for a given period.

        Args:
            period: One of ``"day"``, ``"week"``, ``"month"``, ``"year"``
                (default ``"day"``).
            subaccount_id: Subaccount ID (defaults to active).

        Returns a dict with:
        - **subAccountId** — string ID
        - **period** — the requested period string
        - **performanceHistory** — ``{"history": [{"sampledAt": int,
          "accountValue": str, "pnl": str}], "volume": str}``
        """
        return self._require_account().get_performance_history(period, subaccount_id)

    # ── Account Management (authenticated) ──────────────────────────

    def create_subaccount(self, name: Optional[str] = None) -> Dict:
        """Create a new subaccount under the current master account.

        Returns ``{"subAccountId": str, "subAccountName": str}``.
        """
        return self._require_account().create_subaccount(name)

    def update_leverage(self, symbol: str, leverage: int, subaccount_id: Optional[int] = None) -> Dict:
        """Set leverage for a symbol on a subaccount.

        Returns ``{"symbol": str, "newLeverage": str, "previousLeverage": str}``.
        """
        return self._require_account().update_leverage(symbol, leverage, subaccount_id)

    def update_sub_account_name(self, name: str, subaccount_id: Optional[int] = None) -> Dict:
        """Rename a subaccount.

        Returns ``{"subAccountId": str, "name": str}``.
        """
        return self._require_account().update_sub_account_name(name, subaccount_id)

    def withdraw_collateral(
        self,
        amount: str,
        symbol: str = "USDC",
        destination: Optional[str] = None,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Withdraw collateral to a destination address (defaults to own wallet).

        Returns ``{"requestId": str, "symbol": str, "amount": str, "destination": str}``.
        """
        return self._require_account().withdraw_collateral(amount, symbol, destination, subaccount_id)

    def transfer_collateral(
        self,
        amount: str,
        to_subaccount_id: int,
        symbol: str = "USDC",
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Transfer collateral between subaccounts.

        Returns ``{"status": "success", "symbol": str, "amount": str,
        "to": {"subAccountId": str}, "transferId": str}``.
        """
        return self._require_account().transfer_collateral(amount, to_subaccount_id, symbol, subaccount_id)

    # ── Fees & Funding (authenticated) ──────────────────────────────

    def get_fees(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get fee tier structure and current trading volume.

        Returns ``{"feeTiers": [{"symbol", "feeRate"}],
        "userDailyVolume": str, "userFeeTier": {"symbol", "feeRate"}}``.
        """
        return self._require_account().get_fees(subaccount_id)

    def get_funding_payments(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get funding payment history with summary.

        Returns ``{"summary": {"totalFundingReceived", "totalFundingPaid",
        "netFunding", "totalPayments", "averagePaymentSize"},
        "fundingHistory": [{"paymentId", "symbol", "positionSize",
        "fundingRate", "payment", "timestamp", ...}]}``.
        """
        return self._require_account().get_funding_payments(subaccount_id)

    def get_rate_limits(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get current rate limit usage.

        Returns ``{"requestsUsed": int, "requestsCap": int}``.
        """
        return self._require_account().get_rate_limits(subaccount_id)

    # ── Delegation (authenticated) ──────────────────────────────────

    def add_delegated_signer(
        self,
        delegate_address: str,
        permissions: List[str],
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Add a delegated signer with specified permissions.

        Args:
            delegate_address: Wallet address to delegate to.
            permissions: Permission list (e.g. ``["session"]``).

        Returns ``{"walletAddress": str, "permissions": [...]}``.
        """
        return self._require_account().add_delegated_signer(delegate_address, subaccount_id, permissions=permissions)

    def get_delegated_signers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get all delegated signers for a subaccount.

        Returns ``{"delegatedSigners": [{"subAccountId", "walletAddress",
        "permissions", "expiresAt"}]}``.
        """
        return self._require_account().get_delegated_signers(subaccount_id)

    def get_delegations_for_delegate(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get delegations from the perspective of this wallet as delegate.

        Returns ``{"delegatedAccounts": [...]}``.
        """
        return self._require_account().get_delegations_for_delegate(subaccount_id)

    def remove_delegated_signer(self, delegate_address: str, subaccount_id: Optional[int] = None) -> Dict:
        """Remove a delegated signer.

        Returns ``{"walletAddress": str}``.
        """
        return self._require_account().remove_delegated_signer(delegate_address, subaccount_id)

    def remove_all_delegated_signers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Remove all delegated signers for a subaccount."""
        return self._require_account().remove_all_delegated_signers(subaccount_id)

    # ── WebSocket Trading (authenticated) ────────────────────────────

    async def ws_place_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        price: str = "",
        order_type: str = ORDER_TYPE_LIMIT_GTC,
        reduce_only: bool = False,
        client_order_id: str = "",
        close_position: bool = False,
        trigger_price: str = "",
        is_trigger_market: bool = False,
    ) -> Dict:
        """Place a single order via WebSocket."""
        order = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "price": price,
            "quantity": quantity,
            "reduceOnly": reduce_only,
            "clientOrderId": client_order_id,
            "closePosition": close_position,
            "triggerPrice": trigger_price,
            "isTriggerMarket": is_trigger_market,
        }
        is_trigger = order_type in (ORDER_TYPE_TRIGGER_TP, ORDER_TYPE_TRIGGER_SL)
        grouping = GROUPING_POSITION_TPSL if is_trigger else GROUPING_NA
        return await self.ws_place_orders([order], grouping=grouping)

    async def ws_market_order(self, symbol: str, side: str, quantity: str) -> Dict:
        """Place a market order via WebSocket."""
        return await self.ws_place_order(symbol, side, quantity, order_type=ORDER_TYPE_MARKET)

    async def ws_place_orders(self, orders: List[Dict[str, Any]], grouping: str = "na") -> Dict:
        """Place one or more orders via WebSocket."""
        signer, subaccount_id = self._require_auth()
        request = signer.sign_place_orders(
            subaccount_id, orders, grouping=grouping, expires_after_ms=self._expires_after_ms
        )
        return await self._ensure_ws().post(request)

    async def ws_modify_order(
        self,
        order_id: int,
        price: Optional[str] = None,
        quantity: Optional[str] = None,
        trigger_price: Optional[str] = None,
    ) -> Dict:
        """Modify an existing order via WebSocket."""
        signer, subaccount_id = self._require_auth()
        request = signer.sign_modify_order(
            subaccount_id,
            order_id,
            price=price or "",
            quantity=quantity or "",
            trigger_price=trigger_price or "",
            expires_after_ms=self._expires_after_ms,
        )
        return await self._ensure_ws().post(request)

    async def ws_cancel_order(self, order_id: int) -> Dict:
        """Cancel a single order via WebSocket."""
        return await self.ws_cancel_orders([order_id])

    async def ws_cancel_orders(self, order_ids: List[int]) -> Dict:
        """Cancel orders by ID via WebSocket."""
        signer, subaccount_id = self._require_auth()
        request = signer.sign_cancel_orders(subaccount_id, order_ids, expires_after_ms=self._expires_after_ms)
        return await self._ensure_ws().post(request)

    async def ws_cancel_order_by_cloid(self, client_order_id: str) -> Dict:
        """Cancel a single order by client order ID via WebSocket."""
        return await self.ws_cancel_orders_by_cloid([client_order_id])

    async def ws_cancel_orders_by_cloid(self, client_order_ids: List[str]) -> Dict:
        """Cancel orders by client order ID via WebSocket."""
        signer, subaccount_id = self._require_auth()
        request = signer.sign_cancel_orders_by_cloid(
            subaccount_id, client_order_ids, expires_after_ms=self._expires_after_ms
        )
        return await self._ensure_ws().post(request)

    async def ws_cancel_all_orders(self, symbol: str) -> Dict:
        """Cancel all open orders for a symbol via WebSocket."""
        signer, subaccount_id = self._require_auth()
        request = signer.sign_cancel_all_orders(
            subaccount_id, symbols=[symbol], expires_after_ms=self._expires_after_ms
        )
        return await self._ensure_ws().post(request)

    # ── WebSocket Account Queries (authenticated) ──────────────────

    async def _ws_query(self, action: str, subaccount_id: Optional[int] = None, **params: Any) -> Any:
        """Sign and send a generic get* query over WebSocket."""
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        action_params = params if params else None
        request = signer.sign_action(
            sub_id, action, action_params=action_params, expires_after_ms=self._expires_after_ms
        )
        return await self._ensure_ws().post(request)

    async def ws_get_open_orders(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get open orders via WebSocket."""
        return await self._ws_query("getOpenOrders", subaccount_id)

    async def ws_get_positions(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get open positions via WebSocket."""
        return await self._ws_query("getPositions", subaccount_id)

    async def ws_get_sub_accounts(self) -> Any:
        """List all subaccounts via WebSocket."""
        return await self._ws_query("getSubAccounts")

    async def ws_get_sub_account(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get subaccount details via WebSocket."""
        return await self._ws_query("getSubAccount", subaccount_id)

    async def ws_get_order_history(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get historical orders via WebSocket."""
        return await self._ws_query("getOrderHistory", subaccount_id)

    async def ws_get_trades(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get trade history via WebSocket."""
        return await self._ws_query("getTrades", subaccount_id)

    async def ws_get_portfolio(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get portfolio summary via WebSocket."""
        return await self._ws_query("getPortfolio", subaccount_id)

    async def ws_get_balance_updates(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get balance change history via WebSocket."""
        return await self._ws_query("getBalanceUpdates", subaccount_id)

    async def ws_get_transfers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get transfer history via WebSocket."""
        return await self._ws_query("getTransfers", subaccount_id)

    async def ws_get_fees(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get fee structure via WebSocket."""
        return await self._ws_query("getFees", subaccount_id)

    async def ws_get_funding_payments(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get funding payment history via WebSocket."""
        return await self._ws_query("getFundingPayments", subaccount_id)

    async def ws_get_rate_limits(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get rate limit status via WebSocket."""
        return await self._ws_query("getRateLimits", subaccount_id)

    async def ws_get_position_history(
        self,
        symbol: Optional[str] = None,
        start_time: int = 0,
        end_time: int = 0,
        limit: int = 0,
        offset: int = 0,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Get historical (closed) positions via WebSocket."""
        kwargs: Dict[str, Any] = {}
        if symbol:
            kwargs["symbol"] = symbol
        if start_time:
            kwargs["startTime"] = start_time
        if end_time:
            kwargs["endTime"] = end_time
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        return await self._ws_query("getPositionHistory", subaccount_id, **kwargs)

    async def ws_get_performance_history(
        self,
        period: Optional[str] = None,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Get account performance history via WebSocket."""
        kwargs: Dict[str, Any] = {}
        if period:
            kwargs["period"] = period
        return await self._ws_query("getPerformanceHistory", subaccount_id, **kwargs)

    async def ws_get_delegated_signers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get list of delegated signers via WebSocket."""
        return await self._ws_query("getDelegatedSigners", subaccount_id)

    async def ws_get_delegations_for_delegate(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get delegations from the perspective of the delegate via WebSocket."""
        return await self._ws_query("getDelegationsForDelegate", subaccount_id)

    # ── WebSocket Account Management (authenticated) ─────────────

    async def ws_create_subaccount(self, name: Optional[str] = None) -> Dict:
        """Create a new subaccount via WebSocket."""
        signer, subaccount_id = self._require_auth()
        request = signer.sign_create_subaccount(subaccount_id, name=name or "", expires_after_ms=self._expires_after_ms)
        return await self._ensure_ws().post(request)

    async def ws_update_leverage(self, symbol: str, leverage: int, subaccount_id: Optional[int] = None) -> Dict:
        """Set leverage for a symbol via WebSocket."""
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        request = signer.sign_update_leverage(sub_id, symbol, str(leverage), expires_after_ms=self._expires_after_ms)
        return await self._ensure_ws().post(request)

    async def ws_withdraw_collateral(
        self,
        amount: str,
        symbol: str = "USDC",
        destination: Optional[str] = None,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Withdraw collateral via WebSocket."""
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        dest = destination or signer.address
        request = signer.sign_withdraw_collateral(sub_id, symbol, amount, dest, expires_after_ms=self._expires_after_ms)
        return await self._ensure_ws().post(request)

    async def ws_transfer_collateral(
        self,
        amount: str,
        to_subaccount_id: int,
        symbol: str = "USDC",
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Transfer collateral between subaccounts via WebSocket."""
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        request = signer.sign_transfer_collateral(
            sub_id, to_subaccount_id, symbol, amount, expires_after_ms=self._expires_after_ms
        )
        return await self._ensure_ws().post(request)

    # ── WebSocket Delegation (authenticated) ─────────────────────

    async def ws_add_delegated_signer(
        self,
        delegate_address: str,
        permissions: List[str],
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Add a delegated signer via WebSocket."""
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        request = signer.sign_add_delegated_signer(
            sub_id, delegate_address, permissions=permissions, expires_after_ms=self._expires_after_ms
        )
        return await self._ensure_ws().post(request)

    async def ws_remove_delegated_signer(self, delegate_address: str, subaccount_id: Optional[int] = None) -> Dict:
        """Remove a delegated signer via WebSocket."""
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        request = signer.sign_remove_delegated_signer(sub_id, delegate_address, expires_after_ms=self._expires_after_ms)
        return await self._ensure_ws().post(request)

    async def ws_remove_all_delegated_signers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Remove all delegated signers via WebSocket."""
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        request = signer.sign_remove_all_delegated_signers(sub_id, expires_after_ms=self._expires_after_ms)
        return await self._ensure_ws().post(request)

    async def ws_schedule_cancel(
        self,
        timeout_seconds: int,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Configure the dead-man switch via WebSocket.

        When active, all open orders are canceled automatically if no heartbeat
        is received within ``timeout_seconds``. Pass ``0`` to disable.

        Args:
            timeout_seconds: Inactivity timeout in seconds. Use ``0`` to
                disable the dead-man switch.
            subaccount_id: Subaccount ID (defaults to active).

        Returns ``{"isActive": bool, "message": str, "timeoutSeconds": int,
        "triggerTime": int|null}``.
        """
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        request = signer.sign_schedule_cancel(sub_id, timeout_seconds, expires_after_ms=self._expires_after_ms)
        return await self._ensure_ws().post(request)

    async def ws_update_sub_account_name(self, name: str, subaccount_id: Optional[int] = None) -> Dict:
        """Rename a subaccount via WebSocket.

        Returns ``{"subAccountId": str, "name": str}``.
        """
        signer, sub_id = self._require_auth()
        sub_id = subaccount_id if subaccount_id is not None else sub_id
        request = signer.sign_update_sub_account_name(sub_id, name, expires_after_ms=self._expires_after_ms)
        return await self._ensure_ws().post(request)

    # ── WebSocket ───────────────────────────────────────────────────

    def _ensure_ws(self):
        if self._ws_manager is None:
            from synthetix.ws.manager import WebSocketManager

            self._ws_manager = WebSocketManager(
                self._ws_url,
                signer=self._signer,
                subaccount_id=self._subaccount_id,
                auto_reconnect=self._auto_reconnect,
                ping_interval=self._ping_interval,
                ping_timeout=self._ping_timeout,
            )
        return self._ws_manager

    async def subscribe(
        self,
        channel: str,
        callback: Callable,
        on_error: Optional[Callable] = None,
        **params: Any,
    ) -> int:
        """Subscribe to a WebSocket channel. Returns subscription ID.

        Args:
            channel: Channel name — ``"marketPrices"``, ``"orderbook"``,
                ``"trades"``, ``"candles"``, or ``"subAccountUpdates"``.
            callback: Sync or async function called with each push message.
            on_error: Optional sync or async ``(exception, message_data)``
                handler invoked when ``callback`` raises. If not provided,
                errors are logged and the subscription continues silently.
            **params: Channel-specific params (e.g. ``symbol``).

        Orderbook params:
            format: ``"diff"`` (default) or ``"snapshot"``.
            depth: ``10``, ``50`` (default), or ``100``.
            updateFrequencyMs: ``50``, ``100``, ``250`` (default), ``500``,
                or ``1000``. When depth is 100, only 250/500/1000 are allowed.

        Example::

            # Orderbook with custom depth and snapshot mode
            await snx.subscribe(
                "orderbook", callback, symbol="BTC-USDT",
                format="snapshot", depth=10, updateFrequencyMs=100,
            )
        """
        ws = self._ensure_ws()
        return await ws.subscribe(channel, callback, on_error=on_error, **params)

    async def unsubscribe(self, subscription_id: int) -> None:
        """Unsubscribe by ID."""
        if self._ws_manager:
            await self._ws_manager.unsubscribe(subscription_id)

    async def close(self) -> None:
        """Close WebSocket connections."""
        if self._ws_manager:
            await self._ws_manager.stop()
            self._ws_manager = None

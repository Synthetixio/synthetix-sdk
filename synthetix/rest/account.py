"""
Authenticated account and trading endpoints (POST /v1/trade).
All requests require EIP-712 signatures.
"""

from typing import Any, Dict, List, Optional

from synthetix.rest.api import API
from synthetix.signing import Signer
from synthetix.utils.constants import DEFAULT_EXPIRES_AFTER_MS


class AccountAPI:
    """Authenticated trading and account endpoints — all POST to /trade."""

    def __init__(
        self,
        api: API,
        signer: Signer,
        subaccount_id: int,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> None:
        self._api = api
        self._signer = signer
        self.subaccount_id = subaccount_id
        self.expires_after_ms = expires_after_ms

    def _trade(self, request: Dict[str, Any]) -> Any:
        """Send a signed request to /trade."""
        return self._api.post("/trade", request)

    def _action(
        self,
        action: str,
        subaccount_id: Optional[int] = None,
        **params: Any,
    ) -> Any:
        """Sign and send a generic subaccount action (get* queries)."""
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        action_params = params if params else None
        request = self._signer.sign_action(
            sid, action, action_params=action_params, expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    # ── Order Management ────────────────────────────────────────────

    def place_orders(
        self,
        orders: List[Dict[str, Any]],
        grouping: str = "na",
    ) -> Dict:
        """Place one or more orders in a single request.

        Args:
            orders: List of order dicts with camelCase keys (``symbol``,
                ``side``, ``orderType``, ``quantity``, etc.).
            grouping: ``"na"`` (default), ``"positionTpsl"``, or ``"twap"``.

        Returns ``{"statuses": [...]}``.
        """
        request = self._signer.sign_place_orders(
            self.subaccount_id, orders, grouping=grouping, expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    def modify_order(
        self,
        order_id: int,
        price: Optional[str] = None,
        quantity: Optional[str] = None,
        trigger_price: Optional[str] = None,
    ) -> Dict:
        """Modify an existing order."""
        request = self._signer.sign_modify_order(
            self.subaccount_id,
            order_id,
            price=price or "",
            quantity=quantity or "",
            trigger_price=trigger_price or "",
            expires_after_ms=self.expires_after_ms,
        )
        return self._trade(request)

    def cancel_orders(self, order_ids: List[int]) -> Dict:
        """Cancel orders by ID."""
        request = self._signer.sign_cancel_orders(self.subaccount_id, order_ids, expires_after_ms=self.expires_after_ms)
        return self._trade(request)

    def cancel_orders_by_cloid(self, client_order_ids: List[str]) -> Dict:
        """Cancel orders by client order ID."""
        request = self._signer.sign_cancel_orders_by_cloid(
            self.subaccount_id, client_order_ids, expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    def cancel_all_orders(self, symbol: str) -> Dict:
        """Cancel all open orders for the given symbol."""
        request = self._signer.sign_cancel_all_orders(
            self.subaccount_id, symbols=[symbol], expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    # ── Account/Position Queries ────────────────────────────────────

    def get_sub_accounts(self) -> Any:
        """List all subaccounts.

        Returns ``{"subAccounts": [{subAccountId, masterAccountId,
        subAccountName, collaterals, crossMarginSummary, positions,
        marketPreferences, feeRates, delegatedSigners}]}``.
        """
        return self._action("getSubAccounts")

    def get_sub_account(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get detailed info for a single subaccount.

        Returns a dict with: subAccountId, masterAccountId, subAccountName,
        collaterals (symbol, quantity, withdrawable, pendingWithdraw),
        crossMarginSummary (accountValue, availableMargin, totalUnrealizedPnl,
        maintenanceMargin, initialMargin, withdrawable, adjustedAccountValue),
        positions, marketPreferences, feeRates.
        """
        return self._action("getSubAccount", subaccount_id=subaccount_id)

    def get_positions(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get open positions.

        Each position contains: positionId, subAccountId, symbol, side,
        entryPrice, quantity, unrealizedPnl, usedMargin, maintenanceMargin,
        liquidationPrice, status, netFunding, updatedAt, createdAt.
        """
        return self._action("getPositions", subaccount_id=subaccount_id)

    def get_open_orders(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get open orders.

        Each order contains: order (``{"venueId": str}``), symbol, side, type,
        quantity, price, triggerPrice, triggerPriceType, timeInForce, reduceOnly,
        postOnly, createdTime, updatedTime, filledQuantity, closePosition,
        expiresAt (optional ISO timestamp for GTD order expiry).
        """
        return self._action("getOpenOrders", subaccount_id=subaccount_id)

    def get_order_history(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get historical orders (filled, canceled, etc.).

        Each order contains the same fields as ``get_open_orders()`` plus:
        expiresAt (optional ISO timestamp for GTD order expiry) and
        cancelReason (optional string explaining why the order was canceled).
        """
        return self._action("getOrderHistory", subaccount_id=subaccount_id)

    def get_trades(
        self,
        order_id: Optional[str] = None,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Get trade history.

        Args:
            order_id: Optional venue order ID to filter trades for a specific
                order. Must be a valid positive integer string up to 2^63-1.
            subaccount_id: Subaccount ID (defaults to active).

        Returns ``{"trades": [...], "hasMore": bool, "total": int}``.
        Each trade contains: tradeId, order (``{"venueId": str}``), symbol,
        side, price, quantity, realizedPnl, fee, feeRate, timestamp, maker,
        reduceOnly, markPrice, entryPrice, triggeredByLiquidation, direction,
        postOnly.
        """
        kwargs: Dict[str, Any] = {}
        if order_id:
            kwargs["orderId"] = order_id
        return self._action("getTrades", subaccount_id=subaccount_id, **kwargs)

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
        Each trade contains: tradeId, order (``{"venueId": str}``), symbol,
        orderType, side, price, quantity, realizedPnl, fee, feeRate, timestamp,
        maker, reduceOnly, markPrice, entryPrice, triggeredByLiquidation,
        direction, postOnly.
        """
        kwargs: Dict[str, Any] = {"positionId": position_id}
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        return self._action("getTradesForPosition", subaccount_id=subaccount_id, **kwargs)

    def get_portfolio(self, subaccount_id: Optional[int] = None) -> List[Dict]:
        """Get portfolio snapshots. Each entry has assets and timestamp."""
        return self._action("getPortfolio", subaccount_id=subaccount_id)

    def get_balance_updates(
        self,
        start_time: int = 0,
        end_time: int = 0,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Get balance change history.

        Args:
            start_time: Start timestamp in milliseconds (optional, Synthetix
                defaults to 7 days ago; max window is 365 days).
            end_time: End timestamp in milliseconds (optional, Synthetix
                defaults to now).
            subaccount_id: Subaccount ID (defaults to active).

        Returns ``{"balanceUpdates": [...]}``, each with: id, subAccountId,
        action, status, amount, collateral, timestamp, destinationAddress, txHash.
        """
        kwargs: Dict[str, Any] = {}
        if start_time:
            kwargs["startTime"] = start_time
        if end_time:
            kwargs["endTime"] = end_time
        return self._action("getBalanceUpdates", subaccount_id=subaccount_id, **kwargs)

    def get_transfers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get transfer history.

        Returns ``{"transfers": [...], "total": int}``, each with:
        transferId, from, to, symbol, amount, transferType, status, timestamp.
        """
        return self._action("getTransfers", subaccount_id=subaccount_id)

    def get_position_history(
        self,
        symbol: Optional[str] = None,
        start_time: int = 0,
        end_time: int = 0,
        limit: int = 0,
        offset: int = 0,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Get historical (closed) positions.

        Returns ``{"positions": [...], "hasMore": bool}``.
        """
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
        return self._action("getPositionHistory", subaccount_id=subaccount_id, **kwargs)

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
        kwargs: Dict[str, Any] = {}
        if period:
            kwargs["period"] = period
        return self._action("getPerformanceHistory", subaccount_id=subaccount_id, **kwargs)

    # ── Account Management ──────────────────────────────────────────

    def create_subaccount(self, name: Optional[str] = None) -> Dict:
        """Create a new subaccount (uses current subaccount as master)."""
        request = self._signer.sign_create_subaccount(
            self.subaccount_id, name=name or "", expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    def update_sub_account_name(self, name: str, subaccount_id: Optional[int] = None) -> Dict:
        """Rename a subaccount."""
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        request = self._signer.sign_update_sub_account_name(sid, name, expires_after_ms=self.expires_after_ms)
        return self._trade(request)

    def update_leverage(self, symbol: str, leverage: int, subaccount_id: Optional[int] = None) -> Dict:
        """Set leverage for a symbol."""
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        request = self._signer.sign_update_leverage(sid, symbol, str(leverage), expires_after_ms=self.expires_after_ms)
        return self._trade(request)

    def withdraw_collateral(
        self,
        amount: str,
        symbol: str = "USDC",
        destination: Optional[str] = None,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Withdraw collateral to destination address (defaults to wallet address)."""
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        dest = destination or self._signer.address
        request = self._signer.sign_withdraw_collateral(
            sid, symbol, amount, dest, expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    def transfer_collateral(
        self,
        amount: str,
        to_subaccount_id: int,
        symbol: str = "USDC",
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Transfer collateral between subaccounts."""
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        request = self._signer.sign_transfer_collateral(
            sid, to_subaccount_id, symbol, amount, expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    # ── Fees & Funding ──────────────────────────────────────────────

    def get_fees(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get fee structure.

        Returns ``{"feeTiers": [...], "userDailyVolume": str,
        "userFeeTier": {"symbol", "feeRate"}}``.
        """
        return self._action("getFees", subaccount_id=subaccount_id)

    def get_funding_payments(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get funding payment history.

        Returns ``{"summary": {"totalFundingReceived", "totalFundingPaid",
        "netFunding", "totalPayments", "averagePaymentSize"},
        "fundingHistory": [...]}``.
        """
        return self._action("getFundingPayments", subaccount_id=subaccount_id)

    def get_rate_limits(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get rate limit status. Returns ``{"requestsUsed": int, "requestsCap": int}``."""
        return self._action("getRateLimits", subaccount_id=subaccount_id)

    # ── Delegation ──────────────────────────────────────────────────

    def add_delegated_signer(
        self,
        delegate_address: str,
        subaccount_id: Optional[int] = None,
        permissions: Optional[List[str]] = None,
    ) -> Dict:
        """Add a delegated signer. permissions must contain exactly one value (e.g. ['session'])."""
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        request = self._signer.sign_add_delegated_signer(
            sid, delegate_address, permissions=permissions, expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    def get_delegated_signers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get list of delegated signers.

        Returns ``{"delegatedSigners": [{"subAccountId", "walletAddress",
        "permissions", "expiresAt"}]}``.
        """
        return self._action("getDelegatedSigners", subaccount_id=subaccount_id)

    def remove_delegated_signer(self, delegate_address: str, subaccount_id: Optional[int] = None) -> Dict:
        """Remove a delegated signer."""
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        request = self._signer.sign_remove_delegated_signer(
            sid, delegate_address, expires_after_ms=self.expires_after_ms
        )
        return self._trade(request)

    def remove_all_delegated_signers(self, subaccount_id: Optional[int] = None) -> Dict:
        """Remove all delegated signers."""
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        request = self._signer.sign_remove_all_delegated_signers(sid, expires_after_ms=self.expires_after_ms)
        return self._trade(request)

    def schedule_cancel(
        self,
        timeout_seconds: int,
        subaccount_id: Optional[int] = None,
    ) -> Dict:
        """Configure the dead-man switch (schedule cancel).

        When active, all open orders will be canceled if the server does not
        receive a heartbeat within ``timeout_seconds``. Pass ``0`` to disable.

        Args:
            timeout_seconds: Inactivity timeout in seconds. Use ``0`` to
                disable the dead-man switch.
            subaccount_id: Subaccount ID (defaults to active).

        Returns a dict with:
        - **isActive** — ``bool`` — whether the dead-man switch is armed
        - **message** — human-readable status message
        - **timeoutSeconds** — configured timeout
        - **triggerTime** — millisecond timestamp when it will fire, or ``null``
        """
        sid = subaccount_id if subaccount_id is not None else self.subaccount_id
        request = self._signer.sign_schedule_cancel(sid, timeout_seconds, expires_after_ms=self.expires_after_ms)
        return self._trade(request)

    def get_delegations_for_delegate(self, subaccount_id: Optional[int] = None) -> Dict:
        """Get delegations from the perspective of the delegate.

        Returns ``{"delegatedAccounts": [...]}``.
        """
        return self._action("getDelegationsForDelegate", subaccount_id=subaccount_id)

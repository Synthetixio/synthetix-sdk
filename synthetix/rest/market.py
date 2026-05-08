"""
Public market data endpoints.
No authentication required.
"""

from typing import Any, Dict, List

from synthetix.rest.api import API


class MarketAPI:
    """Public market data — no authentication required."""

    def __init__(self, api: API, ws_api: API) -> None:
        self._api = api
        self._ws_api = ws_api

    def _info(self, action: str, **params: Any) -> Any:
        return self._api.post("/info", {"params": {"action": action, **params}})

    def get_exchange_status_rest(self) -> Dict:
        """Get exchange operational status from the REST server.

        Returns a dict with:
        accepting_orders (bool), exchange_status (``"RUNNING"`` or
        ``"MAINTENANCE"``), code (present during maintenance, e.g.
        ``"SERVICE_DRAINING"``), message, timestamp_ms.
        """
        return self._api.get("/exchange/status")

    def get_exchange_status_ws(self) -> Dict:
        """Get exchange operational status from the WebSocket server.

        Returns a dict with the same shape as :meth:`get_exchange_status_rest`.
        """
        return self._ws_api.get("/exchange/status")

    def get_markets(self) -> List[Dict]:
        """Get all available markets and their configurations.

        Each market contains: symbol, description, baseAsset, quoteAsset,
        isOpen, isCloseOnly, priceIncrement, minOrderSize, orderSizeIncrement,
        contractSize, maxMarketOrderSize, maxLimitOrderSize, minNotionalValue,
        maintenanceMarginTiers, etc.
        """
        return self._info("getMarkets")

    def get_market_prices(self) -> Dict[str, Dict]:
        """Get current prices for all markets. Returns dict keyed by symbol.

        Each entry contains: symbol, bestBid, bestAsk, markPrice, indexPrice,
        lastPrice, prevDayPrice, volume24h, quoteVolume24h, fundingRate,
        openInterest, timestamp.
        """
        return self._info("getMarketPrices")

    def get_orderbook(self, symbol: str) -> Dict:
        """Get orderbook snapshot for a symbol.

        Returns ``{"bids": [[price, size], ...], "asks": [[price, size], ...]}``.
        """
        return self._info("getOrderbook", symbol=symbol)

    def get_last_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a symbol.

        Each trade contains: tradeId, symbol, side, price, quantity,
        timestamp, isMaker.
        """
        result = self._info("getLastTrades", symbol=symbol, limit=limit)
        if isinstance(result, dict) and "trades" in result:
            return result["trades"]
        return result

    def get_funding_rate(self, symbol: str) -> Dict:
        """Get current funding rate for a symbol.

        Returns a dict with: symbol, estimatedFundingRate, lastSettlementRate,
        lastSettlementTime, nextFundingTime, fundingInterval.
        """
        return self._info("getFundingRate", symbol=symbol)

    def get_funding_rate_history(
        self,
        symbol: str,
        start_time: int,
        end_time: int,
    ) -> Dict:
        """Get historical funding rates. Times are in milliseconds.

        ``start_time`` must satisfy the enforced-minimum floor —
        requests with a ``start_time`` that is too far in the past are
        rejected with a 400 error.

        Returns ``{"symbol": str, "fundingRates": [{"fundingRate",
        "fundingTime", "appliedAt"}]}``.
        """
        return self._info("getFundingRateHistory", symbol=symbol, startTime=start_time, endTime=end_time)

    def get_open_interest(self) -> List[Dict]:
        """Get open interest for all markets.

        Each entry contains: symbol, openInterest, longOpenInterest,
        shortOpenInterest, timestamp.
        """
        return self._info("getOpenInterest")

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
            interval: Timeframe — one of ``"1m"``, ``"5m"``, ``"15m"``,
                ``"30m"``, ``"1h"``, ``"4h"``, ``"8h"``, ``"12h"``,
                ``"1d"``, ``"3d"``, ``"1w"``, ``"1M"``, ``"3M"``.
            start_time: Start timestamp in milliseconds (optional).
            end_time: End timestamp in milliseconds (optional).
            limit: Max number of candles to return (optional).

        Returns ``{"symbol": str, "interval": str, "candles": [...]}``.
        Each candle contains: openTime, closeTime, openPrice, highPrice,
        lowPrice, closePrice, volume, quoteVolume, tradeCount.
        """
        kwargs: Dict[str, Any] = {"symbol": symbol, "interval": interval}
        if start_time:
            kwargs["startTime"] = start_time
        if end_time:
            kwargs["endTime"] = end_time
        if limit:
            kwargs["limit"] = limit
        return self._info("getCandles", **kwargs)

    def get_sub_account_ids(self, wallet_address: str) -> List[int]:
        """Get subaccount IDs for a wallet address. Returns a list of integer IDs."""
        return self._info("getSubAccountIds", walletAddress=wallet_address)

    def get_tiers(self) -> List[Dict]:
        """Get the exchange's fee/account tier configuration.

        Returns a list of tier dicts, each containing:
        tierId, tierType, tierName, minTradeVolume, makerFeeRate, takerFeeRate,
        maxSubAccounts, maxOrdersPerMarket, maxTotalOrders, maxBorrowCapacity.

        ``minTradeVolume``, ``makerFeeRate``, ``takerFeeRate``, and
        ``maxBorrowCapacity`` are decimal strings; ``maxSubAccounts``,
        ``maxOrdersPerMarket``, and ``maxTotalOrders`` are ints.
        """
        return self._info("getTiers")

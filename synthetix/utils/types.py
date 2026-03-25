"""
Type definitions for Synthetix V4 Python SDK
"""

from typing import Any, Callable, Dict, Literal, TypedDict

OrderSide = Literal["buy", "sell"]
OrderType = Literal["limitGtc", "limitIoc", "market", "triggerTp", "triggerSl"]
Grouping = Literal["na", "normalTpsl", "positionTpsl"]


class OrderRequest(TypedDict, total=False):
    symbol: str
    side: OrderSide
    orderType: OrderType
    price: str
    triggerPrice: str
    quantity: str
    reduceOnly: bool
    isTriggerMarket: bool
    clientOrderId: str
    closePosition: bool


class Signature(TypedDict):
    v: int
    r: str
    s: str


SubscriptionCallback = Callable[[Dict[str, Any]], None]

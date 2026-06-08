"""
Constants for Synthetix V4 Python SDK
EIP-712 types, URLs, and defaults
"""

# REST URLs
PROD_REST_URL = "https://papi.synthetix.io/v1"

# WebSocket URLs
PROD_WS_URL = "wss://papi.synthetix.io/v1/ws"

# Chain ID (always mainnet for EIP-712 domain)
CHAIN_ID = 1

# EIP-712 domain configuration
DOMAIN = {
    "name": "Synthetix",
    "version": "1",
    "chainId": CHAIN_ID,
    "verifyingContract": "0x0000000000000000000000000000000000000000",
}

# EIP-712 type definitions for WebSocket authentication
AUTH_MESSAGE_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "AuthMessage": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "timestamp", "type": "uint256"},
        {"name": "action", "type": "string"},
    ],
}

# EIP-712 type definitions for place orders messages
PLACE_ORDER_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "Order": [
        {"name": "symbol", "type": "string"},
        {"name": "side", "type": "string"},
        {"name": "orderType", "type": "string"},
        {"name": "price", "type": "string"},
        {"name": "triggerPrice", "type": "string"},
        {"name": "quantity", "type": "string"},
        {"name": "reduceOnly", "type": "bool"},
        {"name": "isTriggerMarket", "type": "bool"},
        {"name": "clientOrderId", "type": "string"},
        {"name": "closePosition", "type": "bool"},
    ],
    "PlaceOrders": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "orders", "type": "Order[]"},
        {"name": "grouping", "type": "string"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

# EIP-712 type definitions for cancel orders messages
CANCEL_ORDERS_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "CancelOrders": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "orderIds", "type": "uint256[]"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

# EIP-712 type definitions for generic subaccount actions (get* queries)
# When nonce > 0, the server includes nonce in the type (between action and expiresAfter)
SUBACCOUNT_ACTION_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "SubAccountAction": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "action", "type": "string"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

# EIP-712 domain fields (shared)
_EIP712_DOMAIN_FIELDS = [
    {"name": "name", "type": "string"},
    {"name": "version", "type": "string"},
    {"name": "chainId", "type": "uint256"},
    {"name": "verifyingContract", "type": "address"},
]

CANCEL_ORDERS_BY_CLOID_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "CancelOrdersByCloid": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "clientOrderIds", "type": "string[]"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

CANCEL_ALL_ORDERS_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "CancelAllOrders": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "symbols", "type": "string[]"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

MODIFY_ORDER_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "ModifyOrder": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "orderId", "type": "uint256"},
        {"name": "price", "type": "string"},
        {"name": "quantity", "type": "string"},
        {"name": "triggerPrice", "type": "string"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

UPDATE_LEVERAGE_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "UpdateLeverage": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "symbol", "type": "string"},
        {"name": "leverage", "type": "string"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

WITHDRAW_COLLATERAL_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "WithdrawCollateral": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "symbol", "type": "string"},
        {"name": "amount", "type": "string"},
        {"name": "destination", "type": "address"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

CREATE_SUBACCOUNT_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "CreateSubaccount": [
        {"name": "masterSubAccountId", "type": "uint256"},
        {"name": "name", "type": "string"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

TRANSFER_COLLATERAL_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "TransferCollateral": [
        {"name": "amount", "type": "string"},
        {"name": "expiresAfter", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
        {"name": "subAccountId", "type": "uint256"},
        {"name": "symbol", "type": "string"},
        {"name": "to", "type": "uint256"},
    ],
}

VOLUNTARY_COLLATERAL_EXCHANGE_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "VoluntaryCollateralExchange": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "sourceAsset", "type": "string"},
        {"name": "targetUSDTAmount", "type": "string"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

UPDATE_SUB_ACCOUNT_NAME_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "UpdateSubAccountName": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "name", "type": "string"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

REMOVE_ALL_DELEGATED_SIGNERS_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "RemoveAllDelegatedSigners": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

ADD_DELEGATED_SIGNER_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "AddDelegatedSigner": [
        {"name": "delegateAddress", "type": "address"},
        {"name": "subAccountId", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
        {"name": "expiresAt", "type": "uint256"},
        {"name": "permissions", "type": "string[]"},
    ],
}

REMOVE_DELEGATED_SIGNER_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "RemoveDelegatedSigner": [
        {"name": "delegateAddress", "type": "address"},
        {"name": "subAccountId", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

SCHEDULE_CANCEL_TYPES = {
    "EIP712Domain": _EIP712_DOMAIN_FIELDS,
    "ScheduleCancel": [
        {"name": "subAccountId", "type": "uint256"},
        {"name": "timeoutSeconds", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiresAfter", "type": "uint256"},
    ],
}

# Subscription types
SUBSCRIPTION_MARKET_PRICES = "marketPrices"
SUBSCRIPTION_ORDERBOOK = "orderbook"
SUBSCRIPTION_TRADES = "trades"
SUBSCRIPTION_SUBACCOUNT_UPDATES = "subAccountUpdates"

# Order sides
SIDE_BUY = "buy"
SIDE_SELL = "sell"

# Order types
ORDER_TYPE_LIMIT_GTC = "limitGtc"
ORDER_TYPE_LIMIT_IOC = "limitIoc"
ORDER_TYPE_LIMIT_GTD = "limitGtd"
ORDER_TYPE_MARKET = "market"
ORDER_TYPE_TRIGGER_TP = "triggerTp"
ORDER_TYPE_TRIGGER_SL = "triggerSl"
ORDER_TYPE_TWAP = "twap"

# Grouping types
GROUPING_NA = "na"
GROUPING_POSITION_TPSL = "positionTpsl"
GROUPING_TWAP = "twap"

# Request expiration (milliseconds from nonce)
DEFAULT_EXPIRES_AFTER_MS = 60000

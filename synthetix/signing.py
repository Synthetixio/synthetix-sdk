"""
EIP-712 signing for Synthetix V4 offchain trading API.
Consolidated from slp-manager's signer classes.
"""

import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from eth_account import Account
from eth_account.messages import encode_typed_data

from synthetix.utils.constants import (
    ADD_DELEGATED_SIGNER_TYPES,
    AUTH_MESSAGE_TYPES,
    CANCEL_ALL_ORDERS_TYPES,
    CANCEL_ORDERS_BY_CLOID_TYPES,
    CANCEL_ORDERS_TYPES,
    CREATE_SUBACCOUNT_TYPES,
    DEFAULT_EXPIRES_AFTER_MS,
    DOMAIN,
    MODIFY_ORDER_TYPES,
    PLACE_ORDER_TYPES,
    REMOVE_ALL_DELEGATED_SIGNERS_TYPES,
    REMOVE_DELEGATED_SIGNER_TYPES,
    SCHEDULE_CANCEL_TYPES,
    SUBACCOUNT_ACTION_TYPES,
    TRANSFER_COLLATERAL_TYPES,
    UPDATE_LEVERAGE_TYPES,
    UPDATE_SUB_ACCOUNT_NAME_TYPES,
    WITHDRAW_COLLATERAL_TYPES,
)


def generate_nonce() -> int:
    """Generate a nonce based on current timestamp in milliseconds."""
    return int(time.time() * 1000)


def generate_client_order_id() -> str:
    """Generate a random client order ID (0x + 32 hex chars)."""
    return "0x" + uuid.uuid4().hex[:32]


def format_order_for_eip712(order: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize an order dict for EIP-712 signing."""
    return {
        "symbol": str(order.get("symbol", "")),
        "side": str(order.get("side", "")),
        "orderType": str(order.get("orderType", "")),
        "price": str(order.get("price", "")),
        "triggerPrice": str(order.get("triggerPrice", "")),
        "quantity": str(order.get("quantity", "")),
        "reduceOnly": bool(order.get("reduceOnly", False)),
        "isTriggerMarket": bool(order.get("isTriggerMarket", False)),
        "clientOrderId": str(order.get("clientOrderId", "")),
        "closePosition": bool(order.get("closePosition", False)),
    }


def format_signature(sig: Dict[str, Any]) -> Dict[str, Any]:
    """Zero-pad r and s to 64 hex chars (32 bytes)."""
    v = sig["v"]
    r = sig["r"]
    s = sig["s"]

    if isinstance(r, int):
        r = "0x" + hex(r)[2:].zfill(64)
    elif isinstance(r, str):
        r_clean = r[2:] if r.startswith("0x") else r
        r = "0x" + r_clean.zfill(64)

    if isinstance(s, int):
        s = "0x" + hex(s)[2:].zfill(64)
    elif isinstance(s, str):
        s_clean = s[2:] if s.startswith("0x") else s
        s = "0x" + s_clean.zfill(64)

    return {"v": v, "r": r, "s": s}


class Signer:
    """Unified EIP-712 signer for all Synthetix operations."""

    def __init__(self, private_key: str) -> None:
        self._account = Account.from_key(private_key)
        self._last_nonce = 0
        self._nonce_lock = threading.Lock()

    @property
    def address(self) -> str:
        return self._account.address

    def _get_next_nonce(self) -> int:
        """Monotonically increasing nonce (thread-safe)."""
        with self._nonce_lock:
            nonce = generate_nonce()
            if nonce <= self._last_nonce:
                nonce = self._last_nonce + 1
            self._last_nonce = nonce
            return nonce

    def _sign_typed_data(self, types: Dict, primary_type: str, message: Dict) -> Dict[str, Any]:
        """Sign EIP-712 typed data. Returns {v, r, s}."""
        # Remove EIP712Domain — eth_account constructs it from the domain param
        types_without_domain = {k: v for k, v in types.items() if k != "EIP712Domain"}

        structured_data = {
            "types": types_without_domain,
            "primaryType": primary_type,
            "domain": DOMAIN,
            "message": message,
        }

        encoded = encode_typed_data(full_message=structured_data)
        signed = self._account.sign_message(encoded)

        return {
            "v": signed.v,
            "r": hex(signed.r),
            "s": hex(signed.s),
        }

    def _make_request(
        self,
        sig: Dict,
        nonce: int,
        expires_after: int,
        action: str,
        subaccount_id: int,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build the REST request envelope."""
        params: Dict[str, Any] = {
            "action": action,
            "subaccountId": str(subaccount_id),
            "walletAddress": self.address,
        }
        if extra_params:
            params.update(extra_params)

        return {
            "signature": format_signature(sig),
            "nonce": nonce,
            "expiresAfter": expires_after,
            "params": params,
        }

    def _nonce_and_expiry(self, nonce: Optional[int], expires_after_ms: int) -> tuple[int, int]:
        if nonce is None:
            nonce = self._get_next_nonce()
        return nonce, nonce + expires_after_ms

    # ── Auth (WebSocket) ────────────────────────────────────────────

    def sign_auth(self, subaccount_id: int) -> tuple[Dict[str, Any], str]:
        """
        Sign WebSocket authentication message.
        Returns (payload, signature_hex) for the auth request.
        """
        timestamp = int(generate_nonce() / 1000)  # seconds

        message = {
            "subAccountId": subaccount_id,
            "timestamp": timestamp,
            "action": "websocket_auth",
        }

        sig = self._sign_typed_data(AUTH_MESSAGE_TYPES, "AuthMessage", message)
        formatted = format_signature(sig)

        # Concatenate into single hex: 0x + r(64) + s(64) + v(2)
        r_hex = formatted["r"][2:]
        s_hex = formatted["s"][2:]
        v_hex = hex(formatted["v"])[2:].zfill(2)
        signature_hex = "0x" + r_hex + s_hex + v_hex

        payload = {
            "types": AUTH_MESSAGE_TYPES,
            "primaryType": "AuthMessage",
            "domain": {
                "name": DOMAIN["name"],
                "version": DOMAIN["version"],
                "chainId": DOMAIN["chainId"],
                "verifyingContract": DOMAIN["verifyingContract"],
            },
            "message": {
                "subAccountId": hex(subaccount_id),
                "timestamp": hex(timestamp),
                "action": "websocket_auth",
            },
        }

        return payload, signature_hex

    # ── Place Orders ────────────────────────────────────────────────

    def sign_place_orders(
        self,
        subaccount_id: int,
        orders: List[Dict[str, Any]],
        grouping: str = "na",
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a place orders request. Returns formatted REST request dict."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)
        formatted_orders = [format_order_for_eip712(o) for o in orders]

        message = {
            "subAccountId": subaccount_id,
            "orders": formatted_orders,
            "grouping": grouping,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(PLACE_ORDER_TYPES, "PlaceOrders", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "placeOrders",
            subaccount_id,
            {"orders": formatted_orders, "grouping": grouping},
        )

    # ── Cancel Orders ───────────────────────────────────────────────

    def sign_cancel_orders(
        self,
        subaccount_id: int,
        order_ids: List[int],
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a cancel orders request. Returns formatted REST request dict."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "orderIds": order_ids,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(CANCEL_ORDERS_TYPES, "CancelOrders", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "cancelOrders",
            subaccount_id,
            {"orderIds": [str(oid) for oid in order_ids]},
        )

    # ── Cancel Orders by Cloid ───────────────────────────────────────

    def sign_cancel_orders_by_cloid(
        self,
        subaccount_id: int,
        client_order_ids: List[str],
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a cancel orders by client order ID request. Returns formatted REST request dict."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "clientOrderIds": client_order_ids,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(CANCEL_ORDERS_BY_CLOID_TYPES, "CancelOrdersByCloid", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "cancelOrders",
            subaccount_id,
            {"clientOrderIds": client_order_ids},
        )

    # ── Cancel All Orders ──────────────────────────────────────────

    def sign_cancel_all_orders(
        self,
        subaccount_id: int,
        symbols: Optional[List[str]] = None,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a cancel-all-orders request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)
        symbol_list = symbols or []

        message = {
            "subAccountId": subaccount_id,
            "symbols": symbol_list,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(CANCEL_ALL_ORDERS_TYPES, "CancelAllOrders", message)

        extra: Dict[str, Any] = {}
        if symbols:
            extra["symbols"] = symbols
        return self._make_request(
            sig,
            nonce,
            expires_after,
            "cancelAllOrders",
            subaccount_id,
            extra,
        )

    # ── Modify Order ───────────────────────────────────────────────

    def sign_modify_order(
        self,
        subaccount_id: int,
        order_id: int,
        price: str = "",
        quantity: str = "",
        trigger_price: str = "",
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a modify-order request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "orderId": order_id,
            "price": price,
            "quantity": quantity,
            "triggerPrice": trigger_price,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(MODIFY_ORDER_TYPES, "ModifyOrder", message)

        extra: Dict[str, Any] = {"orderId": str(order_id)}
        if price:
            extra["price"] = price
        if quantity:
            extra["quantity"] = quantity
        if trigger_price:
            extra["triggerPrice"] = trigger_price
        return self._make_request(
            sig,
            nonce,
            expires_after,
            "modifyOrder",
            subaccount_id,
            extra,
        )

    # ── Update Leverage ────────────────────────────────────────────

    def sign_update_leverage(
        self,
        subaccount_id: int,
        symbol: str,
        leverage: str,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign an update-leverage request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "symbol": symbol,
            "leverage": leverage,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(UPDATE_LEVERAGE_TYPES, "UpdateLeverage", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "updateLeverage",
            subaccount_id,
            {"symbol": symbol, "leverage": leverage},
        )

    # ── Withdraw Collateral ────────────────────────────────────────

    def sign_withdraw_collateral(
        self,
        subaccount_id: int,
        symbol: str,
        amount: str,
        destination: str,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a withdraw-collateral request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "symbol": symbol,
            "amount": amount,
            "destination": destination,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(WITHDRAW_COLLATERAL_TYPES, "WithdrawCollateral", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "withdrawCollateral",
            subaccount_id,
            {"symbol": symbol, "amount": amount, "destination": destination},
        )

    # ── Create Subaccount ──────────────────────────────────────────

    def sign_create_subaccount(
        self,
        master_subaccount_id: int,
        name: str = "",
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a create-subaccount request (uses masterSubAccountId)."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "masterSubAccountId": master_subaccount_id,
            "name": name,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(CREATE_SUBACCOUNT_TYPES, "CreateSubaccount", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "createSubaccount",
            master_subaccount_id,
            {"name": name},
        )

    # ── Transfer Collateral ────────────────────────────────────────

    def sign_transfer_collateral(
        self,
        subaccount_id: int,
        to_subaccount_id: int,
        symbol: str,
        amount: str,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a transfer-collateral request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "amount": amount,
            "expiresAfter": expires_after,
            "nonce": nonce,
            "subAccountId": subaccount_id,
            "symbol": symbol,
            "to": to_subaccount_id,
        }

        sig = self._sign_typed_data(TRANSFER_COLLATERAL_TYPES, "TransferCollateral", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "transferCollateral",
            subaccount_id,
            {"symbol": symbol, "amount": amount, "to": str(to_subaccount_id)},
        )

    # ── Update Sub Account Name ────────────────────────────────────

    def sign_update_sub_account_name(
        self,
        subaccount_id: int,
        name: str,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign an update-sub-account-name request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "name": name,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(UPDATE_SUB_ACCOUNT_NAME_TYPES, "UpdateSubAccountName", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "updateSubAccountName",
            subaccount_id,
            {"name": name},
        )

    # ── Remove All Delegated Signers ───────────────────────────────

    def sign_remove_all_delegated_signers(
        self,
        subaccount_id: int,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a remove-all-delegated-signers request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(
            REMOVE_ALL_DELEGATED_SIGNERS_TYPES,
            "RemoveAllDelegatedSigners",
            message,
        )

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "removeAllDelegatedSigners",
            subaccount_id,
        )

    # ── Add Delegated Signer ──────────────────────────────────────

    def sign_add_delegated_signer(
        self,
        subaccount_id: int,
        delegate_address: str,
        permissions: Optional[List[str]] = None,
        expires_at: int = 0,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign an add-delegated-signer request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)
        perms = permissions or []

        message = {
            "delegateAddress": delegate_address,
            "subAccountId": subaccount_id,
            "nonce": nonce,
            "expiresAfter": expires_after,
            "expiresAt": expires_at,
            "permissions": perms,
        }

        sig = self._sign_typed_data(ADD_DELEGATED_SIGNER_TYPES, "AddDelegatedSigner", message)

        # addDelegatedSigner needs signer's walletAddress at the top level (for auth) while
        # params.walletAddress carries the delegate's address (what's being added).
        params: Dict[str, Any] = {
            "action": "addDelegatedSigner",
            "walletAddress": delegate_address,
            "expiresAt": expires_at,
        }
        if perms:
            params["permissions"] = perms
        return {
            "signature": format_signature(sig),
            "nonce": nonce,
            "expiresAfter": expires_after,
            "subaccountId": str(subaccount_id),
            "walletAddress": self.address,
            "params": params,
        }

    # ── Remove Delegated Signer ───────────────────────────────────

    def sign_remove_delegated_signer(
        self,
        subaccount_id: int,
        delegate_address: str,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a remove-delegated-signer request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "delegateAddress": delegate_address,
            "subAccountId": subaccount_id,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(REMOVE_DELEGATED_SIGNER_TYPES, "RemoveDelegatedSigner", message)

        # Same structure as addDelegatedSigner: signer's walletAddress at top level,
        # params.walletAddress carries the delegate address.
        return {
            "signature": format_signature(sig),
            "nonce": nonce,
            "expiresAfter": expires_after,
            "subaccountId": str(subaccount_id),
            "walletAddress": self.address,
            "params": {
                "action": "removeDelegatedSigner",
                "walletAddress": delegate_address,
            },
        }

    # ── Schedule Cancel (dead-man switch) ─────────────────────────

    def sign_schedule_cancel(
        self,
        subaccount_id: int,
        timeout_seconds: int,
        nonce: Optional[int] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a schedule-cancel (dead-man switch) request."""
        nonce, expires_after = self._nonce_and_expiry(nonce, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "timeoutSeconds": timeout_seconds,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(SCHEDULE_CANCEL_TYPES, "ScheduleCancel", message)

        return self._make_request(
            sig,
            nonce,
            expires_after,
            "scheduleCancel",
            subaccount_id,
            {"timeoutSeconds": timeout_seconds},
        )

    # ── Generic Subaccount Action (get* queries) ──────────────────

    def sign_action(
        self,
        subaccount_id: int,
        action: str,
        action_params: Optional[Dict[str, Any]] = None,
        expires_after_ms: int = DEFAULT_EXPIRES_AFTER_MS,
    ) -> Dict[str, Any]:
        """Sign a generic subaccount action (getPositions, getOpenOrders, etc.)."""
        nonce, expires_after = self._nonce_and_expiry(None, expires_after_ms)

        message = {
            "subAccountId": subaccount_id,
            "action": action,
            "nonce": nonce,
            "expiresAfter": expires_after,
        }

        sig = self._sign_typed_data(SUBACCOUNT_ACTION_TYPES, "SubAccountAction", message)

        extra = dict(action_params) if action_params else None
        return self._make_request(
            sig,
            nonce,
            expires_after,
            action,
            subaccount_id,
            extra,
        )

"""User Hub — real-time account, order, position, and trade updates via SignalR."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from signalrcore.hub_connection_builder import HubConnectionBuilder

from topstep.http import WS_USER_HUB

logger = logging.getLogger("topstep.realtime.user")

# Callback type: receives event data
UserCallback = Callable[..., None]


class UserHub:
    """Real-time user data via the ProjectX SignalR User Hub.

    Provides streaming account balance, order status, position, and trade updates.

    Usage::

        async with await TopstepClient.create(...) as client:
            client.user.on_order(my_order_handler)
            client.user.connect()
            client.user.subscribe_orders(account_id)
    """

    def __init__(self, token: str, hub_url: str = WS_USER_HUB) -> None:
        self._token = token
        self._hub_url = hub_url
        self._hub: Any = None
        self._subscriptions: list[tuple[str, list]] = []

        # User callbacks
        self._on_account: UserCallback | None = None
        self._on_order: UserCallback | None = None
        self._on_position: UserCallback | None = None
        self._on_trade: UserCallback | None = None
        self._on_open: Callable[[], None] | None = None
        self._on_close: Callable[[], None] | None = None

    def on_account(self, callback: UserCallback) -> None:
        """Register a handler for GatewayUserAccount events."""
        self._on_account = callback

    def on_order(self, callback: UserCallback) -> None:
        """Register a handler for GatewayUserOrder events."""
        self._on_order = callback

    def on_position(self, callback: UserCallback) -> None:
        """Register a handler for GatewayUserPosition events."""
        self._on_position = callback

    def on_trade(self, callback: UserCallback) -> None:
        """Register a handler for GatewayUserTrade events."""
        self._on_trade = callback

    def on_open(self, callback: Callable[[], None]) -> None:
        """Register a handler called when the WebSocket connection opens."""
        self._on_open = callback

    def on_close(self, callback: Callable[[], None]) -> None:
        """Register a handler called when the WebSocket connection closes."""
        self._on_close = callback

    def connect(self) -> None:
        """Build and start the SignalR connection.

        This is a blocking call — the connection runs in a background thread
        managed by signalrcore. Call ``stop()`` to disconnect.
        """
        url = f"{self._hub_url}?access_token={self._token}"

        self._hub = (
            HubConnectionBuilder()
            .with_url(url, options={
                "transport": "websockets",
                "skip_negotiation": True,
                "verify_ssl": True,
            })
            .configure_logging(logging.WARNING)
            .build()
        )

        # Wire up SignalR events to user callbacks
        self._hub.on("GatewayUserAccount", self._handle_account)
        self._hub.on("GatewayUserOrder", self._handle_order)
        self._hub.on("GatewayUserPosition", self._handle_position)
        self._hub.on("GatewayUserTrade", self._handle_trade)

        self._hub.on_open(self._handle_open)
        self._hub.on_close(self._handle_close)

        logger.info("Connecting to User Hub...")
        self._hub.start()

    def stop(self) -> None:
        """Disconnect from the User Hub."""
        if self._hub is not None:
            self._hub.stop()
            self._hub = None
            self._subscriptions.clear()
            logger.info("User Hub disconnected")

    # --- Subscription management ---

    def subscribe_accounts(self) -> None:
        """Subscribe to real-time account balance updates."""
        self._send("SubscribeAccounts", [])

    def unsubscribe_accounts(self) -> None:
        """Unsubscribe from account updates."""
        self._send("UnsubscribeAccounts", [])

    def subscribe_orders(self, account_id: int) -> None:
        """Subscribe to real-time order updates for an account."""
        self._send("SubscribeOrders", [account_id])

    def unsubscribe_orders(self, account_id: int) -> None:
        """Unsubscribe from order updates."""
        self._send("UnsubscribeOrders", [account_id])

    def subscribe_positions(self, account_id: int) -> None:
        """Subscribe to real-time position updates for an account."""
        self._send("SubscribePositions", [account_id])

    def unsubscribe_positions(self, account_id: int) -> None:
        """Unsubscribe from position updates."""
        self._send("UnsubscribePositions", [account_id])

    def subscribe_trades(self, account_id: int) -> None:
        """Subscribe to real-time trade updates for an account."""
        self._send("SubscribeTrades", [account_id])

    def unsubscribe_trades(self, account_id: int) -> None:
        """Unsubscribe from trade updates."""
        self._send("UnsubscribeTrades", [account_id])

    def subscribe_all(self, account_id: int) -> None:
        """Subscribe to accounts, orders, positions, and trades."""
        self.subscribe_accounts()
        self.subscribe_orders(account_id)
        self.subscribe_positions(account_id)
        self.subscribe_trades(account_id)

    def unsubscribe_all(self, account_id: int) -> None:
        """Unsubscribe from all user streams."""
        self.unsubscribe_accounts()
        self.unsubscribe_orders(account_id)
        self.unsubscribe_positions(account_id)
        self.unsubscribe_trades(account_id)

    # --- Internal handlers ---

    def _send(self, method: str, args: list) -> None:
        if self._hub is None:
            raise RuntimeError("Not connected — call connect() first")
        self._hub.send(method, args)
        self._subscriptions.append((method, args))
        logger.debug("Sent %s(%s)", method, args)

    def _handle_account(self, *args: Any) -> None:
        if self._on_account:
            self._on_account(*args)

    def _handle_order(self, *args: Any) -> None:
        if self._on_order:
            self._on_order(*args)

    def _handle_position(self, *args: Any) -> None:
        if self._on_position:
            self._on_position(*args)

    def _handle_trade(self, *args: Any) -> None:
        if self._on_trade:
            self._on_trade(*args)

    def _handle_open(self) -> None:
        logger.info("User Hub connected")
        if self._on_open:
            self._on_open()

    def _handle_close(self) -> None:
        logger.info("User Hub disconnected")
        if self._on_close:
            self._on_close()

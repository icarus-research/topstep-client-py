"""User Hub — real-time account, order, position, and trade updates via SignalR."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any

from signalrcore.hub_connection_builder import HubConnectionBuilder

from topstep.http import WS_USER_HUB

logger = logging.getLogger("topstep.realtime.user")

# Callback type: receives event data
UserCallback = Callable[..., Any]


class UserHub:
    """Real-time user data via the ProjectX SignalR User Hub.

    Provides streaming account balance, order status, position, and trade updates.

    Usage::

        async with await TopstepClient.create(...) as client:
            client.user.on_order(my_order_handler)
            await client.user.connect()
            await client.user.subscribe_orders(account_id)
    """

    def __init__(self, token: str, hub_url: str = WS_USER_HUB) -> None:
        self._token = token
        self._hub_url = hub_url
        self._hub: Any = None
        self._subscriptions: set[tuple[str, tuple[Any, ...]]] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connected = False

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

    def set_token(self, token: str) -> None:
        """Update the auth token used for future connections."""
        self._token = token

    async def connect(self) -> None:
        """Build and start the SignalR connection without blocking the event loop.

        SignalR itself runs its own background thread. This method only waits
        for the initial connection startup to complete.
        """
        if self._connected:
            return

        self._loop = asyncio.get_running_loop()
        self._hub = (
            HubConnectionBuilder()
            .with_url(self._hub_url, options={
                "access_token_factory": lambda: self._token,
                "verify_ssl": True,
            })
            .configure_logging(logging.WARNING)
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 0,
            })
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
        try:
            await asyncio.to_thread(self._hub.start)
        except Exception:
            self._hub = None
            self._connected = False
            raise

        self._connected = True

    async def stop(self) -> None:
        """Disconnect from the User Hub."""
        if self._hub is not None:
            try:
                await asyncio.to_thread(self._hub.stop)
            finally:
                self._hub = None
                self._subscriptions.clear()
                self._connected = False
                logger.info("User Hub disconnected")

    # --- Subscription management ---

    async def subscribe_accounts(self) -> None:
        """Subscribe to real-time account balance updates."""
        await self._send("SubscribeAccounts", [])
        self._subscriptions.add(("SubscribeAccounts", ()))

    async def unsubscribe_accounts(self) -> None:
        """Unsubscribe from account updates."""
        await self._send("UnsubscribeAccounts", [])
        self._subscriptions.discard(("SubscribeAccounts", ()))

    async def subscribe_orders(self, account_id: int) -> None:
        """Subscribe to real-time order updates for an account."""
        await self._send("SubscribeOrders", [account_id])
        self._subscriptions.add(("SubscribeOrders", (account_id,)))

    async def unsubscribe_orders(self, account_id: int) -> None:
        """Unsubscribe from order updates."""
        await self._send("UnsubscribeOrders", [account_id])
        self._subscriptions.discard(("SubscribeOrders", (account_id,)))

    async def subscribe_positions(self, account_id: int) -> None:
        """Subscribe to real-time position updates for an account."""
        await self._send("SubscribePositions", [account_id])
        self._subscriptions.add(("SubscribePositions", (account_id,)))

    async def unsubscribe_positions(self, account_id: int) -> None:
        """Unsubscribe from position updates."""
        await self._send("UnsubscribePositions", [account_id])
        self._subscriptions.discard(("SubscribePositions", (account_id,)))

    async def subscribe_trades(self, account_id: int) -> None:
        """Subscribe to real-time trade updates for an account."""
        await self._send("SubscribeTrades", [account_id])
        self._subscriptions.add(("SubscribeTrades", (account_id,)))

    async def unsubscribe_trades(self, account_id: int) -> None:
        """Unsubscribe from trade updates."""
        await self._send("UnsubscribeTrades", [account_id])
        self._subscriptions.discard(("SubscribeTrades", (account_id,)))

    async def subscribe_all(self, account_id: int) -> None:
        """Subscribe to accounts, orders, positions, and trades."""
        await self.subscribe_accounts()
        await self.subscribe_orders(account_id)
        await self.subscribe_positions(account_id)
        await self.subscribe_trades(account_id)

    async def unsubscribe_all(self, account_id: int) -> None:
        """Unsubscribe from all user streams."""
        await self.unsubscribe_accounts()
        await self.unsubscribe_orders(account_id)
        await self.unsubscribe_positions(account_id)
        await self.unsubscribe_trades(account_id)

    # --- Internal handlers ---

    async def _send(self, method: str, args: list) -> None:
        if self._hub is None:
            raise RuntimeError("Not connected — call connect() first")
        await asyncio.to_thread(self._hub.send, method, args)
        logger.debug("Sent %s(%s)", method, args)

    async def _restore_subscriptions(self) -> None:
        if self._hub is None:
            return

        for method, args in sorted(self._subscriptions):
            await asyncio.to_thread(self._hub.send, method, list(args))
            logger.debug("Restored %s(%s)", method, args)

    def _dispatch_callback(self, callback: Callable[..., Any] | None, *args: Any) -> None:
        if callback is None:
            return

        loop = self._loop
        if loop is None or loop.is_closed():
            logger.warning("Dropping realtime callback because no active event loop is available")
            return

        def runner() -> None:
            try:
                result = callback(*args)
                if inspect.isawaitable(result):
                    task = loop.create_task(result)
                    task.add_done_callback(self._log_task_error)
            except Exception:
                logger.exception("Unhandled exception in user callback")

        loop.call_soon_threadsafe(runner)

    def _log_task_error(self, task: asyncio.Task[Any]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Unhandled exception in async user callback")

    def _handle_account(self, *args: Any) -> None:
        self._dispatch_callback(self._on_account, *args)

    def _handle_order(self, *args: Any) -> None:
        self._dispatch_callback(self._on_order, *args)

    def _handle_position(self, *args: Any) -> None:
        self._dispatch_callback(self._on_position, *args)

    def _handle_trade(self, *args: Any) -> None:
        self._dispatch_callback(self._on_trade, *args)

    def _handle_open(self) -> None:
        logger.info("User Hub connected")
        if self._subscriptions and self._loop is not None and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(
                lambda: self._loop.create_task(self._restore_subscriptions())
            )
        self._dispatch_callback(self._on_open)

    def _handle_close(self) -> None:
        logger.info("User Hub disconnected")
        self._connected = False
        self._dispatch_callback(self._on_close)

from __future__ import annotations

from datetime import datetime
from typing import Optional

from topstep.http import HTTPClient
from topstep.models.order import Order, PlaceOrderRequest


class OrdersEndpoint:
    """Operations on orders."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    async def place(self, order: PlaceOrderRequest) -> int:
        """Place a new order. Returns the order ID."""
        data = await self._http.post("/api/Order/place", order.to_api_dict())
        return data["orderId"]

    async def modify(
        self,
        account_id: int,
        order_id: int,
        size: Optional[int] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail_price: Optional[float] = None,
    ) -> None:
        """Modify an open order."""
        payload: dict = {
            "accountId": account_id,
            "orderId": order_id,
        }
        if size is not None:
            payload["size"] = size
        if limit_price is not None:
            payload["limitPrice"] = limit_price
        if stop_price is not None:
            payload["stopPrice"] = stop_price
        if trail_price is not None:
            payload["trailPrice"] = trail_price

        await self._http.post("/api/Order/modify", payload)

    async def cancel(self, account_id: int, order_id: int) -> None:
        """Cancel an open order."""
        await self._http.post("/api/Order/cancel", {
            "accountId": account_id,
            "orderId": order_id,
        })

    async def search(
        self,
        account_id: int,
        start: datetime,
        end: Optional[datetime] = None,
    ) -> list[Order]:
        """Search orders by time range."""
        payload: dict = {
            "accountId": account_id,
            "startTimestamp": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if end is not None:
            payload["endTimestamp"] = end.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = await self._http.post("/api/Order/search", payload)
        return [Order.model_validate(o) for o in data.get("orders", [])]

    async def search_open(self, account_id: int) -> list[Order]:
        """Get all currently open orders for an account."""
        data = await self._http.post("/api/Order/searchOpen", {
            "accountId": account_id,
        })
        return [Order.model_validate(o) for o in data.get("orders", [])]

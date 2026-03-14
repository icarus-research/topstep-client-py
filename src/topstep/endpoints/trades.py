from __future__ import annotations

from datetime import datetime
from typing import Optional

from topstep.http import HTTPClient
from topstep.models.trade import Trade


class TradesEndpoint:
    """Operations on trade history."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def search(
        self,
        account_id: int,
        start: datetime,
        end: Optional[datetime] = None,
    ) -> list[Trade]:
        """Search trades by time range."""
        payload: dict = {
            "accountId": account_id,
            "startTimestamp": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if end is not None:
            payload["endTimestamp"] = end.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = self._http.post("/api/Trade/search", payload)
        return [Trade.model_validate(t) for t in data.get("trades", [])]

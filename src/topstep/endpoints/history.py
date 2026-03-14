from __future__ import annotations

from datetime import datetime

from topstep.http import HTTPClient
from topstep.models.bar import Bar, BarUnit


class HistoryEndpoint:
    """Historical market data."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def retrieve_bars(
        self,
        contract_id: str,
        start: datetime,
        end: datetime,
        unit: BarUnit = BarUnit.MINUTE,
        unit_number: int = 1,
        limit: int = 20000,
        include_partial_bar: bool = False,
    ) -> list[Bar]:
        """Retrieve historical OHLCV bars.

        Args:
            contract_id: The contract to fetch bars for.
            start: Start of the time range (UTC).
            end: End of the time range (UTC).
            unit: Bar timeframe unit (second, minute, hour, etc.).
            unit_number: Number of units per bar (e.g. 5 for 5-minute bars).
            limit: Maximum number of bars to return (API max: 20000).
            include_partial_bar: Whether to include the current incomplete bar.

        Rate limit: 50 requests per 30 seconds.
        """
        data = self._http.post("/api/History/retrieveBars", {
            "contractId": contract_id,
            "live": False,
            "startTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "unit": int(unit),
            "unitNumber": unit_number,
            "limit": limit,
            "includePartialBar": include_partial_bar,
        })
        return [Bar.model_validate(b) for b in data.get("bars", [])]

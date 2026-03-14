from __future__ import annotations

from topstep.http import HTTPClient
from topstep.models.position import Position


class PositionsEndpoint:
    """Operations on positions."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def search_open(self, account_id: int) -> list[Position]:
        """Get all open positions for an account."""
        data = self._http.post("/api/Position/searchOpen", {
            "accountId": account_id,
        })
        return [Position.model_validate(p) for p in data.get("positions", [])]

    def close(self, account_id: int, contract_id: str) -> None:
        """Close all positions for a contract."""
        self._http.post("/api/Position/closeContract", {
            "accountId": account_id,
            "contractId": contract_id,
        })

    def partial_close(self, account_id: int, contract_id: str, size: int) -> None:
        """Partially close a position (specify number of contracts to close)."""
        self._http.post("/api/Position/partialCloseContract", {
            "accountId": account_id,
            "contractId": contract_id,
            "size": size,
        })

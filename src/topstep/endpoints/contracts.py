from __future__ import annotations

from topstep.http import HTTPClient
from topstep.models.contract import Contract


class ContractsEndpoint:
    """Operations on futures contracts."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    async def available(self, live: bool = False) -> list[Contract]:
        """List all available contracts."""
        data = await self._http.post("/api/Contract/available", {"live": live})
        return [Contract.model_validate(c) for c in data.get("contracts", [])]

    async def search(self, text: str, live: bool = False) -> list[Contract]:
        """Search contracts by name/description (max 20 results)."""
        data = await self._http.post("/api/Contract/search", {
            "searchText": text,
            "live": live,
        })
        return [Contract.model_validate(c) for c in data.get("contracts", [])]

    async def search_by_id(self, contract_id: str) -> Contract:
        """Look up a single contract by its ID."""
        data = await self._http.post("/api/Contract/searchById", {
            "contractId": contract_id,
        })
        return Contract.model_validate(data["contract"])

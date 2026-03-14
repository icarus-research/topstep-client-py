from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, Field


class PositionType(IntEnum):
    UNDEFINED = 0
    LONG = 1
    SHORT = 2


class Position(BaseModel):
    """An open position."""

    model_config = {"populate_by_name": True}

    id: int
    account_id: int = Field(alias="accountId")
    contract_id: str = Field(alias="contractId")
    creation_timestamp: datetime = Field(alias="creationTimestamp")
    type: PositionType
    size: int
    average_price: float = Field(alias="averagePrice")

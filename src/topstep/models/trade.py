from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Trade(BaseModel):
    """A trade execution."""

    model_config = {"populate_by_name": True}

    id: int
    account_id: int = Field(alias="accountId")
    contract_id: str = Field(alias="contractId")
    creation_timestamp: datetime = Field(alias="creationTimestamp")
    price: float
    profit_and_loss: Optional[float] = Field(None, alias="profitAndLoss")
    fees: float
    side: int
    size: int
    voided: bool
    order_id: int = Field(alias="orderId")

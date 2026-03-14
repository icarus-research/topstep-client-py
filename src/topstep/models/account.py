from pydantic import BaseModel, Field


class Account(BaseModel):
    """A TopstepX trading account."""

    model_config = {"populate_by_name": True}

    id: int
    name: str
    balance: float
    can_trade: bool = Field(alias="canTrade")
    is_visible: bool = Field(alias="isVisible")

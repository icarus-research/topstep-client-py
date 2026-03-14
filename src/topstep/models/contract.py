from pydantic import BaseModel, Field


class Contract(BaseModel):
    """A tradeable futures contract."""

    model_config = {"populate_by_name": True}

    id: str
    name: str
    description: str
    tick_size: float = Field(alias="tickSize")
    tick_value: float = Field(alias="tickValue")
    active_contract: bool = Field(alias="activeContract")
    symbol_id: str = Field(alias="symbolId")

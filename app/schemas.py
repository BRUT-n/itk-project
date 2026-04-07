from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WalletResponse(BaseModel):
    id: UUID
    balance: Decimal = Field(max_digits=20, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)


class OperationType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

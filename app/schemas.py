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


class WalletOperation(BaseModel):
    operation_type: OperationType = Field(
        description="Тип операции: DEPOSIT (пополнение) или WITHDRAW (списание)"
    )
    amount: Decimal = Field(gt=0, examples=[1000])

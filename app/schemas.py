from decimal import Decimal
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

class WalletResponse(BaseModel):
    id: UUID
    balance: Decimal = Field(max_digits=20, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)# проверить можно ли убрать


class OperationType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperation(BaseModel):
    operation_type: OperationType = Field(
        description="Тип операции: DEPOSIT (пополнение) или WITHDRAW (списание)"
    )
    amount: Decimal = Field(gt=0, examples=[1000])


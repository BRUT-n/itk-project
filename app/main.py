from contextlib import asynccontextmanager
from decimal import Decimal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import engine, get_db
from app.models import Base, Wallet
from app.schemas import OperationType, WalletResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(title="Wallet FastAPI", lifespan=lifespan)


async def validate_wallet_exists(wallet_uuid: UUID, session: AsyncSession) -> Wallet:
    wallet = await crud.get_wallet_by_id(wallet_id=wallet_uuid, session=session)
    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"
        )

    return wallet


@app.get(
    "/api/v1/wallets/{wallet_uuid}",
    tags=["Кошелек"],
    summary="Вывести текущий баланс",
    status_code=status.HTTP_200_OK,
    response_model=WalletResponse,
)
async def get_balance_endpoint(
    wallet_uuid: UUID,
    session: AsyncSession = Depends(get_db),
):
    wallet = await validate_wallet_exists(wallet_uuid=wallet_uuid, session=session)

    return wallet


@app.post(
    "/api/v1/wallets/{wallet_uuid}/operation",
    tags=["Кошелек"],
    summary="Провести операцию (DEPOSIT/WITHDRAW)",
    status_code=status.HTTP_200_OK,
    response_model=WalletResponse,
)
async def wallet_operation_endpoint(
    wallet_uuid: UUID,
    operation: OperationType,
    amount: Decimal = Query(gt=0, examples=[1000]),
    session: AsyncSession = Depends(get_db),
):
    wallet = await validate_wallet_exists(wallet_uuid=wallet_uuid, session=session)

    result = await crud.wallet_operation(
        operation=operation,
        amount=amount,
        wallet=wallet,
        session=session,
    )

    if result is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds"
        )
    return result

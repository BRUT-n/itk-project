from contextlib import asynccontextmanager
from decimal import Decimal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import engine, get_db
from app.models import Base, Wallet
from app.schemas import OperationType, WalletResponse


# 1. Описываем логику "Жизненного цикла"
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код здесь выполнится ПРИ СТАРТЕ
    async with engine.begin() as conn:
        # Создаем таблицы, если их нет
        await conn.run_sync(Base.metadata.create_all)

    yield  # В этот момент приложение работает и принимает запросы

    # Код здесь выполнится ПРИ ВЫКЛЮЧЕНИИ (например, закрытие пула БД)
    await engine.dispose()


# 2. Передаем lifespan в инициализацию FastAPI
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
    # response_model=WalletResponse, # если обрать функцию гет можно юзать ответ этот
)
async def get_balance_endpoint(
    wallet_uuid: UUID,
    session: AsyncSession = Depends(get_db),
):

    wallet = await validate_wallet_exists(wallet_uuid=wallet_uuid, session=session)

    return wallet  # НЕОБХОДИМО ПРОВЕРИТЬ ВЫВОД В СВАГЕРЕ


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
    async with session.begin():
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


# ОТЛАДКА
@app.get(
    "/api/v1/wallets",
    tags=["Кошелек"],
    summary="Посмотреть все кошельки в БД",
    response_model=list[WalletResponse],
)
async def list_wallets(session: AsyncSession = Depends(get_db)):
    wallets = await crud.get_all_wallets(session=session)
    return wallets


# ОТЛАДКА
@app.post("/api/v1/wallets", tags=["Кошелек"], summary="Создать новый кошелек")
async def create_new_wallet(session: AsyncSession = Depends(get_db)):
    new_wallet = Wallet()  # Создаем объект (ID и баланс подставятся автоматом)
    session.add(new_wallet)
    await session.commit()
    await session.refresh(new_wallet)
    return new_wallet

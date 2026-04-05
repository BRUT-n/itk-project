from decimal import Decimal
from os import login_tty
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models import Wallet
from app.schemas import OperationType, WalletOperation, WalletResponse
import logging

logger = logging.getLogger(__name__)


async def get_wallet_by_id(
    wallet_id: UUID,
    session: AsyncSession
)-> Wallet | None:
    query = select(Wallet).where(Wallet.id==wallet_id).with_for_update()
    result = await session.execute(query)
    return result.scalar_one_or_none()

# async def get_balance(
#     wallet_uuid: UUID,
#     session: AsyncSession
# ) -> Decimal | None:
#     wallet = await get_wallet_by_id(wallet_id=wallet_uuid, session=session)

#     if not wallet:
#         return None

#     return wallet.balance


async def wallet_operation(
    operation: OperationType,
    amount: Decimal,
    wallet: Wallet,
    session: AsyncSession,
):
    if operation == OperationType.DEPOSIT:
        wallet.balance += amount

    elif operation == OperationType.WITHDRAW:
        if wallet.balance < amount:
            return False
        wallet.balance -= amount

    try:
        await session.commit()
        await session.refresh(wallet)
    # ошибка алхимии (базовый класс алхимической ошибки)
    except Exception as e:
        await session.rollback()
        logging.error(f"Database error: {e}")
        raise
    
    return wallet

# ОТЛАДКА
async def get_all_wallets(session: AsyncSession):
    """Получить список всех кошельков из базы"""
    query = select(Wallet)
    result = await session.execute(query)
    return result.scalars().all() # .scalars().all() превращает результат в список объектов Wallet


import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet
from app.schemas import OperationType

logger = logging.getLogger(__name__)


async def get_wallet_by_id(wallet_id: UUID, session: AsyncSession) -> Wallet | None:
    query = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
    result = await session.execute(query)
    return result.scalar_one_or_none()


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
    except SQLAlchemyError as e:
        await session.rollback()
        logging.error(f"Database error: {e}")
        raise

    return wallet


# ОТЛАДКА
async def get_all_wallets(session: AsyncSession):
    """Получить список всех кошельков из базы"""
    query = select(Wallet)
    result = await session.execute(query)
    return (
        result.scalars().all()
    )

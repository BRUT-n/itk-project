import pytest
import asyncio
from uuid import uuid4
from app.models import Wallet

@pytest.mark.anyio
async def test_deposit_operation(client, db_session):
    # 1. Подготовка: создаем кошелек в тестовой базе
    wallet_id = uuid4()
    new_wallet = Wallet(id=wallet_id, balance=1000.00)
    db_session.add(new_wallet)
    await db_session.commit()

    # 2. Действие: отправляем запрос на пополнение
    payload = {
        "operation_type": "DEPOSIT",
        "amount": 500
    }
    response = await client.post(f"/api/v1/wallets/{wallet_id}/operation", json=payload)

    # 3. Проверка
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(wallet_id)
    assert data["balance"] == "1500.00" # Decimal обычно возвращается строкой или числом в JSON

@pytest.mark.anyio
async def test_withdraw_insufficient_funds(client, db_session):
    # 1. Готовим кошелек с небольшой суммой
    wallet_id = uuid4()
    new_wallet = Wallet(id=wallet_id, balance=100.00)
    db_session.add(new_wallet)
    await db_session.commit()

    # 2. Пытаемся снять больше, чем есть
    payload = {
        "operation_type": "WITHDRAW",
        "amount": 500.00
    }
    response = await client.post(f"/api/v1/wallets/{wallet_id}/operation", json=payload)

    # 3. Проверяем, что API нам отказало
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"


@pytest.mark.asyncio
async def test_concurrent_withdrawals(client, db_session):
    # 1. Создаем кошелек с 1000 рублями
    wallet_id = uuid4()
    new_wallet = Wallet(id=wallet_id, balance=1000.00)
    db_session.add(new_wallet)
    await db_session.commit()

    # 2. Готовим 5 одинаковых запросов на списание по 200
    payload = {"operation_type": "WITHDRAW", "amount": 200.00}
    tasks = [
        client.post(f"/api/v1/wallets/{wallet_id}/operation", json=payload)
        for _ in range(5)
    ]

    # 3. Запускаем их ОДНОВРЕМЕННО
    responses = await asyncio.gather(*tasks)

    # 4. Проверяем результаты
    for resp in responses:
        assert resp.status_code == 200

    # 5. Проверяем финальный баланс
    final_resp = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert final_resp.json()["balance"] == "0.00"


import asyncio
from uuid import uuid4

import pytest

from app.models import Wallet


async def test_deposit_operation(client, db_session):
    wallet_id = uuid4()
    new_wallet = Wallet(id=wallet_id, balance=1000.00)
    db_session.add(new_wallet)
    await db_session.commit()

    payload = {"operation": "DEPOSIT", "amount": 500}
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        params=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(wallet_id)
    assert data["balance"] == "1500.00"

async def test_withdraw_insufficient_funds(client, db_session):
    wallet_id = uuid4()
    new_wallet = Wallet(id=wallet_id, balance=100.00)
    db_session.add(new_wallet)
    await db_session.commit()

    payload = {"operation": "WITHDRAW", "amount": 500.00}
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        params=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"


async def test_concurrent_withdrawals(client, db_session):
    wallet_id = uuid4()
    new_wallet = Wallet(id=wallet_id, balance=1000.00)
    db_session.add(new_wallet)
    await db_session.commit()

    payload = {"operation": "WITHDRAW", "amount": 200.00}
    tasks = [
        client.post(f"/api/v1/wallets/{wallet_id}/operation", params=payload)
        for _ in range(5)
    ]

    responses = await asyncio.gather(*tasks)

    for resp in responses:
        assert resp.status_code == 200

    final_resp = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert final_resp.json()["balance"] == "0.00"


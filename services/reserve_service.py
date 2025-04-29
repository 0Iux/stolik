from asyncpg import UniqueViolationError
from datetime import time
from fastapi import HTTPException
from db.database import get_db_pool
from schemas.reserve import ReserveCreate
from services.restoraunt_service import get_restoraunt_by_id

from datetime import time
from fastapi import HTTPException
from db.database import get_db_pool
from schemas.reserve import ReserveCreate
from services.restoraunt_service import get_restoraunt_by_id

async def create_reserve(user_id: int, data: ReserveCreate):
    pool = get_db_pool()

    # Получаем ресторан
    restoraunt = await get_restoraunt_by_id(data.restoraunt_id)
    if not restoraunt:
        raise HTTPException(status_code=404, detail="Ресторан не найден")

    start_time = data.date_start.time()
    end_time = data.date_end.time()

    if not (restoraunt["open_time"] <= start_time < end_time <= restoraunt["close_time"]):
        raise HTTPException(
            status_code=400,
            detail=f"Время брони должно быть в пределах работы ресторана: {restoraunt['open_time']} – {restoraunt['close_time']}"
        )

    async with pool.acquire() as conn:
        # Проверка на пересечение с другими активными бронями
        conflict = await conn.fetchrow(
            """
            SELECT id FROM reserves
            WHERE restoraunt_id = $1
              AND status NOT IN ('cancelled', 'completed')
              AND ($2, $3) OVERLAPS (date_start, date_end)
            """,
            data.restoraunt_id,
            data.date_start,
            data.date_end
        )
        if conflict:
            raise HTTPException(status_code=409, detail="На выбранное время уже есть бронь")

        # Проверка: есть ли у пользователя бронь в это же время
        user_conflict = await conn.fetchrow(
            """
            SELECT id FROM reserves
            WHERE user_id = $1
              AND status NOT IN ('cancelled', 'completed')
              AND ($2, $3) OVERLAPS (date_start, date_end)
            """,
            user_id,
            data.date_start,
            data.date_end
        )
        if user_conflict:
            raise HTTPException(status_code=409, detail="У вас уже есть активная бронь на это время")

        # Проверка скидки
        discount = await conn.fetchrow(
            """
            SELECT discount_percent FROM discounts
            WHERE restoraunt_id = $1
              AND LOWER(day_of_week) = LOWER(to_char($2, 'Day'))
              AND $3::time >= hour_start
              AND $4::time <= hour_end
            LIMIT 1
            """,
            data.restoraunt_id,
            data.date_start,
            data.date_start.time(),
            data.date_end.time()
        )

        discount_percent = discount["discount_percent"] if discount else None

        # Вставка брони
        reserve_id = await conn.fetchval(
            """
            INSERT INTO reserves (restoraunt_id, user_id, date_start, date_end, status, discount_percent)
            VALUES ($1, $2, $3, $4, 'new', $5)
            RETURNING id
            """,
            data.restoraunt_id,
            user_id,
            data.date_start,
            data.date_end,
            discount_percent
        )

        return reserve_id


async def update_reserve_status(reserve_id: int, new_status: str, current_user: dict):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        reserve = await conn.fetchrow("SELECT * FROM reserves WHERE id = $1", reserve_id)
        if not reserve:
            raise HTTPException(status_code=404, detail="Бронь не найдена")
        current_status = reserve["status"]

        if current_status == "completed":
            raise HTTPException(status_code=400, detail="Бронь уже завершена")

        if new_status == "cancelled":
            if current_user["role"] != "user" or reserve["user_id"] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Вы не можете отменить эту бронь")
        elif new_status == "confirmed":
            if current_user["role"] != "manager":
                raise HTTPException(status_code=403, detail="Только управляющий может подтвердить бронь")
            rest = await get_restoraunt_by_id(reserve["restoraunt_id"])
            if not rest or rest["manager_id"] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Вы не управляете этим рестораном")
            if current_status != "new":
                raise HTTPException(status_code=400, detail="Можно подтвердить только новую бронь")

        elif new_status == "completed":
            if current_user["role"] != "manager":
                raise HTTPException(status_code=403, detail="Только управляющий может завершить бронь")
            rest = await get_restoraunt_by_id(reserve["restoraunt_id"])
            if not rest or rest["manager_id"] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Вы не управляете этим рестораном")
        else:
            raise HTTPException(status_code=400, detail="Недопустимый статус")

        await conn.execute(
            "UPDATE reserves SET status = $1 WHERE id = $2",
            new_status, reserve_id
        )

async def get_user_reserves(user_id: int):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, restoraunt_id, user_id, date_start, date_end, status
            FROM reserves
            WHERE user_id = $1
            ORDER BY date_start DESC
            """,
            user_id
        )
    return [dict(r) for r in rows]

async def get_restoraunt_reserves(restoraunt_id: int):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, restoraunt_id, user_id, date_start, date_end, status
            FROM reserves
            WHERE restoraunt_id = $1
            ORDER BY date_start DESC
            """,
            restoraunt_id
        )
    return [dict(r) for r in rows]

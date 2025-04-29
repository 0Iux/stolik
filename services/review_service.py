from db.database import get_db_pool
from fastapi import HTTPException
from schemas.review import ReviewCreate


async def create_review(user_id: int, data: ReviewCreate):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        # Проверка брони
        reserve = await conn.fetchrow(
            """
            SELECT * FROM reserves WHERE id = $1
            """,
            data.reserve_id
        )
        if not reserve:
            raise HTTPException(status_code=404, detail="Бронь не найдена")
        if reserve["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Вы не можете оставить отзыв к чужой броне")
        if reserve["status"] != "completed":
            raise HTTPException(status_code=400, detail="Оставлять отзыв можно только к завершённой броне")

        existing = await conn.fetchrow(
            """
            SELECT id FROM reviews WHERE reserve_id = $1
            """,
            data.reserve_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="Отзыв к этой броне уже существует")

        # Вставка отзыва
        review_id = await conn.fetchval(
            """
            INSERT INTO reviews (restoraunt_id, user_id, mark, text_review, created_at, reserve_id)
            VALUES ($1, $2, $3, $4, NOW(), $5)
            RETURNING id
            """,
            reserve["restoraunt_id"],
            user_id,
            data.mark,
            data.text_review,
            data.reserve_id
        )

        for reason_id in data.reason_ids:
            await conn.execute(
                """
                INSERT INTO review_reason_choices (review_id, reason_id)
                VALUES ($1, $2)
                """,
                review_id,
                reason_id
            )

        return review_id

async def get_reviews_by_restoraunt(restoraunt_id: int):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT r.id, r.restoraunt_id, r.user_id, r.mark, r.text_review, r.created_at,
                   ARRAY_AGG(rr.text) AS reasons
            FROM reviews r
            LEFT JOIN review_reason_choices rc ON rc.review_id = r.id
            LEFT JOIN review_reasons rr ON rr.id = rc.reason_id
            WHERE r.restoraunt_id = $1
            GROUP BY r.id
            ORDER BY r.created_at DESC
            """,
            restoraunt_id
        )
    return [dict(row) for row in rows]

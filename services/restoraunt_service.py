from db.database import get_db_pool
from schemas.restoraunt import RestorauntCreate

async def create_restoraunt(restoraunt_data: RestorauntCreate):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        restoraunt_id = await conn.fetchval(
            """
            INSERT INTO restoraunts (title, description, address, menu_path)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            restoraunt_data.title,
            restoraunt_data.description,
            restoraunt_data.address,
            restoraunt_data.menu_path,
        )
        return restoraunt_id

async def assign_manager(restoraunt_id: int, user_id: int):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET role = 'manager' WHERE id = $1",
            user_id
        )
        await conn.execute(
            "UPDATE restoraunts SET manager_id = $1 WHERE id = $2",
            user_id,
            restoraunt_id
        )

async def get_all_restoraunts():
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, description, address, menu_path
            FROM restoraunts
            """
        )
    return [dict(row) for row in rows]

async def get_restoraunt_by_id(restoraunt_id: int):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, title, description, address, menu_path
            FROM restoraunts
            WHERE id = $1
            """,
            restoraunt_id
        )
    return dict(row) if row else None


async def update_restoraunt(restoraunt_id: int, data: dict):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        set_clauses = []
        values = []

        for idx, (key, value) in enumerate(data.items(), start=1):
            set_clauses.append(f"{key} = ${idx}")
            values.append(value)

        if not set_clauses:
            return

        query = f"""
            UPDATE restoraunts
            SET {', '.join(set_clauses)}
            WHERE id = ${len(values) + 1}
        """

        values.append(restoraunt_id)
        await conn.execute(query, *values)

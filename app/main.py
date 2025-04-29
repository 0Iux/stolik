from fastapi import FastAPI
from contextlib import asynccontextmanager

from db.database import get_db_pool
from db.database import connect_to_db, close_db_connection
from api.auth import router as auth_router
from api import restoraunt, reserve, review

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db()
    yield
    await close_db_connection()

app = FastAPI(lifespan=lifespan)

app.include_router(review.router)
app.include_router(reserve.router)
app.include_router(restoraunt.router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "API работает!"}

@app.get("/check-db")
async def check_db():
    pool = get_db_pool()
    if not pool:
        return {"status": "Нет подключения к базе"}

    async with pool.acquire() as conn:
        db_name = await conn.fetchval('SELECT current_database();')
        return {"status": "Подключено", "database": db_name}
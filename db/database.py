import asyncpg
from fastapi import FastAPI
from core.config import settings

db_pool = None  # глобальная переменная пула соединений

async def connect_to_db():
    """Создаёт пул соединений при запуске приложения"""
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=settings.database_url)

async def close_db_connection():
    """Закрывает пул соединений при остановке"""
    global db_pool
    if db_pool:
        await db_pool.close()

def get_db_pool():
    """Даёт доступ к открытому пулу для запросов"""
    return db_pool

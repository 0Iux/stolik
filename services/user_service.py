from db.database import get_db_pool
from schemas.user import UserCreate, UserInDB
from passlib.context import CryptContext
from core.config import settings
from datetime import datetime, timedelta
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(user_data: UserCreate):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        existing_user = await conn.fetchrow(
            "SELECT id FROM users WHERE number = $1",
            user_data.number
        )
        if existing_user:
            raise ValueError("Пользователь с таким номером уже существует")
        
        hashed_password = pwd_context.hash(user_data.password)

        user_id = await conn.fetchval(
            """
            INSERT INTO users (number, user_pass, allow_notification, role, created_at)
            VALUES ($1, $2, TRUE, 'user', now())
            RETURNING id
            """,
            user_data.number,
            hashed_password
        )

        return UserInDB(
            id=user_id,
            number=user_data.number,
            allow_notification=True,
            role="user"
        )

async def authenticate_user(number: str, password: str):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        user_row = await conn.fetchrow(
            "SELECT * FROM users WHERE number = $1",
            number
        )

    if not user_row:
        return None

    user = dict(user_row)

    if not pwd_context.verify(password, user['user_pass']):
        return None

    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

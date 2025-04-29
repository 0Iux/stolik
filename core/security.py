from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from core.config import settings
from db.database import get_db_pool

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    pool = get_db_pool()
    async with pool.acquire() as conn:
        user_row = await conn.fetchrow("SELECT id, number, role FROM users WHERE id = $1", int(user_id))
    
    if not user_row:
        raise credentials_exception

    user = dict(user_row)
    return user

async def get_current_active_user_with_role(allowed_roles: list[str], user: dict = Depends(get_current_user)):
    if user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа"
        )
    return user

async def admin_or_manager(user: dict = Depends(get_current_user)):
    if user["role"] in ["admin", "manager"]:
        return user
    raise HTTPException(status_code=403, detail="Только для администратора или управляющего")


async def admin_user(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Только для администратора")
    return user

async def manager_user(user: dict = Depends(get_current_user)):
    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Только для управляющего")
    return user

async def regular_user(user: dict = Depends(get_current_user)):
    if user["role"] != "user":
        raise HTTPException(status_code=403, detail="Только для обычного пользователя")
    return user


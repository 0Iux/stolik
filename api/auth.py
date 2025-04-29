from fastapi import APIRouter, HTTPException, Depends
from schemas.user import UserCreate, UserPublic, UserLogin
from services.user_service import create_user, authenticate_user, create_access_token
from core.security import get_current_user, admin_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserPublic)
async def register(user_create: UserCreate):
    """
    Регистрация нового пользователя.

    Пользователь указывает номер телефона и пароль.  
    Если номер ещё не зарегистрирован, создаётся новый аккаунт.  
    Возвращает публичные данные о пользователе (id и номер).
    """
    try:
        user = await create_user(user_create)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user_login: UserLogin):
    """
    Авторизация пользователя.

    Принимает номер телефона и пароль.  
    При успешной проверке возвращает JWT токен для дальнейшей аутентификации.
    """
    user = await authenticate_user(user_login.number, user_login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный номер или пароль")

    access_token = create_access_token(data={"sub": str(user["id"])})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Получение информации о текущем пользователе.

    Требует валидного JWT токена в заголовке Authorization.
    Возвращает ID пользователя, извлечённый из токена.
    """
    return {"user_id": current_user["id"]}

@router.get("/admin-only")
async def admin_only_route(user: dict = Depends(admin_user)):
    """
    Только для админов.
    """
    return {"message": "Добро пожаловать, администратор!"}


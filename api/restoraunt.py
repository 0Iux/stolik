from schemas.restoraunt import RestorauntCreate, RestorauntPublic, AssignManager, RestorauntUpdate
from services.restoraunt_service import create_restoraunt, assign_manager, get_all_restoraunts, update_restoraunt, get_restoraunt_by_id
from core.security import admin_or_manager, admin_user
from fastapi import APIRouter, Depends, HTTPException, status
from db.database import get_db_pool

router = APIRouter(prefix="/restoraunts", tags=["Restoraunts"])


@router.post("/", response_model=RestorauntPublic, status_code=status.HTTP_201_CREATED)
async def create_new_restoraunt(
    restoraunt_data: RestorauntCreate,
    user: dict = Depends(admin_user)
):
    """
    Создание нового ресторана.

    Доступно только пользователям с ролью 'admin'.
    """
    restoraunt_id = await create_restoraunt(restoraunt_data)
    return RestorauntPublic(id=restoraunt_id, **restoraunt_data.dict())


@router.post("/assign-manager", status_code=status.HTTP_200_OK)
async def assign_manager_to_restoraunt(
    data: AssignManager,
    user: dict = Depends(admin_user)
):
    """
    Назначить управляющего ресторану.

    Доступно только пользователям с ролью 'admin'.
    """
    await assign_manager(restoraunt_id=data.restoraunt_id, user_id=data.user_id)
    return {"detail": "Менеджер успешно назначен"}


@router.get("/", response_model=list[RestorauntPublic])
async def list_all_restoraunts():
    """
    Получение списка всех ресторанов.

    Доступно для всех пользователей, даже не авторизованных.
    """
    restoraunts = await get_all_restoraunts()
    return restoraunts


@router.patch("/{restoraunt_id}", response_model=RestorauntPublic)
async def update_restoraunt_data(
    restoraunt_id: int,
    data: RestorauntUpdate,
    user: dict = Depends(admin_or_manager)
):
    """
    Обновление информации о ресторане.

    Доступно только админу или управляющему этого ресторана.
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        restoraunt = await conn.fetchrow("SELECT manager_id FROM restoraunts WHERE id = $1", restoraunt_id)
    
    if not restoraunt:
        raise HTTPException(status_code=404, detail="Ресторан не найден")

    if user["role"] == "admin" or (user["role"] == "manager" and restoraunt["manager_id"] == user["id"]):
        await update_restoraunt(restoraunt_id, data.dict(exclude_none=True))
        updated = await get_restoraunt_by_id(restoraunt_id)
        return updated
    else:
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения этого ресторана")


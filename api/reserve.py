from fastapi import APIRouter, Depends, HTTPException, status
from schemas.reserve import ReserveInList
from services.reserve_service import get_user_reserves, get_restoraunt_reserves
from core.security import regular_user
from schemas.reserve import ReserveCreate, ReservePublic
from services.reserve_service import create_reserve
from services.restoraunt_service import get_restoraunt_by_id

router = APIRouter(prefix="/reserves", tags=["Reserves"])

@router.post("/", response_model=ReservePublic, status_code=status.HTTP_201_CREATED)
async def make_reservation(
    data: ReserveCreate,
    user: dict = Depends(regular_user)
):
    """
    Забронировать столик в ресторане.
    """
    restoraunt = await get_restoraunt_by_id(data.restoraunt_id)
    if not restoraunt:
        raise HTTPException(status_code=404, detail="Ресторан не найден")

    reserve_id = await create_reserve(user_id=user["id"], data=data)

    return ReservePublic(
        id=reserve_id,
        restoraunt_id=data.restoraunt_id,
        user_id=user["id"],
        date_start=data.date_start,
        date_end=data.date_end,
        cancelled=False
    )

from services.reserve_service import update_reserve_status
from core.security import regular_user, manager_user
from fastapi import APIRouter, Depends

@router.patch("/{reserve_id}/cancel")
async def cancel_reserve(reserve_id: int, user: dict = Depends(regular_user)):
    """
    Отмена брони пользователем.
    """
    await update_reserve_status(reserve_id, "cancelled", user)
    return {"detail": "Бронь отменена"}

@router.patch("/{reserve_id}/confirm")
async def confirm_reserve(reserve_id: int, user: dict = Depends(manager_user)):
    """
    Подтверждение брони менеджером.
    """
    await update_reserve_status(reserve_id, "confirmed", user)
    return {"detail": "Бронь подтверждена"}

@router.patch("/{reserve_id}/complete")
async def complete_reserve(reserve_id: int, user: dict = Depends(manager_user)):
    """
    Завершение брони менеджером.
    """
    await update_reserve_status(reserve_id, "completed", user)
    return {"detail": "Бронь завершена"}

@router.get("/my", response_model=list[ReserveInList])
async def get_my_reserves(user: dict = Depends(regular_user)):
    """
    Получить список всех своих броней.
    """
    return await get_user_reserves(user["id"])

@router.get("/by-restoraunt/{restoraunt_id}", response_model=list[ReserveInList])
async def get_restoraunt_reserves_view(
    restoraunt_id: int,
    user: dict = Depends(manager_user)
):
    """
    Получить список всех броней ресторана.
    Только для управляющего этого ресторана.
    """
    rest = await get_restoraunt_by_id(restoraunt_id)
    if not rest:
        raise HTTPException(status_code=404, detail="Ресторан не найден")
    if rest["manager_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Вы не управляете этим рестораном")
    return await get_restoraunt_reserves(restoraunt_id)
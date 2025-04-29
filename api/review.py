from typing import List
from fastapi import APIRouter, Depends, HTTPException
from schemas.review import ReviewCreate, ReviewInList
from services.review_service import create_review
from core.security import regular_user
from services.review_service import get_reviews_by_restoraunt
from core.security import manager_user
from services.restoraunt_service import get_restoraunt_by_id

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", status_code=201)
async def leave_review(data: ReviewCreate, user: dict = Depends(regular_user)):
    """
    Оставить отзыв на завершённую бронь.
    """
    review_id = await create_review(user["id"], data)
    return {"review_id": review_id, "detail": "Отзыв успешно создан"}


@router.get("/by-restoraunt/{restoraunt_id}", response_model=List[ReviewInList])
async def get_reviews_for_restoraunt(
    restoraunt_id: int,
    user: dict = Depends(manager_user)
):
    """
    Получить все отзывы о своём ресторане.
    Только для управляющего этого ресторана.
    """
    rest = await get_restoraunt_by_id(restoraunt_id)
    if not rest:
        raise HTTPException(status_code=404, detail="Ресторан не найден")

    if rest["manager_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Вы не управляете этим рестораном")

    return await get_reviews_by_restoraunt(restoraunt_id)

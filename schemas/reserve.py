from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReserveCreate(BaseModel):
    restoraunt_id: int
    date_start: datetime
    date_end: datetime

class ReservePublic(BaseModel):
    id: int
    restoraunt_id: int
    user_id: int
    date_start: datetime
    date_end: datetime
    status: str
    discount_percent: Optional[int] = None 

class ReserveInList(ReservePublic):
    id: int
    restoraunt_id: int
    user_id: int
    date_start: datetime
    date_end: datetime
    status: str
    discount_percent: Optional[int] = None 

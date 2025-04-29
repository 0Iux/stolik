from pydantic import BaseModel, Field
from typing import Optional
from datetime import time

class RestorauntCreate(BaseModel):
    title: str
    description: Optional[str] = None
    address: str
    menu_path: Optional[str] = None
    open_time: time
    close_time: time


class RestorauntPublic(BaseModel):
    id: int
    title: str
    description: Optional[str]
    address: str
    menu_path: Optional[str]
    open_time: time
    close_time: time

class AssignManager(BaseModel):
    restoraunt_id: int
    user_id: int

class RestorauntUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    menu_path: Optional[str] = None
    open_time: Optional[time] = None
    close_time: Optional[time] = None


from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ReviewCreate(BaseModel):
    reserve_id: int
    mark: int = Field(..., ge=1, le=5)
    reason_ids: List[int] = Field(default_factory=list)
    text_review: Optional[str] = None


class ReviewInList(BaseModel):
    id: int
    restoraunt_id: int
    user_id: int
    mark: int
    text_review: Optional[str] = None
    created_at: datetime
    reasons: List[str]

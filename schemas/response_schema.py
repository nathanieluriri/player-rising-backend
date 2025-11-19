# schemas/response_schema.py

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    status_code: int
    data: Optional[T]
    detail: str

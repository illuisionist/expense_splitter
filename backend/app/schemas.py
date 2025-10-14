# schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str]
    class Config:
        orm_mode = True

class GroupCreate(BaseModel):
    name: str

class GroupOut(BaseModel):
    id: int
    name: str
    owner_id: int
    class Config:
        orm_mode = True

class ExpenseCreate(BaseModel):
    payer_id: int
    amount: Decimal
    description: Optional[str] = ""
    participants: List[int]  # IDs
    # shares optional: mapping user_id -> amount (not implemented in UI yet)

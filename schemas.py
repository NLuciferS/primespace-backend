from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
from typing import Optional, Any
from datetime import datetime


class UserRole(str, Enum):
    customer = "customer"
    provider = "provider"
    admin = "admin"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.customer

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes).")
        return v


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class VenueOut(BaseModel):
    id: str
    name: str
    location: str
    city: str
    venue_type: str
    capacity: int
    rating: float
    price: int

    model_config = {"from_attributes": True}


class BookingCreate(BaseModel):
    venue_id: str
    date: str
    guests: int
    total: int

    @field_validator("guests")
    @classmethod
    def guests_positive(cls, v: int):
        if v <= 0:
            raise ValueError("Guests must be >= 1.")
        return v

    @field_validator("total")
    @classmethod
    def total_positive(cls, v: int):
        if v <= 0:
            raise ValueError("Total must be >= 1.")
        return v


class BookingOut(BaseModel):
    id: int
    venue_id: str
    date: str
    guests: int
    total: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityOut(BaseModel):
    venue_id: str
    available_dates: list[str]  # DD/MM/YYYY format, excluding booked dates


class UserUpdate(BaseModel):
    name: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if v is not None:
            v = (v or "").strip()
            if not v:
                raise ValueError("Name cannot be empty.")
        return v


class ErrorOut(BaseModel):
    detail: Any

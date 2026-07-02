from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
from uuid import UUID

from database import get_db
from models.db_models import User, Shop
from core.security import hash_password, verify_password, create_access_token, get_current_manager

router = APIRouter(prefix="/staff", tags=["staff"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CreateStaffRequest(BaseModel):
    full_name: str
    phone: str
    email: str | None = None
    password: str


class StaffOut(BaseModel):
    user_id: str
    full_name: str
    phone: str
    email: str | None
    role: str
    is_active: bool
    created_at: datetime


class StaffLoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    shop_id: str
    full_name: str


# ---------------------------------------------------------------------------
# POST /staff/create   — manager creates a cashier account
# ---------------------------------------------------------------------------
@router.post("/create", response_model=StaffOut, status_code=201)
def create_staff(
    data: CreateStaffRequest,
    db: Session = Depends(get_db),
    current_shop: Shop = Depends(get_current_manager),
):
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        shop_id       = current_shop.shop_id,
        full_name     = data.full_name,
        phone         = data.phone,
        email         = data.email,
        password_hash = hash_password(data.password),
        role          = "cashier",
        is_active     = True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return StaffOut(
        user_id    = str(user.user_id),
        full_name  = user.full_name,
        phone      = user.phone,
        email      = user.email,
        role       = user.role,
        is_active  = user.is_active,
        created_at = user.created_at,
    )


# ---------------------------------------------------------------------------
# POST /staff/login   — cashier logs in with phone + password
# ---------------------------------------------------------------------------
@router.post("/login", response_model=StaffLoginResponse)
def staff_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # username field = phone number
    user = db.query(User).filter(
        User.phone     == form_data.username,
        User.role      == "cashier",
        User.is_active == True,
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token({
        "sub":     str(user.user_id),
        "shop_id": str(user.shop_id),
        "role":    user.role,
    })

    return StaffLoginResponse(
        access_token = token,
        token_type   = "bearer",
        role         = user.role,
        shop_id      = str(user.shop_id),
        full_name    = user.full_name,
    )


# ---------------------------------------------------------------------------
# GET /staff   — manager lists all cashiers in their shop
# ---------------------------------------------------------------------------
@router.get("", response_model=List[StaffOut])
def list_staff(
    db: Session = Depends(get_db),
    current_shop: Shop = Depends(get_current_manager),
):
    users = db.query(User).filter(
        User.shop_id == current_shop.shop_id,
        User.role    == "cashier",
    ).all()

    return [
        StaffOut(
            user_id    = str(u.user_id),
            full_name  = u.full_name,
            phone      = u.phone,
            email      = u.email,
            role       = u.role,
            is_active  = u.is_active,
            created_at = u.created_at,
        )
        for u in users
    ]


# ---------------------------------------------------------------------------
# PATCH /staff/{user_id}/deactivate   — disable cashier access
# ---------------------------------------------------------------------------
@router.patch("/{user_id}/deactivate", response_model=StaffOut)
def deactivate_staff(
    user_id: str,
    db: Session = Depends(get_db),
    current_shop: Shop = Depends(get_current_manager),
):
    user = db.query(User).filter(
        User.user_id == UUID(user_id),
        User.shop_id == current_shop.shop_id,
        User.role    == "cashier",
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Cashier not found")

    user.is_active = False
    db.commit()
    db.refresh(user)

    return StaffOut(
        user_id    = str(user.user_id),
        full_name  = user.full_name,
        phone      = user.phone,
        email      = user.email,
        role       = user.role,
        is_active  = user.is_active,
        created_at = user.created_at,
    )


# ---------------------------------------------------------------------------
# PATCH /staff/{user_id}/reactivate   — re-enable cashier access
# ---------------------------------------------------------------------------
@router.patch("/{user_id}/reactivate", response_model=StaffOut)
def reactivate_staff(
    user_id: str,
    db: Session = Depends(get_db),
    current_shop: Shop = Depends(get_current_manager),
):
    user = db.query(User).filter(
        User.user_id == UUID(user_id),
        User.shop_id == current_shop.shop_id,
        User.role    == "cashier",
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Cashier not found")

    user.is_active = True
    db.commit()
    db.refresh(user)

    return StaffOut(
        user_id    = str(user.user_id),
        full_name  = user.full_name,
        phone      = user.phone,
        email      = user.email,
        role       = user.role,
        is_active  = user.is_active,
        created_at = user.created_at,
    )
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
from models.db_models import Shop, User
from schemas.pydantic_schemas import ShopRegister, TokenResponse, ShopOut
from core.security import hash_password, verify_password, create_access_token, get_current_manager

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ShopOut, status_code=201)
def register(data: ShopRegister, db: Session = Depends(get_db)):
    existing = db.query(Shop).filter(Shop.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    shop = Shop(
        shop_name       = data.shop_name,
        owner_name      = data.owner_name,
        email           = data.email,
        hashed_password = hash_password(data.password),
        phone           = data.phone,
        address         = data.address,
        state           = data.state,
        district        = data.district,
        city            = data.city,
        pincode         = data.pincode,
        gstin           = data.gstin,
    )
    db.add(shop)
    db.flush()   # get shop_id before creating the owner User

    # Auto-create a User record for the owner so cashier_id is always a
    # valid UUID in orders — even when the manager places the order.
    owner_user = User(
        shop_id       = shop.shop_id,
        full_name     = data.owner_name,
        phone         = data.phone,
        email         = data.email,
        password_hash = hash_password(data.password),
        role          = "owner",
        is_active     = True,
    )
    db.add(owner_user)
    db.commit()
    db.refresh(shop)
    return shop


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    shop = db.query(Shop).filter(Shop.email == form_data.username).first()
    if not shop or not verify_password(form_data.password, shop.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Fetch the owner User record — created automatically on register.
    # For shops registered before this update, create it on the fly here.
    owner_user = db.query(User).filter(
        User.shop_id == shop.shop_id,
        User.role    == "owner",
        User.is_active == True,
    ).first()

    if not owner_user:
        # Migration path: shops registered before the User system was added
        owner_user = User(
            shop_id       = shop.shop_id,
            full_name     = shop.owner_name,
            phone         = shop.phone,
            email         = shop.email,
            password_hash = shop.hashed_password,  # reuse already-hashed password
            role          = "owner",
            is_active     = True,
        )
        db.add(owner_user)
        db.commit()
        db.refresh(owner_user)

    # Update last_login
    owner_user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token({
        "sub":     str(owner_user.user_id),
        "shop_id": str(shop.shop_id),
        "role":    "owner",
    })
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=ShopOut)
def get_me(current_shop: Shop = Depends(get_current_manager)):
    return current_shop
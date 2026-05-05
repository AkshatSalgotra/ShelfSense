from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import Shop
from schemas.pydantic_schemas import ShopRegister, TokenResponse, ShopOut
from core.security import hash_password, verify_password, create_access_token, get_current_shop

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
    db.commit()
    db.refresh(shop)
    return shop


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.email == form_data.username).first()
    if not shop or not verify_password(form_data.password, shop.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": str(shop.shop_id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=ShopOut)
def get_me(current_shop: Shop = Depends(get_current_shop)):
    return current_shop
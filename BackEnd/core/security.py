from dataclasses import dataclass
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import Shop, User
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY                  = os.getenv("SECRET_KEY", "fallback-dev-key")
ALGORITHM                   = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080))

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@dataclass
class PosActor:
    """Unified identity object returned for any authenticated user hitting POS routes."""
    shop_id: UUID
    user_id: UUID
    role: str          # "owner" | "manager" | "cashier"


# ---------------------------------------------------------------------------
# get_current_manager
# Protects all manager-only routes (products, inventory, alerts, forecasts …)
# Accepts tokens with role = "owner" or "manager"
# Returns the Shop object (keeps existing route code mostly unchanged)
# ---------------------------------------------------------------------------
def get_current_manager(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Shop:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role not in ("owner", "manager"):
            print(f" [AUTH] Forbidden: Role '{role}' is not manager/owner")
            raise HTTPException(status_code=403, detail="Manager access required")

        shop_id_str = payload.get("shop_id")
        if not shop_id_str:
            raise HTTPException(status_code=401, detail="Invalid token: missing shop_id")

        shop = db.query(Shop).filter(Shop.shop_id == UUID(shop_id_str)).first()
        if not shop:
            print(f" [AUTH] Shop not found for ID: {shop_id_str}")
            raise HTTPException(status_code=401, detail="Shop not found")
        return shop

    except JWTError:
        print(" [AUTH] JWT Decode Error: Token is invalid or signature mismatch")
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError as e:
        print(f" [AUTH] Value Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f" [AUTH] Unexpected Error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail="Internal auth error")


# ---------------------------------------------------------------------------
# get_pos_actor
# Protects POS routes (orders, payments)
# Accepts any valid role — owner, manager, cashier
# Returns a PosActor so cashier_id is always a real UUID
# ---------------------------------------------------------------------------
def get_pos_actor(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> PosActor:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role        = payload.get("role")
        user_id_str = payload.get("sub")
        shop_id_str = payload.get("shop_id")

        if not all([role, user_id_str, shop_id_str]):
            raise HTTPException(status_code=401, detail="Invalid token: missing claims")

        user_id = UUID(user_id_str)
        shop_id = UUID(shop_id_str)

        user = db.query(User).filter(
            User.user_id == user_id,
            User.is_active == True,
        ).first()
        if not user:
            print(f" [AUTH] User not found or inactive for ID: {user_id_str}")
            raise HTTPException(status_code=401, detail="User not found or inactive")

        return PosActor(shop_id=shop_id, user_id=user_id, role=role)

    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
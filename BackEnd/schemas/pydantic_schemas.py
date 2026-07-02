from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


# ─── Auth ────────────────────────────────────────────────────────────────────

class ShopRegister(BaseModel):
    shop_name:  str
    owner_name: str
    email:      EmailStr
    password:   str
    phone:      Optional[str] = None
    address:    Optional[str] = None
    state:      Optional[str] = None
    district:   Optional[str] = None
    city:       Optional[str] = None
    pincode:    Optional[str] = None
    gstin:      Optional[str] = None

class ShopLogin(BaseModel):
    email:    EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class ShopOut(BaseModel):
    shop_id:    UUID
    shop_name:  str
    owner_name: str
    email:      str
    phone:      Optional[str]
    state:      Optional[str]
    district:   Optional[str]
    city:       Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Products ────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    product_name:      str
    category:          Optional[str]   = None   # pass category name e.g. "potato_chips"
    unit:              Optional[str]   = "units"
    current_stock:     Optional[float] = 0.0
    reorder_threshold: Optional[float] = 10.0
    cost_price:        Optional[float] = None
    selling_price:     Optional[float] = None
    sku_code:          Optional[str]   = None

class ProductUpdate(BaseModel):
    product_name:      Optional[str]   = None
    category:          Optional[str]   = None   # pass category name to update
    unit:              Optional[str]   = None
    current_stock:     Optional[float] = None
    reorder_threshold: Optional[float] = None
    cost_price:        Optional[float] = None
    selling_price:     Optional[float] = None
    sku_code:          Optional[str]   = None

class ProductOut(BaseModel):
    product_id:        UUID
    shop_id:           UUID
    product_name:      str
    category:          Optional[str]   # category name resolved from relationship
    unit:              str
    current_stock:     float
    reorder_threshold: float
    cost_price:        Optional[float]
    selling_price:     Optional[float]
    sku_code:          Optional[str]
    needs_restock:     bool = False

    @model_validator(mode="after")
    def compute_needs_restock(self):
        self.needs_restock = self.current_stock < self.reorder_threshold
        return self

    class Config:
        from_attributes = True


# ─── Sales ───────────────────────────────────────────────────────────────────

class SaleCreate(BaseModel):
    product_id:    UUID
    quantity_sold: float
    sale_date:     Optional[date] = None
    note:          Optional[str]  = None

class SaleOut(BaseModel):
    log_id:        UUID
    shop_id:       UUID
    product_id:    UUID
    quantity_sold: float
    sale_date:     date
    note:          Optional[str]
    created_at:    datetime

    class Config:
        from_attributes = True

class SaleSummary(BaseModel):
    product_id:         UUID
    product_name:       str
    total_units_sold:   float
    total_transactions: int


# ─── Predictions ─────────────────────────────────────────────────────────────

class DailyForecast(BaseModel):
    date: str
    quantity: float

class PredictionOut(BaseModel):
    product_id:        UUID
    product_name:      str
    forecast_days:     int
    total_predicted_demand:  float
    current_stock:     float
    recommended_qty:   float
    confidence:        str
    model_tier:        str
    daily_forecast:    List[DailyForecast]
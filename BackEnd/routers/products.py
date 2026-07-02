from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import get_db
from models.db_models import Product, Inventory
from core.security import get_pos_actor

router = APIRouter(prefix="/products", tags=["products"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ProductSearchResult(BaseModel):
    product_id: str
    product_name: str
    sku_code: str | None
    category_id: int | None
    selling_price: float | None
    unit: str
    current_stock: int


# ---------------------------------------------------------------------------
# GET /products/search?q=kurkure
# ---------------------------------------------------------------------------
@router.get("/search", response_model=List[ProductSearchResult])
def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_pos_actor),
):
    results = (
        db.query(Product, Inventory)
        .join(Inventory, Inventory.product_id == Product.product_id, isouter=True)
        .filter(
            Product.shop_id == current_user.shop_id,
            Product.is_active == True,
            Product.product_name.ilike(f"%{q}%"),
        )
        .limit(limit)
        .all()
    )

    return [
        ProductSearchResult(
            product_id=str(p.product_id),
            product_name=p.product_name,
            sku_code=p.sku_code,
            category_id=p.category_id,
            selling_price=float(p.selling_price) if p.selling_price else None,
            unit=p.unit,
            current_stock=inv.current_stock if inv else 0,
        )
        for p, inv in results
    ]


# ---------------------------------------------------------------------------
# GET /products/sku/{sku_code}  — lookup by SKU code (replaces barcode for now)
# Add barcode column to Product model later, then add /products/barcode/{barcode}
# ---------------------------------------------------------------------------
@router.get("/sku/{sku_code}", response_model=ProductSearchResult)
def get_product_by_sku(
    sku_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_pos_actor),
):
    result = (
        db.query(Product, Inventory)
        .join(Inventory, Inventory.product_id == Product.product_id, isouter=True)
        .filter(
            Product.shop_id == current_user.shop_id,
            Product.sku_code == sku_code,
            Product.is_active == True,
        )
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"No product found with SKU {sku_code}")

    p, inv = result
    return ProductSearchResult(
        product_id=str(p.product_id),
        product_name=p.product_name,
        sku_code=p.sku_code,
        category_id=p.category_id,
        selling_price=float(p.selling_price) if p.selling_price else None,
        unit=p.unit,
        current_stock=inv.current_stock if inv else 0,
    )
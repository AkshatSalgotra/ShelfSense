from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from models.db_models import Shop, Product, Category
from schemas.pydantic_schemas import ProductCreate, ProductUpdate, ProductOut
from core.security import get_current_shop

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def _get_or_create_category(db: Session, category_name: str) -> Category:
    """Looks up a category by name, creates it if it doesn't exist."""
    cat = db.query(Category).filter(Category.name == category_name).first()
    if not cat:
        cat = Category(name=category_name)
        db.add(cat)
        db.flush()
    return cat


def _to_product_out(product: Product) -> ProductOut:
    """Resolves category name from the relationship for the response."""
    return ProductOut(
        product_id        = product.product_id,
        shop_id           = product.shop_id,
        product_name      = product.product_name,
        category          = product.category.name if product.category else None,
        unit              = product.unit,
        current_stock     = product.current_stock,
        reorder_threshold = product.reorder_threshold,
        cost_price        = float(product.cost_price) if product.cost_price else None,
        selling_price     = float(product.selling_price) if product.selling_price else None,
        sku_code          = product.sku_code,
    )


@router.get("/", response_model=List[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    products = db.query(Product).filter(Product.shop_id == shop.shop_id).all()
    return [_to_product_out(p) for p in products]


@router.get("/alerts", response_model=List[ProductOut])
def low_stock_alerts(
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    """Returns only products below their reorder threshold."""
    products = db.query(Product).filter(Product.shop_id == shop.shop_id).all()
    return [_to_product_out(p) for p in products if p.current_stock < p.reorder_threshold]


@router.post("/", response_model=ProductOut, status_code=201)
def add_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    category_id = None
    if data.category:
        cat = _get_or_create_category(db, data.category)
        category_id = cat.category_id

    product = Product()
    product.shop_id           = shop.shop_id
    product.product_name      = data.product_name
    product.category_id       = category_id
    product.unit               = data.unit or "units"
    product.current_stock     = data.current_stock or 0.0
    product.reorder_threshold = data.reorder_threshold or 10.0
    product.cost_price        = data.cost_price
    product.selling_price     = data.selling_price
    product.sku_code          = data.sku_code

    db.add(product)
    db.commit()
    db.refresh(product)
    return _to_product_out(product)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.shop_id == shop.shop_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_product_out(product)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.shop_id == shop.shop_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle category name → category_id resolution
    if "category" in update_data:
        cat_name = update_data.pop("category")
        if cat_name:
            cat = _get_or_create_category(db, cat_name)
            product.category_id = cat.category_id
        else:
            product.category_id = None

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return _to_product_out(product)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.shop_id == shop.shop_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
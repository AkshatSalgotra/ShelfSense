"""
seed_csv.py — Wipe and reload synthetic data into the database.

Usage:
    python seed_csv.py --products products.csv --sales sales_2024_2025.csv --email ravi@kirana.com

products.csv columns : sku_code, product_name, category, unit, cost_price, selling_price
sales.csv columns    : date, sku_code, product_name, category, quantity_sold

Run from BackEnd/ directory.
"""

import argparse
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal
from models.db_models import (
    Shop, Product, Category, Inventory,
    SalesLog, ReorderAlert, MLForecast,
    InventoryLog, Order, OrderItem, Payment, Customer, Supplier, User
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_or_create_category(db: Session, name: str, cache: dict) -> int:
    if name in cache:
        return cache[name]
    cat = db.query(Category).filter(Category.name == name).first()
    if not cat:
        cat = Category(name=name)
        db.add(cat)
        db.flush()
    cache[name] = cat.category_id
    return cat.category_id


# ---------------------------------------------------------------------------
# Wipe
# ---------------------------------------------------------------------------
def wipe(db: Session, shop_id):
    print("\n[WIPE] Clearing all shop data except auth...")

    # Delete in dependency order to avoid FK violations
    db.query(Payment).filter(
        Payment.order_id.in_(
            db.query(Order.order_id).filter(Order.shop_id == shop_id)
        )
    ).delete(synchronize_session=False)

    db.query(OrderItem).filter(
        OrderItem.order_id.in_(
            db.query(Order.order_id).filter(Order.shop_id == shop_id)
        )
    ).delete(synchronize_session=False)

    db.query(SalesLog).filter(SalesLog.shop_id == shop_id).delete(synchronize_session=False)
    db.query(Order).filter(Order.shop_id == shop_id).delete(synchronize_session=False)
    db.query(InventoryLog).filter(InventoryLog.shop_id == shop_id).delete(synchronize_session=False)
    db.query(ReorderAlert).filter(ReorderAlert.shop_id == shop_id).delete(synchronize_session=False)
    db.query(MLForecast).filter(MLForecast.shop_id == shop_id).delete(synchronize_session=False)
    db.query(Inventory).filter(Inventory.shop_id == shop_id).delete(synchronize_session=False)
    db.query(Product).filter(Product.shop_id == shop_id).delete(synchronize_session=False)
    db.query(Customer).filter(Customer.shop_id == shop_id).delete(synchronize_session=False)
    db.query(Supplier).filter(Supplier.shop_id == shop_id).delete(synchronize_session=False)

    # Cashier users only — keep the owner User record
    db.query(User).filter(
        User.shop_id == shop_id,
        User.role    == "cashier",
    ).delete(synchronize_session=False)

    db.commit()
    print("[WIPE] Done — shop auth and owner user preserved.")


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------
def seed(products_csv: str, sales_csv: str, shop_email: str):
    db: Session = SessionLocal()

    try:
        # ── Find shop ────────────────────────────────────────────────────────
        shop = db.query(Shop).filter(Shop.email == shop_email).first()
        if not shop:
            print(f"[ERROR] No shop found with email '{shop_email}'.")
            return
        print(f"[OK] Found shop: {shop.shop_name} (id={shop.shop_id})")

        # ── Load CSVs ────────────────────────────────────────────────────────
        prod_df  = pd.read_csv(products_csv)
        sales_df = pd.read_csv(sales_csv)

        prod_required  = {"sku_code", "product_name", "category", "unit", "cost_price", "selling_price"}
        sales_required = {"date", "sku_code", "quantity_sold"}

        for col_set, name, df in [
            (prod_required,  "products CSV",  prod_df),
            (sales_required, "sales CSV",     sales_df),
        ]:
            missing = col_set - set(df.columns)
            if missing:
                print(f"[ERROR] {name} missing columns: {missing}")
                return

        sales_df["date"]          = pd.to_datetime(sales_df["date"])
        sales_df["quantity_sold"] = pd.to_numeric(sales_df["quantity_sold"], errors="coerce").fillna(0)

        print(f"[OK] products CSV : {len(prod_df)} rows")
        print(f"[OK] sales CSV    : {len(sales_df)} rows — {sales_df['sku_code'].nunique()} SKUs")

        # ── Wipe existing data ───────────────────────────────────────────────
        wipe(db, shop.shop_id)

        # ── Seed products + inventory ────────────────────────────────────────
        category_cache = {}
        product_map    = {}   # sku_code → Product

        for _, row in prod_df.iterrows():
            sku_code     = str(row["sku_code"]).strip()
            name         = str(row["product_name"]).strip()
            cat_name     = str(row["category"]).strip() if pd.notna(row["category"]) else None
            unit         = str(row["unit"]).strip()     if pd.notna(row["unit"])     else "units"
            cost_price   = float(row["cost_price"])     if pd.notna(row["cost_price"])   else None
            selling_price= float(row["selling_price"])  if pd.notna(row["selling_price"]) else None

            # Compute a sensible opening stock from the sales data
            sku_sales    = sales_df[sales_df["sku_code"] == sku_code]["quantity_sold"]
            avg_daily    = sku_sales.mean() if len(sku_sales) else 0
            opening_stock = max(int(avg_daily * 30), 10)   # 30-day buffer, minimum 10

            cat_id = get_or_create_category(db, cat_name, category_cache) if cat_name else None

            product = Product(
                shop_id           = shop.shop_id,
                product_name      = name,
                sku_code          = sku_code,
                category_id       = cat_id,
                unit              = unit,
                cost_price        = cost_price,
                selling_price     = selling_price,
                current_stock     = float(opening_stock),
                reorder_threshold = max(int(avg_daily * 7), 5),   # 7-day buffer
                is_active         = True,
            )
            db.add(product)
            db.flush()

            # Inventory row — source of truth for live stock
            inventory = Inventory(
                shop_id       = shop.shop_id,
                product_id    = product.product_id,
                current_stock = opening_stock,
            )
            db.add(inventory)

            product_map[sku_code] = product
            print(f"  [NEW] {sku_code} — {name} (stock={opening_stock}, threshold={product.reorder_threshold})")

        db.commit()
        print(f"\n[OK] {len(product_map)} products + inventory rows created")

        # ── Seed sales log ───────────────────────────────────────────────────
        inserted = 0
        skipped  = 0

        for _, row in sales_df.iterrows():
            sku_code = str(row["sku_code"]).strip()
            product  = product_map.get(sku_code)
            if not product:
                skipped += 1
                continue

            sale = SalesLog(
                shop_id       = shop.shop_id,
                product_id    = product.product_id,
                quantity_sold = float(row["quantity_sold"]),
                sale_date     = row["date"].date(),
                note          = "seeded from CSV",
            )
            db.add(sale)
            inserted += 1

            # Batch commit every 5000 rows to avoid memory buildup
            if inserted % 5000 == 0:
                db.commit()
                print(f"  ...{inserted} sales inserted")

        db.commit()
        print(f"[OK] Inserted {inserted} sale records ({skipped} skipped — SKU not in products CSV)")
        print("[DONE] Seeding complete.\n")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--products", required=True, help="Path to products.csv")
    parser.add_argument("--sales",    required=True, help="Path to sales_2024_2025.csv")
    parser.add_argument("--email",    required=True, help="Shop owner email")
    args = parser.parse_args()

    seed(
        products_csv = args.products,
        sales_csv    = args.sales,
        shop_email   = args.email,
    )
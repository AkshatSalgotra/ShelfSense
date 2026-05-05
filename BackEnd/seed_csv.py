"""
seed_csv.py — Load synthetic CSV data into the database.

Usage:
    python seed_csv.py --csv your_file.csv --email ravi@kirana.com

CSV columns: ds (DD-MM-YYYY), product_name, category, unit, y
Run from BackEnd/ directory.
"""

import argparse
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from models.db_models import Shop, Product, Category, SalesLog


def get_or_create_category(db: Session, name: str) -> Category:
    cat = db.query(Category).filter(Category.name == name).first()
    if not cat:
        cat = Category(name=name)
        db.add(cat)
        db.flush()
    return cat


def seed(csv_path: str, shop_email: str):
    db: Session = SessionLocal()

    try:
        shop = db.query(Shop).filter(Shop.email == shop_email).first()
        if not shop:
            print(f"[ERROR] No shop found with email '{shop_email}'.")
            return

        print(f"[OK] Found shop: {shop.shop_name} (id={shop.shop_id})")

        df = pd.read_csv(csv_path)
        required = {"ds", "product_name", "category", "unit", "y"}
        missing = required - set(df.columns)
        if missing:
            print(f"[ERROR] CSV missing columns: {missing}")
            return

        df["ds"] = pd.to_datetime(df["ds"], format="%Y-%m-%d")
        df["y"]  = pd.to_numeric(df["y"], errors="coerce").fillna(0)

        print(f"[OK] Loaded {len(df)} rows — {df['product_name'].nunique()} unique products")

        # ── Category cache — avoid repeated DB lookups ────────────────────────
        category_cache = {}

        def resolve_category(name: str) -> int:
            if name not in category_cache:
                cat = get_or_create_category(db, name)
                category_cache[name] = cat.category_id
            return category_cache[name]

        # ── Create products ───────────────────────────────────────────────────
        product_map = {}
        unique_products = df[["product_name", "category", "unit"]].drop_duplicates("product_name")

        for _, row in unique_products.iterrows():
            name      = row["product_name"].strip()
            cat_name  = row["category"].strip() if pd.notna(row["category"]) else None
            unit      = row["unit"].strip()     if pd.notna(row["unit"])     else "units"

            existing = db.query(Product).filter(
                Product.shop_id      == shop.shop_id,
                Product.product_name == name
            ).first()

            if existing:
                product_map[name] = existing
                print(f"  [SKIP] {name}")
                continue

            product = Product()
            product.shop_id           = shop.shop_id
            product.product_name      = name
            product.category_id       = resolve_category(cat_name) if cat_name else None
            product.unit              = unit
            product.current_stock     = 0.0
            product.reorder_threshold = 10.0

            db.add(product)
            db.flush()
            product_map[name] = product
            print(f"  [NEW] {name}")

        db.commit()
        print(f"\n[OK] {len(product_map)} products ready")

        # ── Insert sales ──────────────────────────────────────────────────────
        inserted = 0
        for _, row in df.iterrows():
            name = row["product_name"].strip()
            product = product_map.get(name)
            if not product:
                continue
            sale = SalesLog()
            sale.shop_id       = shop.shop_id
            sale.product_id    = product.product_id
            sale.quantity_sold = float(row["y"])
            sale.sale_date     = row["ds"].date()
            sale.note          = "seeded from CSV"
            db.add(sale)
            inserted += 1

        db.commit()
        print(f"[OK] Inserted {inserted} sale records")

        # ── Update current_stock baseline ─────────────────────────────────────
        for name, product in product_map.items():
            total = df[df["product_name"].str.strip() == name]["y"].sum()
            product.current_stock = float(total)
            db.add(product)

        db.commit()
        print("[OK] current_stock updated\n[DONE] Seeding complete.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv",   required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    seed(csv_path=args.csv, shop_email=args.email)
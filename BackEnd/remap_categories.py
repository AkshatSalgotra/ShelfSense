"""
remap_categories.py — Updates product categories to granular values via category_id FK.

Usage:
    python remap_categories.py --email ravi@kirana.com
"""

import argparse
from sqlalchemy.orm import Session
from database import SessionLocal
from models.db_models import Shop, Product, Category

CATEGORY_MAP = {
    "Bisleri Mineral Water 500ml": "packaged_water",
    "Bisleri Mineral Water 5L": "packaged_water",
    "Aquafina Mineral Water 500ml": "packaged_water",
    "Aquafina Mineral Water 1L": "packaged_water",
    "Kinley Mineral Water 500ml": "packaged_water",
    "Kinley Mineral Water 1L": "packaged_water",
    "Kinley Mineral Water 5L": "packaged_water",
    "Coca-Cola Cola 200ml": "cola",
    "Coca-Cola Cola 500ml": "cola",
    "Coca-Cola Cola 2L": "cola",
    "Pepsi Cola 200ml": "cola",
    "Pepsi Cola 500ml": "cola",
    "Pepsi Cola 2L": "cola",
    "Thums Up Cola 200ml": "cola",
    "Thums Up Cola 500ml": "cola",
    "Thums Up Cola 2L": "cola",
    "Sprite Clear Lime Soda 200ml": "lime_soda",
    "Sprite Clear Lime Soda 500ml": "lime_soda",
    "Sprite Clear Lime Soda 2L": "lime_soda",
    "Limca Clear Lime Soda 200ml": "lime_soda",
    "Limca Clear Lime Soda 500ml": "lime_soda",
    "Limca Clear Lime Soda 2L": "lime_soda",
    "7UP Clear Lime Soda 200ml": "lime_soda",
    "7UP Clear Lime Soda 500ml": "lime_soda",
    "7UP Clear Lime Soda 2L": "lime_soda",
    "Slice Mango Drink 150ml": "mango_drink",
    "Slice Mango Drink 600ml": "mango_drink",
    "Slice Mango Drink 1.2L": "mango_drink",
    "Maaza Mango Drink 150ml": "mango_drink",
    "Maaza Mango Drink 600ml": "mango_drink",
    "Maaza Mango Drink 1.2L": "mango_drink",
    "Frooti Mango Drink 150ml": "mango_drink",
    "Frooti Mango Drink 600ml": "mango_drink",
    "Frooti Mango Drink 1.2L": "mango_drink",
    "India Gate Basmati Rice 1kg": "basmati_rice",
    "India Gate Basmati Rice 5kg": "basmati_rice",
    "Daawat Basmati Rice 1kg": "basmati_rice",
    "Daawat Basmati Rice 5kg": "basmati_rice",
    "Kohinoor Basmati Rice 1kg": "basmati_rice",
    "Kohinoor Basmati Rice 5kg": "basmati_rice",
    "Aashirvaad Whole Wheat Atta 1kg": "wheat_atta",
    "Aashirvaad Whole Wheat Atta 5kg": "wheat_atta",
    "Aashirvaad Whole Wheat Atta 10kg": "wheat_atta",
    "Pillsbury Whole Wheat Atta 1kg": "wheat_atta",
    "Pillsbury Whole Wheat Atta 5kg": "wheat_atta",
    "Pillsbury Whole Wheat Atta 10kg": "wheat_atta",
    "Patanjali Whole Wheat Atta 1kg": "wheat_atta",
    "Patanjali Whole Wheat Atta 5kg": "wheat_atta",
    "Patanjali Whole Wheat Atta 10kg": "wheat_atta",
    "Sagar Kuttu Ka Atta 500g": "specialty_flour",
    "Local Kuttu Ka Atta 200g": "specialty_flour",
    "Local Kuttu Ka Atta 500g": "specialty_flour",
    "Tata Sampann Toor Dal 500g": "toor_dal",
    "Tata Sampann Toor Dal 1kg": "toor_dal",
    "Generic Toor Dal 500g": "toor_dal",
    "Generic Toor Dal 1kg": "toor_dal",
    "Tata Sampann Moong Dal 1kg": "moong_dal",
    "Tata Sampann Chana Dal 500g": "chana_dal",
    "Tata Sampann Chana Dal 1kg": "chana_dal",
    "Generic Chana Dal 500g": "chana_dal",
    "Generic Chana Dal 1kg": "chana_dal",
    "Tata Salt 1kg": "salt",
    "Madhur Salt 1kg": "salt",
    "Sagar Sendha Namak 500g": "sendha_namak",
    "Rajdhani Sendha Namak 200g": "sendha_namak",
    "Local Sendha Namak 200g": "sendha_namak",
    "Local Sendha Namak 500g": "sendha_namak",
    "Tata Sugar 1kg": "sugar",
    "Madhur Sugar 1kg": "sugar",
    "Fortune Mustard Oil 1L": "mustard_oil",
    "Fortune Mustard Oil 5L": "mustard_oil",
    "Dhara Mustard Oil 1L": "mustard_oil",
    "Dhara Mustard Oil 5L": "mustard_oil",
    "Saffola Mustard Oil 1L": "mustard_oil",
    "Saffola Mustard Oil 5L": "mustard_oil",
    "Saffola Sunflower Oil 1L": "sunflower_oil",
    "Saffola Sunflower Oil 5L": "sunflower_oil",
    "Fortune Sunflower Oil 1L": "sunflower_oil",
    "Fortune Sunflower Oil 5L": "sunflower_oil",
    "Local Sabudana 200g": "sabudana",
    "Local Sabudana 500g": "sabudana",
    "Rajdhani Sabudana 200g": "sabudana",
    "Rajdhani Sabudana 500g": "sabudana",
    "Local Makhana 200g": "makhana",
    "Local Makhana 500g": "makhana",
    "Sagar Makhana 200g": "makhana",
    "Rajdhani Makhana 500g": "makhana",
    "Lay's Potato Chips 10g": "potato_chips",
    "Lay's Potato Chips 20g": "potato_chips",
    "Lay's Potato Chips 50g": "potato_chips",
    "Balaji Potato Chips 10g": "potato_chips",
    "Balaji Potato Chips 20g": "potato_chips",
    "Balaji Potato Chips 50g": "potato_chips",
    "Bingo Potato Chips 10g": "potato_chips",
    "Bingo Potato Chips 20g": "potato_chips",
    "Bingo Potato Chips 50g": "potato_chips",
    "Lay's Salted Wafers 10g": "salted_wafers",
    "Lay's Salted Wafers 20g": "salted_wafers",
    "Lay's Salted Wafers 50g": "salted_wafers",
    "Balaji Salted Wafers 10g": "salted_wafers",
    "Balaji Salted Wafers 20g": "salted_wafers",
    "Balaji Salted Wafers 50g": "salted_wafers",
    "Bingo Salted Wafers 10g": "salted_wafers",
    "Bingo Salted Wafers 20g": "salted_wafers",
    "Bingo Salted Wafers 50g": "salted_wafers",
    "Kurkure Puff 50g": "extruded_snacks",
    "Kurkure Puff 100g": "extruded_snacks",
    "Kurkure Rings 10g": "extruded_snacks",
    "Kurkure Rings 50g": "extruded_snacks",
    "Kurkure Rings 100g": "extruded_snacks",
    "Kurkure Masala Munch 10g": "extruded_snacks",
    "Kurkure Masala Munch 50g": "extruded_snacks",
    "Kurkure Masala Munch 100g": "extruded_snacks",
    "Cheetos Puff 10g": "extruded_snacks",
    "Cheetos Puff 50g": "extruded_snacks",
    "Cheetos Puff 100g": "extruded_snacks",
    "Cheetos Rings 10g": "extruded_snacks",
    "Cheetos Rings 50g": "extruded_snacks",
    "Cheetos Rings 100g": "extruded_snacks",
    "Cheetos Masala Munch 10g": "extruded_snacks",
    "Cheetos Masala Munch 50g": "extruded_snacks",
    "Cheetos Masala Munch 100g": "extruded_snacks",
    "Yellow Diamond Rings 10g": "extruded_snacks",
    "Yellow Diamond Rings 50g": "extruded_snacks",
    "Yellow Diamond Rings 100g": "extruded_snacks",
    "Yellow Diamond Puff 10g": "extruded_snacks",
    "Yellow Diamond Puff 100g": "extruded_snacks",
    "Yellow Diamond Masala Munch 50g": "extruded_snacks",
    "Yellow Diamond Masala Munch 100g": "extruded_snacks",
    "Haldiram's Aloo Bhujia 200g": "namkeen",
    "Haldiram's Aloo Bhujia 400g": "namkeen",
    "Bikaji Aloo Bhujia 200g": "namkeen",
    "Bikaji Aloo Bhujia 400g": "namkeen",
    "Haldiram's Moong Dal 200g": "namkeen",
    "Haldiram's Moong Dal 400g": "namkeen",
    "Bikaji Moong Dal 200g": "namkeen",
    "Bikaji Moong Dal 400g": "namkeen",
    "Haldiram's Navrattan Mixture 200g": "namkeen",
    "Haldiram's Navrattan Mixture 400g": "namkeen",
    "Bikaji Navrattan Mixture 200g": "namkeen",
    "Bikano Soan Papdi 250g": "indian_sweets",
    "Bikano Soan Papdi 1kg": "indian_sweets",
    "Haldiram's Soan Papdi 1kg": "indian_sweets",
    "Bikano Kaju Katli Box 500g": "indian_sweets",
    "Haldiram's Kaju Katli Box 500g": "indian_sweets",
    "Haldiram's Gulab Jamun Tin 250g": "indian_sweets",
    "Haldiram's Gulab Jamun Tin 500g": "indian_sweets",
    "Bikano Gulab Jamun Tin 250g": "indian_sweets",
    "Bikano Gulab Jamun Tin 1kg": "indian_sweets",
    "Haldiram's Rasgulla Tin 500g": "indian_sweets",
    "Haldiram's Rasgulla Tin 1kg": "indian_sweets",
    "Nestle Dairy Milk 10g": "chocolate",
    "Nestle Dairy Milk 40g": "chocolate",
    "Nestle Dairy Milk 100g": "chocolate",
    "Nestle KitKat 10g": "chocolate",
    "Nestle KitKat 40g": "chocolate",
    "Nestle KitKat 100g": "chocolate",
    "Cadbury KitKat 10g": "chocolate",
    "Cadbury KitKat 100g": "chocolate",
    "Amul KitKat 40g": "chocolate",
    "Amul KitKat 100g": "chocolate",
    "Cadbury Dairy Milk 40g": "chocolate",
    "Amul Dark Chocolate 10g": "chocolate",
    "Amul Dark Chocolate 40g": "chocolate",
    "Nestle Dark Chocolate 10g": "chocolate",
    "Nestle Dark Chocolate 40g": "chocolate",
    "Nestle Dark Chocolate 100g": "chocolate",
    "Cadbury Dark Chocolate 40g": "chocolate",
    "Perfetti Mango Bite Single Piece": "candy",
    "Perfetti Mango Bite Pack of 50": "candy",
    "Parle Mango Bite Single Piece": "candy",
    "Parle Mango Bite Pack of 50": "candy",
    "Kismi Mango Bite Single Piece": "candy",
    "Perfetti Melody Single Piece": "candy",
    "Perfetti Melody Pack of 50": "candy",
    "Parle Melody Single Piece": "candy",
    "Parle Melody Pack of 50": "candy",
    "Kismi Melody Single Piece": "candy",
    "Kismi Melody Pack of 50": "candy",
    "Pulse Melody Single Piece": "candy",
    "Perfetti Alpenliebe Single Piece": "candy",
    "Perfetti Alpenliebe Pack of 50": "candy",
    "Parle Alpenliebe Pack of 50": "candy",
    "Kismi Alpenliebe Single Piece": "candy",
    "Pulse Alpenliebe Pack of 50": "candy",
    "Pulse Kacha Mango Candy Single Piece": "candy",
    "Perfetti Kacha Mango Candy Single Piece": "candy",
    "Parle Kacha Mango Candy Pack of 50": "candy",
    "Kismi Kacha Mango Candy Single Piece": "candy",
    "Kismi Kacha Mango Candy Pack of 50": "candy",
    "Everest Turmeric Powder 50g": "turmeric_powder",
    "Everest Turmeric Powder 200g": "turmeric_powder",
    "Suhana Turmeric Powder 50g": "turmeric_powder",
    "Suhana Turmeric Powder 100g": "turmeric_powder",
    "Catch Turmeric Powder 200g": "turmeric_powder",
    "MDH Turmeric Powder 50g": "turmeric_powder",
    "MDH Turmeric Powder 200g": "turmeric_powder",
    "Everest Red Chilli Powder 100g": "red_chilli_powder",
    "Everest Red Chilli Powder 200g": "red_chilli_powder",
    "MDH Red Chilli Powder 50g": "red_chilli_powder",
    "MDH Red Chilli Powder 100g": "red_chilli_powder",
    "Catch Red Chilli Powder 100g": "red_chilli_powder",
    "Suhana Red Chilli Powder 50g": "red_chilli_powder",
    "Everest Coriander Powder 50g": "coriander_powder",
    "Everest Coriander Powder 200g": "coriander_powder",
    "Suhana Coriander Powder 50g": "coriander_powder",
    "Suhana Coriander Powder 100g": "coriander_powder",
    "Catch Coriander Powder 100g": "coriander_powder",
    "Catch Coriander Powder 200g": "coriander_powder",
    "MDH Coriander Powder 50g": "coriander_powder",
    "MDH Coriander Powder 200g": "coriander_powder",
    "Everest Jeera 100g": "jeera",
    "Everest Jeera 200g": "jeera",
    "Suhana Jeera 100g": "jeera",
    "Catch Jeera 100g": "jeera",
    "Catch Jeera 200g": "jeera",
    "MDH Jeera 100g": "jeera",
    "Everest Garam Masala 50g": "garam_masala",
    "Everest Garam Masala 100g": "garam_masala",
    "Everest Garam Masala 200g": "garam_masala",
    "Catch Garam Masala 50g": "garam_masala",
    "Catch Garam Masala 100g": "garam_masala",
    "Catch Garam Masala 200g": "garam_masala",
    "Pears Soap 75g": "bathing_soap",
    "Pears Soap 125g": "bathing_soap",
    "Dettol Soap 125g": "bathing_soap",
    "Lifebuoy Soap 125g": "bathing_soap",
    "Dove Soap 75g": "bathing_soap",
    "Dove Soap 125g": "bathing_soap",
    "Cinthol Soap 75g": "bathing_soap",
    "Cinthol Soap 200ml": "bathing_soap",
    "Dove Liquid Handwash 125g": "liquid_handwash",
    "Lifebuoy Liquid Handwash 75g": "liquid_handwash",
    "Dettol Liquid Handwash 75g": "liquid_handwash",
    "Dettol Liquid Handwash 125g": "liquid_handwash",
    "Pears Liquid Handwash 75g": "liquid_handwash",
    "Pears Liquid Handwash 125g": "liquid_handwash",
    "Cinthol Liquid Handwash 75g": "liquid_handwash",
    "Cinthol Liquid Handwash 125g": "liquid_handwash",
    "Dove Shampoo 100ml": "shampoo",
    "Dove Shampoo 200ml": "shampoo",
    "Dove Shampoo 650ml": "shampoo",
    "Sunsilk Shampoo 100ml": "shampoo",
    "Sunsilk Shampoo 200ml": "shampoo",
    "Sunsilk Shampoo 650ml": "shampoo",
    "Clinic Plus Shampoo 100ml": "shampoo",
    "Clinic Plus Shampoo 200ml": "shampoo",
    "Clinic Plus Shampoo 650ml": "shampoo",
    "Bajaj Almond Drops Hair Oil 100ml": "hair_oil",
    "Bajaj Almond Drops Hair Oil 250ml": "hair_oil",
    "Parachute Hair Oil 100ml": "hair_oil",
    "Parachute Hair Oil 250ml": "hair_oil",
    "Dabur Amla Hair Oil 100ml": "hair_oil",
    "Dabur Amla Hair Oil 250ml": "hair_oil",
    "Colgate Toothpaste 50g": "toothpaste",
    "Colgate Toothpaste 100g": "toothpaste",
    "Colgate Toothpaste 200g": "toothpaste",
    "Pepsodent Toothpaste 100g": "toothpaste",
    "Pepsodent Toothpaste 200g": "toothpaste",
    "Sensodyne Toothpaste 50g": "toothpaste",
    "Sensodyne Toothpaste 200g": "toothpaste",
    "Close-Up Toothpaste 100g": "toothpaste",
    "Close-Up Toothpaste 200g": "toothpaste",
    "Gillette Shaving Cream 70g": "shaving",
    "Gillette Shaving Cream Standard": "shaving",
    "Gillette Razors (Pack of 3) Standard": "shaving",
    "Old Spice Shaving Cream 70g": "shaving",
    "Old Spice Razors (Pack of 3) Standard": "shaving",
    "Exo Dishwash Bar 100g": "dishwash",
    "Exo Dishwash Bar 250ml": "dishwash",
    "Exo Dishwash Liquid 100g": "dishwash",
    "Exo Dishwash Liquid 250ml": "dishwash",
    "Vim Dishwash Bar 100g": "dishwash",
    "Vim Dishwash Bar 250ml": "dishwash",
    "Vim Dishwash Liquid 250ml": "dishwash",
    "Surf Excel Washing Powder 1kg": "detergent",
    "Surf Excel Washing Powder 1L": "detergent",
    "Surf Excel Detergent Liquid 500g": "detergent",
    "Surf Excel Detergent Liquid 1kg": "detergent",
    "Ariel Washing Powder 500g": "detergent",
    "Ariel Washing Powder 1kg": "detergent",
    "Ariel Detergent Liquid 500g": "detergent",
    "Ariel Detergent Liquid 1L": "detergent",
    "Ariel Detergent Liquid 1kg": "detergent",
    "Rin Washing Powder 500g": "detergent",
    "Rin Washing Powder 1kg": "detergent",
    "Tide Washing Powder 500g": "detergent",
    "Tide Detergent Liquid 1L": "detergent",
    "Lizol Floor Cleaner 1L": "floor_cleaner",
    "Domex Floor Cleaner 500ml": "floor_cleaner",
    "Domex Floor Cleaner 1L": "floor_cleaner",
    "Harpic Floor Cleaner 500ml": "floor_cleaner",
    "Colin Floor Cleaner 1L": "floor_cleaner",
    "Lizol Toilet Cleaner 500ml": "toilet_cleaner",
    "Domex Toilet Cleaner 500ml": "toilet_cleaner",
    "Colin Toilet Cleaner 500ml": "toilet_cleaner",
    "Colin Toilet Cleaner 1L": "toilet_cleaner",
    "Lizol Glass Cleaner 500ml": "glass_cleaner",
    "Colin Glass Cleaner 500ml": "glass_cleaner",
}


def get_or_create_category(db: Session, name: str) -> Category:
    cat = db.query(Category).filter(Category.name == name).first()
    if not cat:
        cat = Category(name=name)
        db.add(cat)
        db.flush()
    return cat


def remap(shop_email: str):
    db: Session = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.email == shop_email).first()
        if not shop:
            print(f"[ERROR] No shop found with email '{shop_email}'")
            return

        print(f"[OK] Found shop: {shop.shop_name} (id={shop.shop_id})")

        # Pre-cache all categories
        category_cache = {}

        updated = unchanged = not_found = 0

        for product_name, new_cat_name in CATEGORY_MAP.items():
            product = db.query(Product).filter(
                Product.shop_id      == shop.shop_id,
                Product.product_name == product_name
            ).first()

            if not product:
                not_found += 1
                continue

            # Resolve category_id
            if new_cat_name not in category_cache:
                cat = get_or_create_category(db, new_cat_name)
                category_cache[new_cat_name] = cat.category_id

            new_category_id = category_cache[new_cat_name]

            if product.category_id == new_category_id:
                unchanged += 1
                continue

            product.category_id = new_category_id
            db.add(product)
            print(f"  [UPDATE] {product_name[:55]:<55} → {new_cat_name}")
            updated += 1

        db.commit()
        print(f"\n[DONE] Updated: {updated} | Unchanged: {unchanged} | Not in DB: {not_found}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    remap(shop_email=args.email)
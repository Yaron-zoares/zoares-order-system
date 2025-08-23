#!/usr/bin/env python3
"""
Data Migration Script
מעביר נתונים ממסד הנתונים הישן (SQLite) למודלים החדשים של SQLAlchemy
"""

import sqlite3
import json
from datetime import datetime
from database import SessionLocal, Customer, Order, Product, SystemEvent
from services import CustomerService, ProductService

def migrate_customers():
    """העברת לקוחות ממסד הנתונים הישן"""
    print("מעביר לקוחות...")
    
    # Connect to old database
    old_conn = sqlite3.connect('zoares_central.db')
    old_cursor = old_conn.cursor()
    
    # Get customers from old database
    old_cursor.execute("SELECT name, phone, address, total_orders, total_amount FROM customers")
    old_customers = old_cursor.fetchall()
    
    # Connect to new database
    db = SessionLocal()
    
    migrated_count = 0
    for old_customer in old_customers:
        name, phone, address, total_orders, total_amount = old_customer
        
        # Check if customer already exists
        existing = db.query(Customer).filter(Customer.phone == phone).first()
        if existing:
            print(f"לקוח {name} כבר קיים, מעדכן...")
            existing.total_orders = total_orders or 0
            existing.total_amount = total_amount or 0.0
            existing.updated_at = datetime.now()
        else:
            print(f"יוצר לקוח חדש: {name}")
            new_customer = Customer(
                name=name,
                phone=phone,
                address=address,
                total_orders=total_orders or 0,
                total_amount=total_amount or 0.0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(new_customer)
        
        migrated_count += 1
    
    db.commit()
    db.close()
    old_conn.close()
    
    print(f"הועברו {migrated_count} לקוחות בהצלחה!")
    return migrated_count

def migrate_products():
    """העברת מוצרים ממסד הנתונים הישן"""
    print("מעביר מוצרים...")
    
    # Product categories restored to the original application set
    PRODUCT_CATEGORIES = {
        "עופות": [
            "עוף שלם",
            "חזה עוף",
            "שניצל עוף",
            "כנפיים",
            "כרעיים עוף",
            "ירכיים",
            "שוקיים עוף",
            "קורקבן עוף",
            "טחול עוף",
            "כבד עוף",
            "לב עוף",
            "עוף טחון",
            "טחון מיוחד (שווארמה נקבה, פרגית וחזה עוף)",
            "שווארמה עוף (פרגיות)"
        ],
        "בשר": [
            "בשר בקר טחון",
            "צלעות בקר",
            "בשר כבש",
            "המבורגר הבית",
            "טחון קוקטייל הבית",
            "בשר עגל טחון",
            "בשר עגל טחון עם שומן כבש",
            "פילה מדומה",
            "פילה פרמיום",
            "צלעות",
            "בשר שריר",
            "אונטריב",
            "רגל פרה",
            "אצבעות אנטריקוט",
            "ריבס אנטריקוט",
            "אסאדו עם עצם מקוצב 4 צלעות",
            "צלי כתף",
            "בננות שריר",
            "אנטריקוט פיידלוט פרימיום",
            "כבד אווז",
            "שקדי עגל גרון /לב",
            "עצמות מח",
            "גידי רגל",
            "כתף כבש",
            "צלעות טלה פרימיום בייבי",
            "שומן גב כבש טרי  בדצ בית יוסף"
        ],
        "דגים": [
            "סלמון",
            "טונה",
            "מושט",
            "אחר"
        ],
        "הודו": [
            "הודו שלם נקבה",
            "חזה הודו נקבה",
            "שווארמה הודו נקבה",
            "קורקבן הודו נקבה",
            "כנפיים הודו נקבה",
            "שוקיים הודו נקבה",
            "לבבות הודו נקבה",
            "גרון הודו",
            "ביצי הודו"
        ],
        "המבורגר הבית": [
            "המבורגר 160 גרם",
            "המבורגר 220 גרם"
        ],
        "אחר": [
            "נקניקיות עוף",
            "נקניקיות חריפות (מרגז)",
            "צ׳יפס מארז 2.5 קג תפוגן",
            "צ׳נגו מוסדי 1.25 קג מארז",
            "במיה כפתורים"
        ]
    }
    
    # Weight and unit products restored to the original application sets
    WEIGHT_PRODUCTS = {
        "חזה עוף", "שניצל עוף", "כנפיים", "כרעיים עוף", "קורקבן עוף", "טחול עוף", "כבד עוף", "לב עוף",
        "עוף טחון", "טחון מיוחד (שווארמה נקבה, פרגית וחזה עוף)", "בשר בקר טחון", "צלעות בקר", "בשר כבש",
        "טחון קוקטייל הבית", "בשר עגל טחון", "בשר עגל טחון עם שומן כבש", "פילה מדומה", "צלעות",
        "בשר שריר", "אונטריב", "רגל פרה", "אצבעות אנטריקוט", "ריבס אנטריקוט",
        "אסאדו עם עצם מקוצב 4 צלעות", "צלי כתף", "בננות שריר", "אנטריקוט פיידלוט פרימיום",
        "כבד אווז", "שקדי עגל גרון /לב", "עצמות מח", "גידי רגל", "צלעות טלה פרימיום בייבי",
        "שומן גב כבש טרי  בדצ בית יוסף"
    }
    
    UNIT_PRODUCTS = {
        "עוף שלם", "נקניקיות עוף", "שווארמה עוף (פרגיות)", "הודו שלם נקבה", "חזה הודו נקבה",
        "שווארמה הודו נקבה", "קורקבן הודו נקבה", "כנפיים הודו נקבה", "שוקיים הודו נקבה", "גרון הודו",
        "כנפיים עוף", "ירכיים", "שוקיים עוף", "לבבות הודו נקבה", "ביצי הודו", "המבורגר הבית", "המבורגר",
        "נקניקיות", "נקניק חריף", "סלמון", "טונה", "מושט", "כתף כבש", "המבורגר 160 גרם", "המבורגר 220 גרם"
    }
    
    # Connect to new database
    db = SessionLocal()
    
    migrated_count = 0
    for category, products in PRODUCT_CATEGORIES.items():
        for product_name in products:
            # Check if product already exists
            existing = db.query(Product).filter(Product.name == product_name).first()
            if existing:
                print(f"מוצר {product_name} כבר קיים, מדלג...")
                continue
            
            # Determine product type and pricing
            is_weight_product = product_name in WEIGHT_PRODUCTS
            is_unit_product = product_name in UNIT_PRODUCTS
            
            if is_weight_product:
                unit_type = "ק\"ג"
                price_per_kg = 45.0  # Default price, can be updated later
                price_per_unit = None
            elif is_unit_product:
                unit_type = "יחידות"
                price_per_kg = None
                price_per_unit = 15.0  # Default price, can be updated later
            else:
                # Default to weight product
                unit_type = "ק\"ג"
                price_per_kg = 40.0
                price_per_unit = None
            
            print(f"יוצר מוצר חדש: {product_name} ({category})")
            new_product = Product(
                name=product_name,
                category=category,
                price_per_kg=price_per_kg,
                price_per_unit=price_per_unit,
                unit_type=unit_type,
                is_weight_product=is_weight_product,
                is_unit_product=is_unit_product,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(new_product)
            migrated_count += 1
    
    db.commit()
    db.close()
    
    print(f"הועברו {migrated_count} מוצרים בהצלחה!")
    return migrated_count

def migrate_orders():
    """העברת הזמנות ממסד הנתונים הישן"""
    print("מעביר הזמנות...")
    
    # Connect to old database
    old_conn = sqlite3.connect('zoares_central.db')
    old_cursor = old_conn.cursor()
    
    # Get orders from old database
    old_cursor.execute("""
        SELECT customer_name, customer_phone, customer_address, items, 
               total_amount, delivery_cost, final_total, notes, created_at
        FROM orders
    """)
    old_orders = old_cursor.fetchall()
    
    # Connect to new database
    db = SessionLocal()
    
    migrated_count = 0
    for old_order in old_orders:
        customer_name, customer_phone, customer_address, items_json, \
        total_amount, delivery_cost, final_total, notes, created_at = old_order
        
        try:
            # Parse items JSON
            if items_json:
                items_data = json.loads(items_json)
            else:
                items_data = []
            
            # Create order items
            order_items = []
            for item in items_data:
                order_items.append({
                    "product_name": item.get("product", ""),
                    "quantity": item.get("quantity", 0),
                    "unit": item.get("unit", "יחידות"),
                    "price_per_unit": item.get("price_per_unit", 0),
                    "total_price": item.get("total_price", 0),
                    "cutting_instructions": item.get("cutting_instructions", "")
                })
            
            # Check if order already exists
            existing = db.query(Order).filter(
                Order.customer_phone == customer_phone,
                Order.created_at == created_at
            ).first()
            
            if existing:
                print(f"הזמנה ל{customer_name} כבר קיימת, מדלג...")
                continue
            
            print(f"יוצר הזמנה חדשה ל: {customer_name}")
            
            # Find customer
            customer = db.query(Customer).filter(Customer.phone == customer_phone).first()
            customer_id = customer.id if customer else None
            
            new_order = Order(
                customer_id=customer_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_address=customer_address,
                items=json.dumps(order_items, ensure_ascii=False),
                total_amount=total_amount or 0.0,
                delivery_cost=delivery_cost or 0.0,
                final_total=final_total or 0.0,
                notes=notes,
                status="pending",
                created_at=created_at or datetime.now(),
                updated_at=datetime.now()
            )
            db.add(new_order)
            migrated_count += 1
            
        except Exception as e:
            print(f"שגיאה בהעברת הזמנה ל{customer_name}: {str(e)}")
            continue
    
    db.commit()
    db.close()
    old_conn.close()
    
    print(f"הועברו {migrated_count} הזמנות בהצלחה!")
    return migrated_count

def create_system_events():
    """יצירת אירועי מערכת ראשוניים"""
    print("יוצר אירועי מערכת ראשוניים...")
    
    db = SessionLocal()
    
    # Create initial system event
    initial_event = SystemEvent(
        event_type="system_initialized",
        entity_id=None,
        entity_type="system",
        data=json.dumps({
            "message": "מערכת הותקנה והועברו נתונים ממסד הנתונים הישן",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False),
        created_at=datetime.now()
    )
    db.add(initial_event)
    
    db.commit()
    db.close()
    
    print("נוצרו אירועי מערכת ראשוניים בהצלחה!")

def main():
    """הפעלת תהליך ההעברה הראשי"""
    print("מתחיל תהליך העברת נתונים...")
    print("=" * 50)
    
    try:
        # Migrate data in order
        customers_count = migrate_customers()
        products_count = migrate_products()
        orders_count = migrate_orders()
        
        # Create system events
        create_system_events()
        
        print("=" * 50)
        print("תהליך ההעברה הושלם בהצלחה!")
        print(f"סה\"כ הועברו:")
        print(f"- {customers_count} לקוחות")
        print(f"- {products_count} מוצרים")
        print(f"- {orders_count} הזמנות")
        print("\nהמערכת מוכנה לשימוש!")
        
    except Exception as e:
        print(f"שגיאה בתהליך ההעברה: {str(e)}")
        raise

if __name__ == "__main__":
    main()

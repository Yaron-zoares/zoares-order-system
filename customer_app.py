import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import webbrowser
import sys
import os

# הגדרת הדף - חייב להיות הפקודה הראשונה של Streamlit
st.set_page_config(
    page_title="Zoares - הזמנת מוצרים",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import database functions
from database import (
    load_orders, save_order, find_or_create_customer, 
    update_customer_stats, cleanup_old_customers
)

# Add backend directory to path for API client
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
try:
    from backend.client import create_api_client, auto_refresh_on_updates, migrate_existing_data
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    st.warning("⚠️ לא ניתן לטעון את קליינט ה-API. המערכת תפעל במצב offline.")

# הגדרת CSS מותאם אישית
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .product-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .cart-item {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.25rem 0;
    }
    .price-display {
        font-weight: bold;
        color: #28a745;
        font-size: 1.1em;
    }
    .search-highlight {
        background-color: #fff3cd;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# הגדרת משתני session state
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'customer_first_name' not in st.session_state:
    st.session_state.customer_first_name = ""
if 'customer_last_name' not in st.session_state:
    st.session_state.customer_last_name = ""
if 'customer_street_name' not in st.session_state:
    st.session_state.customer_street_name = ""
if 'customer_street_number' not in st.session_state:
    st.session_state.customer_street_number = ""
if 'customer_floor' not in st.session_state:
    st.session_state.customer_floor = ""
if 'customer_apartment' not in st.session_state:
    st.session_state.customer_apartment = ""
if 'customer_city' not in st.session_state:
    st.session_state.customer_city = ""
if 'customer_phone' not in st.session_state:
    st.session_state.customer_phone = ""
if 'customer_delivery_notes' not in st.session_state:
    st.session_state.customer_delivery_notes = ""
if 'customer_kitchen_notes' not in st.session_state:
    st.session_state.customer_kitchen_notes = ""
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "כל הקטגוריות"
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'sidebar_search_query' not in st.session_state:
    st.session_state.sidebar_search_query = ""
if 'clear_search_flag' not in st.session_state:
    st.session_state.clear_search_flag = False
if 'clear_sidebar_search_flag' not in st.session_state:
    st.session_state.clear_sidebar_search_flag = False
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "הזמנת מוצרים"

# הגדרת קטגוריות המוצרים - מתוקן לפי הקובץ המקורי
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

# הגדרת מוצרים לפי משקל - מתוקן לפי הקובץ המקורי
WEIGHT_PRODUCTS = {
    "חזה עוף": True,
    "שניצל עוף": True,
    "כנפיים": True,
    "כרעיים עוף": True,
    "קורקבן עוף": True,
    "טחול עוף": True,
    "כבד עוף": True,
    "לב עוף": True,
    "עוף טחון": True,
    "טחון מיוחד (שווארמה נקבה, פרגית וחזה עוף)": True,
    "בשר בקר טחון": True,
    "צלעות בקר": True,
    "בשר כבש": True,
    "טחון קוקטייל הבית": True,
    "בשר עגל טחון": True,
    "בשר עגל טחון עם שומן כבש": True,
    "פילה מדומה": True,
    "צלעות": True,
    "בשר שריר": True,
    "אונטריב": True,
    "רגל פרה": True,
    "אצבעות אנטריקוט": True,
    "ריבס אנטריקוט": True,
    "אסאדו עם עצם מקוצב 4 צלעות": True,
    "צלי כתף": True,
    "בננות שריר": True,
    "אנטריקוט פיידלוט פרימיום": True,
    "כבד אווז": True,
    "שקדי עגל גרון /לב": True,
    "עצמות מח": True,
    "גידי רגל": True,
    "צלעות טלה פרימיום בייבי": True,
    "שומן גב כבש טרי  בדצ בית יוסף": True
}

# הגדרת מוצרים לפי יחידות - מתוקן לפי הקובץ המקורי
UNIT_PRODUCTS = {
    "עוף שלם": True,
    "נקניקיות עוף": True,
    "המבורגר עוף": True,
    "שווארמה עוף (פרגיות)": True,
    "הודו שלם נקבה": True,
    "חזה הודו נקבה": True,
    "שווארמה הודו נקבה": True,
    "קורקבן הודו נקבה": True,
    "כנפיים הודו נקבה": True,
    "שוקיים הודו נקבה": True,
    "גרון הודו": True,
    "כנפיים עוף": True,
    "ירכיים": True,
    "שוקיים עוף": True,
    "לבבות הודו נקבה": True,
    "ביצי הודו": True,
    "המבורגר הבית": True,
    "המבורגר": True,
    "נקניקיות": True,
    "נקניק חריף": True,
    "סלמון": True,
    "טונה": True,
    "מושט": True,
    "כתף כבש": True,
    "המבורגר 160 גרם": True,
    "המבורגר 220 גרם": True
}

# הגדרת מחירים - מתוקן לפי הקובץ המקורי
PRODUCT_PRICES = {
    "עוף שלם": 50.0,
    "חזה עוף": 40.0,
    "שניצל עוף": 35.0,
    "כנפיים": 15.0,
    "כרעיים": 10.0,
    "כרעיים עוף": 12.0,
    "ירכיים": 18.0,
    "ירכיים עוף": 20.0,
    "עוף עם עור": 45.0,
    "עוף בלי עור": 42.0,
    "כבד עוף": 20.0,
    "לב עוף": 25.0,
    "עוף טחון": 30.0,
    "נקניקיות עוף": 10.0,
    "המבורגר עוף": 20.0,
    "שווארמה עוף (פרגיות)": 15.0,
    "שווארמה הודו": 25.0,
    "הודו שלם": 45.0,
    "חזה הודו": 35.0,
    "קורקבן הודו": 20.0,
    "כנפיים הודו": 18.0,
    "שוקיים הודו": 15.0,
    "ביצי עוף": 10.0,
    "ביצי הודו": 12.0,
    "בשר בקר טחון": 60.0,
    "סטייק אנטריקוט": 55.0,
    "צלעות בקר": 50.0,
    "בשר כבש": 70.0,
    "המבורגר בקר": 20.0,
    "בשר טחון מעורב": 65.0,
    "בשר עגל": 50.0,
    "בשר עגל טחון": 55.0,
    "בשר עגל טחון עם שומן כבש": 65.0,
    "רגל פרה": 40.0,
    "עצמות": 25.0,
    "גידים": 45.0,
    "סלמון": 80.0,
    "טונה": 70.0,
    "מושט": 65.0,
    "אחר": 50.0,
    "ביצים טריות": 15.0,
    "חלב": 10.0,
    "גבינה": 20.0,
    "יוגורט": 15.0,
    "חמאה": 15.0,
    "שמן זית": 20.0,
    "דבש": 10.0,
    "קמח": 10.0,
    "סוכר": 10.0,
    "מלח": 5.0,
    "המבורגר הבית": 20.0,
    "טחון קוקטייל הבית": 65.0,
    "הודו שלם נקבה": 45.0,
    "חזה הודו נקבה": 35.0,
    "שווארמה הודו נקבה": 25.0,
    "קורקבן הודו נקבה": 20.0,
    "כנפיים הודו נקבה": 18.0,
    "שוקיים הודו נקבה": 15.0,
    "לבבות הודו נקבה": 25.0,
    "גרון הודו": 20.0,
    "ביצי הודו": 12.0,
    "המבורגר 160 גרם": 20.0,
    "המבורגר 220 גרם": 25.0,
    "טחון מיוחד (שווארמה נקבה, פרגית וחזה עוף)": 30.0,
    "קורקבן עוף": 20.0,
    "טחול עוף": 15.0,
    "לב עוף": 25.0,
    "נקניקיות חריפות (מרגז)": 12.0,
    "צ׳יפס מארז 2.5 קג תפוגן": 25.0,
    "צ׳נגו מוסדי 1.25 קג מארז": 15.0,
    "במיה כפתורים": 8.0
}

# הגדרת אפשרויות חיתוך - מתוקן לפי הקובץ המקורי
CUTTABLE_PRODUCTS = {
    "עוף שלם": {
        "name": "עוף שלם",
        "options": ["שלם", "פרוס לשניצל", "פרוס ל-8 חלקים", "עוף פרוס לשניצל ללא עור", "עוף פרוס ל-8 חלקים ללא עור"],
        "default": "שלם"
    },
    "חזה עוף": {
        "name": "חזה עוף",
        "options": ["שלם", "פרוס", "קוביות", "רצועות למוקפץ"],
        "default": "שלם"
    },
    "כרעיים עוף": {
        "name": "כרעיים עוף",
        "options": ["שלם", "חצוי", "שלם בלי עור", "חצוי בלי עור"],
        "default": "שלם"
    },
    "כנפיים": {
        "name": "כנפיים",
        "options": ["שלם", "חצוי"],
        "default": "שלם"
    },
    "שניצל עוף": {
        "name": "שניצל עוף",
        "options": ["שניצל פרוס עבה", "שניצל פרוס דק"],
        "default": "שניצל פרוס עבה"
    },
    "ירכיים": {
        "name": "ירכיים",
        "options": ["עם עור", "בלי עור"],
        "default": "עם עור"
    },
    "שוקיים עוף": {
        "name": "שוקיים עוף",
        "options": ["שוקיים עם עור", "שוקיים בלי עור"],
        "default": "שוקיים עם עור"
    },
    "צלעות בקר": {
        "name": "צלעות בקר",
        "options": ["שלם", "פרוס", "קוביות", "טחון"],
        "default": "טחון"
    },
    "בשר כבש": {
        "name": "בשר כבש",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "בשר עגל טחון": {
        "name": "בשר עגל טחון",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "בשר עגל טחון עם שומן כבש": {
        "name": "בשר עגל טחון עם שומן כבש",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "פילה מדומה": {
        "name": "פילה מדומה",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "פילה פרמיום": {
        "name": "פילה פרמיום",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "צלעות": {
        "name": "צלעות",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "בשר שריר": {
        "name": "בשר שריר",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "אונטריב": {
        "name": "אונטריב",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "שווארמה עוף (פרגיות)": {
        "name": "שווארמה עוף (פרגיות)",
        "options": ["חתוך לשיפודים", "רצועות", "פרוס דק", "סטיק פרגית"],
        "default": "סטיק פרגית"
    },
    "שווארמה הודו נקבה": {
        "name": "שווארמה הודו נקבה",
        "options": ["חתוך לשיפודים", "רצועות", "פרוס", "שלם"],
        "default": "שלם"
    },
    "צלי כתף": {
        "name": "צלי כתף",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "בננות שריר": {
        "name": "בננות שריר",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    }
}

def get_product_unit(product_name):
    """קביעת יחידת המידה של מוצר (משקל או יחידות)"""
    # הסר הוראות חיתוך מהשם אם קיימות
    base_name = product_name.split(' - ')[0] if ' - ' in product_name else product_name
    
    if base_name in WEIGHT_PRODUCTS:
        return "ק\"ג"
    elif base_name in UNIT_PRODUCTS:
        return "יחידות"
    else:
        # ברירת מחדל
        return "ק\"ג"

def levenshtein_distance(s1, s2):
    """חישוב מרחק Levenshtein בין שתי מחרוזות"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def smart_search(query, products, max_distance=2):
    """חיפוש חכם עם תיקון שגיאות כתיב והצעות דומות"""
    if not query:
        return []
    
    # נסה חיפוש דרך ה-API אם זמין
    if API_AVAILABLE:
        try:
            api_client = create_api_client()
            api_results = api_client.search_products(query)
            if api_results:
                return api_results
        except Exception as e:
            st.debug(f"API search failed: {e}")
    
    # חיפוש מקומי עם Levenshtein
    results = []
    query_lower = query.lower()
    
    for product in products:
        product_lower = product.lower()
        
        # חיפוש מדויק
        if query_lower in product_lower:
            results.append((product, 0, "מדויק"))
            continue
        
        # חיפוש עם שגיאות כתיב
        distance = levenshtein_distance(query_lower, product_lower)
        if distance <= max_distance:
            if distance == 1:
                similarity = "דומה מאוד"
            elif distance == 2:
                similarity = "דומה"
            else:
                similarity = "דומה חלקית"
            
            results.append((product, distance, similarity))
    
    # מיון לפי דיוק
    results.sort(key=lambda x: (x[1], x[0]))
    return results

def get_cutting_instructions(product_name):
    """קבלת הוראות חיתוך למוצר"""
    # בדוק אם המוצר כולל הוראות חיתוך
    if ' - ' in product_name:
        base_name = product_name.split(' - ')[0]
        cutting_option = product_name.split(' - ')[1]
        return cutting_option
    return None

def calculate_cart_weight():
    """חישוב משקל העגלה"""
    total_weight = 0
    for product, details in st.session_state.cart.items():
        product_name = product.split(' - ')[0] if ' - ' in product else product
        
        if product_name in WEIGHT_PRODUCTS:
            total_weight += details['quantity']
        # עבור יחידות לא מוסיפים למשקל
    
    return round(total_weight, 2)

def add_to_cart(product_name, quantity, cutting_instructions=None):
    """הוספת מוצר לעגלה"""
    if cutting_instructions:
        full_name = f"{product_name} - {cutting_instructions}"
    else:
        full_name = product_name
    
    if full_name in st.session_state.cart:
        st.session_state.cart[full_name]['quantity'] += quantity
    else:
        # קביעת מחיר מהרשימה המוגדרת
        price = PRODUCT_PRICES.get(product_name, 50.0)  # ברירת מחדל 50 ש"ח
        st.session_state.cart[full_name] = {
            'quantity': quantity,
            'price': price,
            'unit': get_product_unit(product_name)
        }

def remove_from_cart(product_name):
    """הסרת מוצר מהעגלה"""
    if product_name in st.session_state.cart:
        del st.session_state.cart[product_name]

def clear_cart():
    """ניקוי העגלה"""
    st.session_state.cart = {}

def save_order_with_customer():
    """שומר הזמנה עם פרטי לקוח"""
    # יצירת קליינט API
    try:
        from backend.client import create_api_client
        api_client = create_api_client()
    except Exception as e:
        st.warning(f"לא ניתן ליצור קליינט API: {str(e)}")
        api_client = None
    
    # הכנת כתובת מלאה
    address_parts = []
    if st.session_state.customer_street_name:
        address_parts.append(st.session_state.customer_street_name)
    if st.session_state.customer_street_number:
        address_parts.append(st.session_state.customer_street_number)
    if st.session_state.customer_city:
        address_parts.append(st.session_state.customer_city)
    
    full_address = ", ".join(address_parts) if address_parts else "כתובת לא צוינה"
    full_name = f"{st.session_state.customer_first_name} {st.session_state.customer_last_name}"
    
    # בדיקת שדות חובה
    if not st.session_state.customer_first_name or not st.session_state.customer_last_name or not st.session_state.customer_phone:
        st.error("יש להזין שם פרטי, שם משפחה ומספר טלפון של הלקוח")
        return False
    
    if not st.session_state.cart:
        st.error("העגלה ריקה")
        return False
    
    # ולידציה: מספר טלפון ספרתי בלבד
    if not st.session_state.customer_phone.isdigit():
        st.error("מספר הטלפון חייב להכיל ספרות בלבד")
        return False
    
    # נסה לשמור דרך השרת החדש
    if api_client:
        # בדיקה שהשרת זמין
        if not api_client.health_check():
            st.warning("⚠️ השרת לא זמין כרגע. המערכת תנסה לשמור במסד הנתונים המקומי.")
            api_client = None
        else:
            st.success("✅ השרת זמין - שומר דרך השרת החדש")
    
    if api_client:
        try:
            # הכנת נתוני ההזמנה לשרת
            items = []
            total_amount = 0.0
            for product, details in st.session_state.cart.items():
                unit = get_product_unit(product.split(' - ')[0] if ' - ' in product else product)
                price = details.get('price', 0)
                quantity = details['quantity']
                item_total = price * quantity
                total_amount += item_total
                
                # וידוא שכל השדות הנדרשים קיימים
                item = {
                    "product_name": str(product),
                    "quantity": float(quantity),
                    "unit": str(unit),
                    "price_per_unit": float(price),
                    "total_price": float(item_total),
                    "cutting_instructions": ""
                }
                
                # בדיקה שכל השדות תקינים
                if not item["product_name"]:
                    item["product_name"] = "מוצר לא ידוע"
                if item["quantity"] <= 0:
                    item["quantity"] = 1.0
                if not item["unit"]:
                    item["unit"] = "יחידה"
                if item["price_per_unit"] < 0:
                    item["price_per_unit"] = 0.0
                if item["total_price"] < 0:
                    item["total_price"] = 0.0
                
                items.append(item)
            
            # חישוב סכומים
            delivery_cost = 0.0  # ברירת מחדל
            final_total = total_amount + delivery_cost
            
            # בדיקה שהסכומים תקינים
            if total_amount <= 0:
                st.warning("⚠️ סכום ההזמנה הוא 0 או שלילי. בדוק שהמחירים נקבעו נכון.")
                # נסה לחשב מחדש מהמחירים המוגדרים
                recalculated_total = 0.0
                for product, details in st.session_state.cart.items():
                    base_product = product.split(' - ')[0] if ' - ' in product else product
                    default_price = PRODUCT_PRICES.get(base_product, 50.0)
                    recalculated_total += default_price * details['quantity']
                
                if recalculated_total > 0:
                    total_amount = recalculated_total
                    final_total = total_amount + delivery_cost
                    st.info(f"💰 הסכום חושב מחדש: {total_amount} ש\"ח")
                else:
                    st.error("❌ לא ניתן לחשב סכום תקין להזמנה")
                    return False
            
            # הכנת נתוני ההזמנה בפורמט הנכון לשרת
            order_data = {
                "customer_name": str(full_name),
                "customer_phone": str(st.session_state.customer_phone),
                "customer_address": str(full_address) if full_address else "",
                "items": items,  # זה כבר רשימה של פריטים בפורמט הנכון
                "total_amount": float(total_amount),
                "delivery_cost": float(delivery_cost),
                "final_total": float(final_total),
                "notes": str((st.session_state.customer_delivery_notes or "") + " " + (st.session_state.customer_kitchen_notes or "")).strip()
            }
            
            # וידוא שכל השדות הם מהסוג הנכון
            if not order_data["customer_name"] or not order_data["customer_phone"]:
                st.error("❌ שם הלקוח ומספר הטלפון הם שדות חובה")
                return False
            
            # בדיקה שהפריטים לא ריקים
            if not items or len(items) == 0:
                st.error("❌ אין פריטים בהזמנה")
                return False
            
            # בדיקה שהסכומים תקינים
            if total_amount <= 0:
                st.error("❌ סכום ההזמנה חייב להיות גדול מ-0")
                return False
            
            # נסה ליצור לקוח או למצוא קיים
            try:
                customer = api_client.create_or_get_customer(
                    full_name,
                    st.session_state.customer_phone,
                    full_address
                )
                
                if customer.get("error"):
                    st.warning(f"שגיאה ביצירת/מציאת לקוח: {customer['error']}")
                    raise Exception(f"שגיאה בלקוח: {customer['error']}")
                
            except AttributeError as e:
                st.warning("השרת לא תומך בפונקציה create_or_get_customer")
                raise Exception("פונקציה לא נתמכת בשרת")
            except Exception as e:
                st.warning(f"שגיאה ביצירת/מציאת לקוח: {str(e)}")
                raise e
            
            # לוגים לדיבוג
            st.info("📤 שולח הזמנה לשרת...")
            with st.expander("🔍 צפה בנתוני ההזמנה שנשלחים לשרת"):
                st.json(order_data)
            
            # בדיקה שהנתונים הם מילון ולא רשימה
            if not isinstance(order_data, dict):
                st.error(f"❌ שגיאה: order_data הוא {type(order_data)}, אמור להיות dict")
                raise Exception(f"סוג נתונים שגוי: {type(order_data)}")
            
            # בדיקה שכל השדות הנדרשים קיימים
            required_fields = ["customer_name", "customer_phone", "items", "total_amount", "delivery_cost", "final_total"]
            missing_fields = [field for field in required_fields if field not in order_data]
            if missing_fields:
                st.error(f"❌ שדות חסרים: {missing_fields}")
                raise Exception(f"שדות חסרים: {missing_fields}")
            
            # בדיקה שמבנה הפריטים נכון
            if not isinstance(order_data["items"], list):
                st.error(f"❌ שגיאה: items הוא {type(order_data['items'])}, אמור להיות list")
                raise Exception(f"מבנה פריטים שגוי: {type(order_data['items'])}")
            
            # בדיקה שכל פריט הוא מילון עם השדות הנדרשים
            for i, item in enumerate(order_data["items"]):
                if not isinstance(item, dict):
                    st.error(f"❌ פריט {i} הוא {type(item)}, אמור להיות dict")
                    raise Exception(f"פריט {i} אינו מילון")
                
                item_required_fields = ["product_name", "quantity", "unit", "price_per_unit", "total_price"]
                missing_item_fields = [field for field in item_required_fields if field not in item]
                if missing_item_fields:
                    st.error(f"❌ שדות חסרים בפריט {i}: {missing_item_fields}")
                    raise Exception(f"שדות חסרים בפריט {i}: {missing_item_fields}")
            
            # שמירת ההזמנה
            order = api_client.create_order(order_data)
            
            if order and not order.get("error"):
                st.success("✅ ההזמנה נשמרה בהצלחה דרך השרת החדש!")
                st.balloons()
                clear_cart()
                return True
            else:
                error_msg = order.get("error", "שגיאה לא ידועה") if order else "לא התקבלה תגובה מהשרת"
                st.error(f"❌ שגיאה בשמירת ההזמנה בשרת: {error_msg}")
                raise Exception(f"שגיאת שרת: {error_msg}")
            
        except Exception as e:
            st.warning(f"⚠️ שמירה דרך השרת החדש נכשלה: {str(e)}")
            st.info("🔄 המערכת תנסה לשמור במסד הנתונים המקומי")
    else:
        st.info("🔄 השרת לא זמין, שומר במסד הנתונים המקומי")
    
    # נסה לשמור במסד הנתונים המקומי
    try:
        # יצירת או מציאת לקוח (טלפון, שם מלא)
        customer = find_or_create_customer(
            st.session_state.customer_phone,
            full_name
        )
        
        # שמירת ההזמנה
        order_data = {
            'customer_name': full_name,
            'phone': st.session_state.customer_phone,
            'address': full_address,
            'delivery_notes': st.session_state.customer_delivery_notes,
            'kitchen_notes': st.session_state.customer_kitchen_notes,
            'items': st.session_state.cart,
            'total_amount': 0,
            'customer_id': customer,
            'status': 'pending',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        order = save_order(order_data)
        
        if order:
            st.success("✅ ההזמנה נשמרה בהצלחה במסד הנתונים המקומי!")
            st.balloons()
            clear_cart()
            return True
            
    except Exception as e:
        st.error(f"❌ שגיאה בשמירת ההזמנה במסד הנתונים המקומי: {str(e)}")
        # נסה לתקן קונפליקטים אם יש
        if "UNIQUE constraint failed" in str(e):
            try:
                from database import fix_order_id_conflicts
                st.info("🔧 מנסה לתקן קונפליקטים במסד הנתונים...")
                result = fix_order_id_conflicts()
                st.info(f"📋 תוצאות תיקון קונפליקטים: {result}")
                # נסה שוב
                order = save_order(order_data)
                if order:
                    st.success("✅ ההזמנה נשמרה בהצלחה לאחר תיקון הקונפליקטים!")
                    st.balloons()
                    clear_cart()
                    return True
            except Exception as fix_error:
                st.error(f"❌ לא ניתן לתקן את הקונפליקטים: {str(fix_error)}")
        return False

def show_cart_sidebar():
    """הצגת עגלת הקניות בסיידבר"""
    st.sidebar.header("🛒 עגלת קניות")
    
    if not st.session_state.cart:
        st.sidebar.info("העגלה ריקה")
        return
    
    total_price = 0
    
    for product, details in st.session_state.cart.items():
        with st.sidebar.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{product}**")
                unit = get_product_unit(product.split(' - ')[0] if ' - ' in product else product)
                st.write(f"כמות: {details['quantity']} {unit}")
                if details.get('price', 0) > 0:
                    st.write(f"מחיר: ₪{details['price']:.2f}")
            
            with col2:
                if st.button("🗑️", key=f"remove_{product}", help="הסר מהעגלה"):
                    remove_from_cart(product)
                    st.rerun()
            
            total_price += details.get('price', 0) * details['quantity']
        
        st.sidebar.divider()
    
    
    # כפתור ניקוי העגלה
    if st.sidebar.button("🧹 נקה עגלה", use_container_width=True):
        clear_cart()
        st.rerun()
    
    # כפתור המשך להזמנה
    if st.sidebar.button("📝 המשך להזמנה", use_container_width=True, type="primary"):
        st.session_state.show_order_form = True
        st.session_state.selected_page = "עגלת קניות"  # שינוי לדף העגלה
        st.rerun()

def show_order_form():
    """הצגת טופס הזמנה עם פרטי לקוח מפורטים"""
    st.header("📝 פרטי הזמנה")
    
    with st.form("order_form"):
        # פרטי לקוח - שורה ראשונה
        st.subheader("👤 פרטי לקוח")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("שם פרטי", value=st.session_state.customer_first_name, key="order_customer_first_name", placeholder="הכנס שם פרטי")
            st.text_input("שם משפחה", value=st.session_state.customer_last_name, key="order_customer_last_name", placeholder="הכנס שם משפחה")
            st.text_input("מספר נייד", value=st.session_state.customer_phone, key="order_customer_phone", placeholder="הכנס מספר טלפון")
        
        with col2:
            st.text_input("עיר", value=st.session_state.customer_city, key="order_customer_city", placeholder="הכנס שם העיר")
            st.text_input("שם רחוב", value=st.session_state.customer_street_name, key="order_customer_street_name", placeholder="הכנס שם הרחוב")
            st.text_input("מספר רחוב", value=st.session_state.customer_street_number, key="order_customer_street_number", placeholder="הכנס מספר רחוב")
        
        # כתובת מפורטת - שורה שנייה
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("קומה", value=st.session_state.customer_floor, key="order_customer_floor", placeholder="הכנס מספר קומה (אופציונלי)")
            st.text_input("מספר דירה", value=st.session_state.customer_apartment, key="order_customer_apartment", placeholder="הכנס מספר דירה")
        
        with col2:
            st.text_area("הערות לשליח", value=st.session_state.customer_delivery_notes, key="order_customer_delivery_notes", 
                        placeholder="הוראות מיוחדות לשליח (אופציונלי)", height=80)
            st.text_area("הערות לקצב", value=st.session_state.customer_kitchen_notes, key="order_customer_kitchen_notes", 
                        placeholder="הוראות מיוחדות להכנה (אופציונלי)", height=80)
        
        st.divider()
        
        # הצגת סיכום ההזמנה
        st.subheader("🛒 סיכום ההזמנה")
        
        total_price = 0
        for product, details in st.session_state.cart.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{product}**")
            
            with col2:
                unit = get_product_unit(product.split(' - ')[0] if ' - ' in product else product)
                st.write(f"{details['quantity']} {unit}")
            
            with col3:
                # חישובי מחיר מוקפאים בשלב זה
                st.write("₪--")
        
        st.divider()
        
        # סה"כ
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**סה\"כ**")
        with col2:
            st.write("**₪--**")
        
        # כפתור שמירה וכפתור חזרה
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("📤 שלח הזמנה", use_container_width=True):
                # שמירת כל פרטי הלקוח
                st.session_state.customer_first_name = st.session_state.order_customer_first_name
                st.session_state.customer_last_name = st.session_state.order_customer_last_name
                st.session_state.customer_street_name = st.session_state.order_customer_street_name
                st.session_state.customer_street_number = st.session_state.order_customer_street_number
                st.session_state.customer_floor = st.session_state.order_customer_floor
                st.session_state.customer_apartment = st.session_state.order_customer_apartment
                st.session_state.customer_city = st.session_state.order_customer_city
                st.session_state.customer_phone = st.session_state.order_customer_phone
                st.session_state.customer_delivery_notes = st.session_state.order_customer_delivery_notes
                st.session_state.customer_kitchen_notes = st.session_state.order_customer_kitchen_notes
                
                # ולידציה: מספר טלפון ספרתי בלבד
                if not st.session_state.customer_phone.isdigit():
                    st.error("מספר הטלפון חייב להכיל ספרות בלבד")
                else:
                    # בניית הודעה לוואטסאפ (ללא מחירים)
                    full_name = f"{st.session_state.customer_first_name} {st.session_state.customer_last_name}"
                    address_parts = []
                    if st.session_state.customer_street_name:
                        address_parts.append(st.session_state.customer_street_name)
                    if st.session_state.customer_street_number:
                        address_parts.append(st.session_state.customer_street_number)
                    if st.session_state.customer_city:
                        address_parts.append(st.session_state.customer_city)
                    address_text = ", ".join(address_parts)

                    message_lines = []
                    message_lines.append(f"שלום {full_name}, תודה על ההזמנה!\n")
                    if address_text:
                        message_lines.append(f"כתובת: {address_text}")
                    if st.session_state.customer_delivery_notes:
                        message_lines.append(f"הערות לשליח: {st.session_state.customer_delivery_notes}")
                    if st.session_state.customer_kitchen_notes:
                        message_lines.append(f"הערות לקצב: {st.session_state.customer_kitchen_notes}")
                    message_lines.append("\nפריטי ההזמנה:")
                    for product, details in st.session_state.cart.items():
                        base_name = product.split(' - ')[0] if ' - ' in product else product
                        unit = get_product_unit(base_name)
                        qty = details.get('quantity', 0)
                        message_lines.append(f"• {product}: {qty} {unit}")

                    message_text = "\n".join(message_lines)

                    # נירמול מספר טלפון ל-972
                    phone = st.session_state.customer_phone.replace('-', '').replace(' ', '')
                    if phone.startswith('0'):
                        phone = '972' + phone[1:]

                    # שמירה ואז הצגת כפתור וואטסאפ
                    if save_order_with_customer():
                        import urllib.parse
                        encoded_message = urllib.parse.quote(message_text)
                        whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
                        st.markdown(f"[📧 שלח פרטי הזמנה לוואטסאפ]({whatsapp_url})")
            
    # כפתור חזרה לעגלה (מחוץ ל-form)
    if st.button("🔙 חזרה לעגלה", use_container_width=True):
        st.session_state.show_order_form = False
        st.rerun()
            
def show_tracking_page():
    """הצגת דף מעקב הזמנות"""
    st.header("📊 מעקב הזמנות")
    
    # בדיקת חיבור ל-API
    api_status = "מחובר לשרת החדש" if API_AVAILABLE else "מצב offline"
    st.info(f"סטטוס חיבור: {api_status}")
    
    # נסה לטעון הזמנות מה-API אם זמין
    orders = []
    if API_AVAILABLE:
        try:
            api_client = create_api_client()
            api_orders = api_client.get_orders()
            
            # המרת נתוני ה-API לפורמט המקומי
            for api_order in api_orders:
                try:
                    # המרת items מ-JSON אם נדרש
                    items = api_order.get('items', [])
                    if isinstance(items, str):
                        items = json.loads(items)
                    
                    # המרת כתובת מ-JSON אם נדרש
                    customer_address = api_order.get('customer_address', '')
                    if isinstance(customer_address, str) and customer_address.startswith('{'):
                        try:
                            address_data = json.loads(customer_address)
                            customer_address = address_data.get('address', customer_address)
                        except:
                            pass
                    
                    # המרת תאריך
                    order_date = api_order.get('order_date', '')
                    if isinstance(order_date, str):
                        try:
                            # נסה לפרסר תאריכים שונים
                            for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                                try:
                                    parsed_date = datetime.strptime(order_date, fmt)
                                    order_date = parsed_date.strftime('%Y-%m-%d %H:%M')
                                    break
                                except:
                                    continue
                        except:
                            order_date = 'תאריך לא ידוע'
                    
                    order = {
                        'id': api_order.get('id', 0),
                        'customer_name': api_order.get('customer_name', ''),
                        'customer_phone': api_order.get('customer_phone', ''),
                        'customer_address': customer_address,
                        'items': items,
                        'total_amount': api_order.get('total_amount', 0),
                        'order_date': order_date,
                        'status': api_order.get('status', 'ממתין'),
                        'phone': api_order.get('customer_phone', ''),
                        'address': customer_address,
                        'created_at': order_date
                    }
                    orders.append(order)
                    
                except Exception as e:
                    st.warning(f"שגיאה בהמרת הזמנה: {e}")
                    continue
                    
        except Exception as e:
            st.warning(f"לא ניתן לטעון הזמנות מה-API: {e}")
            st.info("המערכת תטען הזמנות מהמסד הנתונים המקומי")
    
    # אם אין הזמנות מה-API, טען מהמסד הנתונים המקומי
    if not orders:
        try:
            orders = load_orders()
        except Exception as e:
            st.error(f"שגיאה בטעינת הזמנות: {e}")
            orders = []
    
    if not orders:
        st.info("אין הזמנות להצגה")
        return
    
    # סינון הזמנות
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 חיפוש הזמנות", placeholder="חיפוש לפי שם לקוח או טלפון")
    
    with col2:
        status_filter = st.selectbox(
            "סטטוס",
            ["כל הסטטוסים", "ממתין", "בטיפול", "הושלם", "בוטל"]
        )
    
    # סינון התוצאות
    filtered_orders = []
    for order in orders:
        # סינון לפי חיפוש
        if search_term:
            search_lower = search_term.lower()
            customer_name = order.get('customer_name', '')
            customer_phone = order.get('phone', order.get('customer_phone', ''))
            if not (search_lower in customer_name.lower() or 
                   search_lower in customer_phone.lower()):
                continue
        
        # סינון לפי סטטוס
        if status_filter != "כל הסטטוסים" and order.get('status') != status_filter:
            continue
        
        filtered_orders.append(order)
    
    if not filtered_orders:
        st.info("לא נמצאו הזמנות לפי הקריטריונים שנבחרו")
        return
    
    # הצגת ההזמנות
    for order in filtered_orders:
        order_id = order.get('id', 0)
        customer_name = order.get('customer_name', '')
        order_date = order.get('order_date', order.get('created_at', ''))
        with st.expander(f"הזמנה #{order_id} - {customer_name} ({order_date})"):
            col1, col2 = st.columns([2, 1])
    
    with col1:
                st.write(f"**לקוח:** {order.get('customer_name', '')}")
                st.write(f"**טלפון:** {order.get('phone', order.get('customer_phone', ''))}")
                if order.get('address') or order.get('customer_address'):
                    address = order.get('address') or order.get('customer_address', '')
                    st.write(f"**כתובת:** {address}")
                
                st.write("**פריטים:**")
                items = order.get('items', [])
                if isinstance(items, dict):
                    # אם items הוא מילון (מהמסד הנתונים המקומי)
                    for product_name, details in items.items():
                        # בדיקה אם details הוא מילון או מספר
                        if isinstance(details, dict):
                            quantity = details.get('quantity', 1)
                            unit = get_product_unit(product_name.split(' - ')[0] if ' - ' in product_name else product_name)
                            price = details.get('price', 0)
                        else:
                            # אם details הוא מספר, זה הכמות
                            quantity = details
                            unit = get_product_unit(product_name.split(' - ')[0] if ' - ' in product_name else product_name)
                            price = 0
                        
                        if price > 0:
                            st.write(f"• {product_name}: {quantity} {unit} - ₪{price:.2f}")
                        else:
                            st.write(f"• {product_name}: {quantity} {unit}")
                elif isinstance(items, list):
                    # אם items הוא רשימה (מה-API)
                    for item in items:
                        if isinstance(item, dict):
                            product_name = item.get('product_name', str(item))
                            quantity = item.get('quantity', 1)
                            unit = get_product_unit(product_name.split(' - ')[0] if ' - ' in product_name else product_name)
                            price = item.get('price', 0)
                            
                            if price > 0:
                                st.write(f"• {product_name}: {quantity} {unit} - ₪{price:.2f}")
                            else:
                                st.write(f"• {product_name}: {quantity} {unit}")
                        else:
                            st.write(f"• {item}")
                else:
                    st.write(f"• {items}")
    
    with col2:
                st.metric("סה\"כ", f"₪{order.get('total_amount', 0):.2f}")
                st.write(f"**סטטוס:** {order.get('status', 'ממתין')}")
                st.write(f"**תאריך:** {order_date}")

def show_order_page():
    """הצגת דף הזמנת מוצרים"""
    st.markdown('<div class="main-header"><h1>🛒 Zoares - הזמנת מוצרים</h1></div>', unsafe_allow_html=True)
    
    # בדיקת חיבור ל-API
    if API_AVAILABLE:
        try:
            api_client = create_api_client()
            if api_client.health_check():
                st.success("✅ מחובר לשרת החדש")
            else:
                st.warning("⚠️ בעיה בחיבור לשרת החדש")
        except:
            st.warning("⚠️ לא ניתן להתחבר לשרת החדש")
    else:
        st.info("ℹ️ המערכת פועלת במצב offline - אין חיבור לשרת החדש")
    
    # חיפוש מוצרים
    st.subheader("🔍 חיפוש מוצרים")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # בדיקה אם צריך לנקות את החיפוש
        if st.session_state.clear_search_flag:
            st.session_state.search_query = ""
            st.session_state.clear_search_flag = False
            st.rerun()
        
        search_input = st.text_input(
            "חיפוש מוצר",
            value=st.session_state.search_query,
            key="main_search_input",
            placeholder="לדוגמה: שניצל עוף, המבורגר הבית, טחון עגל"
        )
        
        if search_input != st.session_state.search_query:
            st.session_state.search_query = search_input
    
    with col2:
        if st.button("🔍 חפש", use_container_width=True):
            pass  # החיפוש מתבצע אוטומטית
    
    # הצגת תוצאות החיפוש
    if st.session_state.search_query:
        st.subheader("🔍 תוצאות חיפוש")
        
        # איסוף כל המוצרים
        all_products = []
        for category, products in PRODUCT_CATEGORIES.items():
            all_products.extend(products)
        
        # חיפוש חכם
        search_results = smart_search(st.session_state.search_query, all_products)
        
        if search_results:
            for product, distance, similarity in search_results:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        # הדגשת תוצאות החיפוש
                        highlighted_name = product
                        if st.session_state.search_query.lower() in product.lower():
                            highlighted_name = product.replace(
                                st.session_state.search_query, 
                                f"<span class='search-highlight'>{st.session_state.search_query}</span>"
                            )
                        st.markdown(f"**{highlighted_name}**", unsafe_allow_html=True)
                        
                        if distance > 0:
                            st.caption(f"({similarity})")
                    
                    with col2:
                        unit = get_product_unit(product)
                        st.write(f"יחידה: {unit}")
                    
                    with col3:
                        # המחיר מוסתר מהמשתמש בשלב זה
                        st.write("מחיר: ₪--")
                    
                    with col4:
                        if st.button("➕ הוסף לעגלה", key=f"add_main_{product}"):
                            if unit == "ק\"ג":
                                # דרישות מינימום מיוחדות
                                if product == "עוף שלם":
                                    min_value = 1.6
                                    default_value = 1.6
                                else:
                                    min_value = 0.1
                                    default_value = 0.5
                                quantity = st.number_input(
                                    "כמות (ק\"ג)",
                                    min_value=min_value,
                                    value=default_value,
                                    step=0.1,
                                    key=f"qty_main_{product}"
                                )
                            else:
                                # דרישות מינימום מיוחדות
                                if product in ["המבורגר 160 גרם", "המבורגר 220 גרם"]:
                                    min_value = 5
                                    default_value = 5
                                else:
                                    min_value = 1
                                    default_value = 1
                                quantity = st.number_input(
                                    "כמות (יחידות)",
                                    min_value=min_value,
                                    value=default_value,
                                    step=1,
                                    key=f"qty_main_{product}"
                                )
                            add_to_cart(product, quantity)
                            st.success(f"נוסף לעגלה: {product}")
                            st.rerun()
                    st.divider()
        else:
            st.info("לא נמצאו מוצרים מתאימים")
            # הצגת הצעות דומות
            st.subheader("💡 הצעות דומות")
            suggestions = []
            for category, products in PRODUCT_CATEGORIES.items():
                for product in products:
                    if any(word in product.lower() for word in st.session_state.search_query.lower().split()):
                        suggestions.append(product)
            if suggestions:
                for suggestion in suggestions[:5]:
                    st.write(f"• {suggestion}")
            else:
                st.write("• נסה חיפוש כללי יותר")
                st.write("• בדוק את האיות")
        # כפתור ניקוי חיפוש
        if st.button("🧹 נקה חיפוש", use_container_width=True):
            st.session_state.clear_search_flag = True
            st.rerun()
            
    # הצגת קטגוריות המוצרים
    st.subheader("📂 קטגוריות מוצרים")
    
    # בחירת קטגוריה
    category_options = ["כל הקטגוריות"] + list(PRODUCT_CATEGORIES.keys())
    selected_category = st.selectbox(
        "בחר קטגוריה",
        category_options,
        index=category_options.index(st.session_state.selected_category)
    )
    
    if selected_category != st.session_state.selected_category:
        st.session_state.selected_category = selected_category
        st.rerun()
    
    # הצגת מוצרים לפי הקטגוריה שנבחרה
    if selected_category == "כל הקטגוריות":
        for category, products in PRODUCT_CATEGORIES.items():
            st.write(f"**{category}:**")
            for product in products:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.write(product)
                    
                    with col2:
                        unit = get_product_unit(product)
                        st.write(f"יחידה: {unit}")
                    
                    with col3:
                        # המחיר מוסתר מהמשתמש בשלב זה
                        st.write("מחיר: ₪--")
                    
                    with col4:
                        # תצוגת אפשרויות חיתוך אם קיימות
                        cutting_choice = None
                        if product in CUTTABLE_PRODUCTS:
                            cutting_options = CUTTABLE_PRODUCTS[product]
                            cutting_choice = st.selectbox(
                                "אופן חיתוך:",
                                cutting_options["options"],
                                index=cutting_options["options"].index(cutting_options["default"]),
                                key=f"cutting_{product}"
                            )
                        
                        # בחירת כמות
                        if unit == "ק\"ג":
                            # דרישות מינימום מיוחדות
                            if product == "עוף שלם":
                                min_value = 1.6
                                default_value = 1.6
                            else:
                                min_value = 0.1
                                default_value = 0.5
                            
                            quantity = st.number_input(
                                "כמות (ק\"ג)",
                                min_value=min_value,
                                value=default_value,
                                step=0.1,
                                key=f"qty_cat_{product}"
                            )
                        else:
                            # דרישות מינימום מיוחדות
                            if product in ["המבורגר 160 גרם", "המבורגר 220 גרם"]:
                                min_value = 5
                                default_value = 5
                            else:
                                min_value = 1
                                default_value = 1
                            quantity = st.number_input(
                                "כמות (יחידות)",
                                min_value=min_value,
                                value=default_value,
                                step=1,
                                key=f"qty_cat_{product}"
                            )
                        
                        if st.button("➕ הוסף לעגלה", key=f"add_cat_{product}"):
                            # קביעת שם המוצר הסופי
                            if cutting_choice and product in CUTTABLE_PRODUCTS and cutting_choice != CUTTABLE_PRODUCTS[product]["default"]:
                                product_name = f"{product} - {cutting_choice}"
                            else:
                                product_name = product
                            add_to_cart(product_name, quantity)
                            st.success(f"נוסף לעגלה: {product_name}")
                            st.rerun()
                    st.divider()
    else:
        products = PRODUCT_CATEGORIES[selected_category]
        for product in products:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{product}**")
                
                with col2:
                    unit = get_product_unit(product)
                    st.write(f"יחידה: {unit}")
                
                with col3:
                    # המחיר מוסתר מהמשתמש בשלב זה
                    st.write("מחיר: ₪--")
                
                with col4:
                    # תצוגת אפשרויות חיתוך אם קיימות
                    cutting_choice = None
                    if product in CUTTABLE_PRODUCTS:
                        cutting_options = CUTTABLE_PRODUCTS[product]
                        cutting_choice = st.selectbox(
                            "אופן חיתוך:",
                            cutting_options["options"],
                            index=cutting_options["options"].index(cutting_options["default"]),
                            key=f"cutting_single_{product}"
                        )
                    
                    # בחירת כמות
                    if unit == "ק\"ג":
                        # דרישות מינימום מיוחדות
                        if product == "עוף שלם":
                            min_value = 1.6
                            default_value = 1.6
                        else:
                            min_value = 0.1
                            default_value = 0.5
                        quantity = st.number_input(
                            "כמות (ק\"ג)",
                            min_value=min_value,
                            value=default_value,
                            step=0.1,
                            key=f"qty_single_{product}"
                        )
                    else:
                        # דרישות מינימום מיוחדות
                        if product in ["המבורגר 160 גרם", "המבורגר 220 גרם"]:
                            min_value = 5
                            default_value = 5
                        else:
                            min_value = 1
                            default_value = 1
                        quantity = st.number_input(
                            "כמות (יחידות)",
                            min_value=min_value,
                            value=default_value,
                            step=1,
                            key=f"qty_single_{product}"
                        )
                    
                    if st.button("➕ הוסף לעגלה", key=f"add_single_{product}"):
                        # קביעת שם המוצר הסופי
                        if cutting_choice and product in CUTTABLE_PRODUCTS and cutting_choice != CUTTABLE_PRODUCTS[product]["default"]:
                            product_name = f"{product} - {cutting_choice}"
                        else:
                            product_name = product
                        add_to_cart(product_name, quantity)
                        st.success(f"נוסף לעגלה: {product_name}")
                        st.rerun()
                
                st.divider()

def main():
    """פונקציה ראשית"""
    # בדיקת חיבור ל-API
    if API_AVAILABLE:
        try:
            api_client = create_api_client()
            if api_client.health_check():
                st.success("✅ מחובר לשרת החדש")
            else:
                st.warning("⚠️ בעיה בחיבור לשרת החדש")
        except:
            st.warning("⚠️ לא ניתן להתחבר לשרת החדש")
    else:
        st.info("ℹ️ המערכת פועלת במצב offline - אין חיבור לשרת החדש")
    
    # תפריט ניווט
    st.sidebar.title("🧭 ניווט")
    
    page = st.sidebar.selectbox(
        "בחר דף",
        ["הזמנת מוצרים", "מעקב הזמנות", "עגלת קניות"],
        index=["הזמנת מוצרים", "מעקב הזמנות", "עגלת קניות"].index(st.session_state.selected_page)
    )
    
    # עדכון הדף הנבחר אם השתנה
    if page != st.session_state.selected_page:
        st.session_state.selected_page = page
        st.rerun()
    
    # חיפוש בסיידבר
    st.sidebar.subheader("🔍 חיפוש מהיר")
    
    # בדיקה אם צריך לנקות את החיפוש בסיידבר
    if st.session_state.clear_sidebar_search_flag:
        st.session_state.sidebar_search_query = ""
        st.session_state.clear_sidebar_search_flag = False
        st.rerun()
    
    sidebar_search = st.sidebar.text_input(
        "חיפוש מוצר",
        value=st.session_state.sidebar_search_query,
        key="sidebar_search_input",
        placeholder="לדוגמה: שניצל עוף, המבורגר הבית"
    )
    
    if sidebar_search != st.session_state.sidebar_search_query:
        st.session_state.sidebar_search_query = sidebar_search
    
    # הצגת תוצאות חיפוש בסיידבר
    if st.session_state.sidebar_search_query:
        st.sidebar.subheader("🔍 תוצאות חיפוש")
        
        # איסוף כל המוצרים
        all_products = []
        for category, products in PRODUCT_CATEGORIES.items():
            all_products.extend(products)
        
        # חיפוש חכם
        search_results = smart_search(st.session_state.sidebar_search_query, all_products)
        
        if search_results:
            for product, distance, similarity in search_results[:5]:  # הצג רק 5 תוצאות בסיידבר
                with st.sidebar.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{product}**")
                        if distance > 0:
                            st.caption(f"({similarity})")
                    
                    with col2:
                        if st.button("➕", key=f"add_sidebar_{product}", help="הוסף לעגלה"):
                            unit = get_product_unit(product)
                            
                            if unit == "ק\"ג":
                                # דרישות מינימום מיוחדות
                                if product == "עוף שלם":
                                    min_value = 1.6
                                    default_value = 1.6
                                else:
                                    min_value = 0.1
                                    default_value = 0.5
                                quantity = st.number_input(
                                    "כמות (ק\"ג)",
                                    min_value=min_value,
                                    value=default_value,
                                    step=0.1,
                                    key=f"qty_sidebar_{product}"
                                )
                            else:
                                # דרישות מינימום מיוחדות
                                if product in ["המבורגר 160 גרם", "המבורגר 220 גרם"]:
                                    min_value = 5
                                    default_value = 5
                                else:
                                    min_value = 1
                                    default_value = 1
                                
                                quantity = st.number_input(
                                    "כמות (יחידות)",
                                    min_value=min_value,
                                    value=default_value,
                                    step=1,
                                    key=f"qty_sidebar_{product}"
                                )
                            
                            add_to_cart(product, quantity)
                            st.sidebar.success(f"נוסף לעגלה: {product}")
                            st.rerun()
                    
                    st.sidebar.divider()
        else:
            st.sidebar.info("לא נמצאו מוצרים")
        
        # כפתור ניקוי חיפוש בסיידבר
        if st.sidebar.button("🧹 נקה חיפוש", use_container_width=True):
            st.session_state.clear_sidebar_search_flag = True
            st.rerun()
    
    # הצגת עגלת הקניות
    show_cart_sidebar()
    
    # סנכרון אוטומטי עם השרת (אם זמין)
    try:
        api_client = create_api_client()
        auto_refresh_on_updates(api_client, refresh_interval=30)  # בדיקה כל 30 שניות
    except Exception as e:
        st.sidebar.warning(f"⚠️ בעיה בסנכרון: {str(e)}")
    
    # הצגת הדף הנבחר
    if st.session_state.selected_page == "הזמנת מוצרים":
        show_order_page()
    elif st.session_state.selected_page == "מעקב הזמנות":
        show_tracking_page()
    elif st.session_state.selected_page == "עגלת קניות":
        if st.session_state.cart:
            show_order_form()
    else:
            st.info("העגלה ריקה. הוסף מוצרים כדי להמשיך להזמנה.")
    
    # הצגת טופס הזמנה אם נבחר (מנוהל דרך selected_page)

if __name__ == "__main__":
    main() 
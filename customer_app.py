import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import webbrowser
from database import (
    init_database, load_orders, save_order, load_closed_orders,
    load_customers, save_customers, find_or_create_customer, 
    update_customer_stats, cleanup_old_customers, import_existing_data
)

# אתחול מסד הנתונים וייבוא נתונים קיימים
if not os.path.exists('zoares_central.db'):
    init_database()
    import_existing_data()

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
    ],
}
# הגדר גם את WEIGHT_PRODUCTS, UNIT_PRODUCTS וכו' לפי הצורך
# הסרתי את כל הייבוא והקוד של supabase
# החזרתי את הפונקציות המקוריות לקריאה וכתיבה ל-JSON:

# --- כאן מתחיל הקוד לאחר הסרת supabase ---

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
    "רגל פרה": True,
    "גידי רגל": True,
    "צלעות טלה פרימיום בייבי": True,
    "שומן גב כבש טרי  בדצ בית יוסף": True
}

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
    "גרון הודו": True,
    "ביצי הודו": True,
    "המבורגר הבית": True,
    "המבורגר": True,
    "המבורגר הבית": True,
    "נקניקיות": True,
    "נקניק חריף": True,
    "סלמון": True,
    "טונה": True,
    "מושט": True,
    "כתף כבש": True,
    "המבורגר 160 גרם": True,
    "המבורגר 220 גרם": True
}

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

# מחירים לפי מוצר
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
    # הוספת מחירים למוצרים עם הוראות חיתוך
    "עוף שלם - שלם": 50.0,
    "עוף שלם - פרוס לשניצל": 50.0,
    "עוף שלם - פרוס ל-8 חלקים": 50.0,
    "עוף שלם - עוף פרוס לשניצל ללא עור": 50.0,
    "עוף שלם - עוף פרוס ל-8 חלקים ללא עור": 50.0,
    "חזה עוף - שלם": 40.0,
    "חזה עוף - פרוס": 40.0,
    "חזה עוף - קוביות": 40.0,
    "חזה עוף - רצועות למוקפץ": 40.0,
    "כרעיים עוף - שלם": 12.0,
    "כרעיים עוף - חצוי": 12.0,
    "כרעיים עוף - שלם בלי עור": 12.0,
    "כרעיים עוף - חצוי בלי עור": 12.0,
    "שווארמה עוף (פרגיות) - חתוך לשיפודים": 15.0,
    "שווארמה עוף (פרגיות) - רצועות": 15.0,
    "שווארמה עוף (פרגיות) - פרוס דק": 15.0,
    "שווארמה עוף (פרגיות) - סטיק פרגית": 15.0,
    "שווארמה הודו נקבה - חתוך לשיפודים": 25.0,
    "שווארמה הודו נקבה - רצועות": 25.0,
    "שווארמה הודו נקבה - פרוס": 25.0,
    "שווארמה הודו נקבה - שלם": 25.0,
    "שוקיים עוף - שוקיים עם עור": 15.0,
    "שוקיים עוף - שוקיים בלי עור": 15.0,
    "שוקיים עוף - שוקיים עם עור": 15.0,
    "שוקיים עוף - שוקיים בלי עור": 15.0,
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
    "עוף טחון": 30.0,
    "שניצל עוף": 35.0,
    "כבד עוף": 20.0,
    "נקניקיות עוף": 10.0,
    "נקניקיות חריפות (מרגז)": 12.0,
    "צ׳יפס מארז 2.5 קג תפוגן": 25.0,
    "צ׳נגו מוסדי 1.25 קג מארז": 15.0,
    "במיה כפתורים": 8.0
}

def calculate_order_total(order):
    """מחשב את הסכום הכולל של ההזמנה"""
    order_total = 0.0
    for product, quantity in order['items'].items():
        # בדיקה שהפריט הוא מוצר ולא הוראות חיתוך
        if not product.endswith('_cutting'):
            # בדיקה אם המוצר נמצא במחירים
            if product in PRODUCT_PRICES:
                order_total += PRODUCT_PRICES[product] * quantity
            else:
                # אם המוצר לא נמצא, ננסה למצוא את המוצר הבסיסי (ללא הוראות חיתוך)
                base_product = product.split(' - ')[0] if ' - ' in product else product
                if base_product in PRODUCT_PRICES:
                    order_total += PRODUCT_PRICES[base_product] * quantity
    return order_total

def save_order_with_customer(order):
    """שומר הזמנה עם קישור ללקוח במסד הנתונים"""
    # חישוב הסכום הכולל
    order_total = calculate_order_total(order)
    order['total_amount'] = order_total
    
    # יצירת או עדכון לקוח
    customer_id = find_or_create_customer(order['phone'], order['customer_name'])
    order['customer_id'] = customer_id
    
    # שמירת ההזמנה
    order_id = save_order(order)
    
    # עדכון סטטיסטיקות לקוח
    update_customer_stats(customer_id, order_total)
    
    return order_id

# אסיר את כל הפונקציות והקריאות להדפסה בהמשך הקובץ (generate_order_html, print_order, וכל כפתור הדפסה)

def calculate_cart_weight(cart):
    """מחשב את המשקל הכולל של העגלה (רק מוצרים שנמכרים במשקל)"""
    total_weight = 0.0
    for product, quantity in cart.items():
        if product in WEIGHT_PRODUCTS:
            total_weight += quantity
    return total_weight

def get_weight_warning(cart):
    """מחזיר אזהרה אם המשקל עולה על המגבלה (לא בשימוש - אין מגבלה)"""
    # הסרת מגבלת משקל - אין אזהרות
    return None

def check_minimum_weight(product, weight):
    """בודק אם המשקל עומד בדרישות המינימום למוצר"""
    # מוצרים עם דרישת משקל מינימום
    MIN_WEIGHT_PRODUCTS = {
        # אין מוצרים עם דרישת משקל מינימום כרגע
    }
    
    if product in MIN_WEIGHT_PRODUCTS:
        min_weight = MIN_WEIGHT_PRODUCTS[product]
        if weight < min_weight:
            return False, f"משקל מינימום למוצר זה הוא {min_weight} קג"
    
    return True, ""

def calculate_delivery_cost(cart, city=""):
    """מחשבת עלות משלוח לפי מיקום"""
    # עלות משלוח לבני ברק: 20 ש"ח
    # עלות משלוח מחוץ לבני ברק: 25 ש"ח
    
    if city and "בני ברק" in city:
        return 20.0
    else:
        return 25.0

def validate_phone_number(phone):
    """מאמת מספר טלפון ישראלי"""
    import re
    
    # הסרת רווחים, מקפים וסוגריים
    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
    
    # בדיקה אם זה מספר טלפון ישראלי תקין
    # פורמטים: 05X-XXXXXXX, 02-XXXXXXX, 03-XXXXXXX, 04-XXXXXXX, 08-XXXXXXX, 09-XXXXXXX
    # או מספרים בלי מקפים: 05XXXXXXXX, 02XXXXXXX, וכו'
    
    # הסרת קידומת +972 אם קיימת
    if phone_clean.startswith('+972'):
        phone_clean = '0' + phone_clean[4:]
    
    # הסרת קידומת 972 אם קיימת
    if phone_clean.startswith('972'):
        phone_clean = '0' + phone_clean[3:]
    
    # בדיקת פורמט מספר טלפון ישראלי
    phone_pattern = r'^(05[0-9]|02|03|04|08|09)[0-9]{7}$'
    
    if re.match(phone_pattern, phone_clean):
        # החזרת המספר בפורמט נקי
        return True, phone_clean
    else:
        return False, phone_clean

def format_phone_number(phone):
    """מעצב מספר טלפון לפורמט קריא"""
    if len(phone) == 10:  # מספר נייד
        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
    elif len(phone) == 9:  # מספר קווי
        return f"{phone[:2]}-{phone[2:5]}-{phone[5:]}"
    else:
        return phone

def validate_hebrew_text(text, field_name):
    """מאמת שטקסט מכיל תווים בעברית בלבד"""
    import re
    
    if not text or not text.strip():
        return False, f"שדה {field_name} הוא שדה חובה"
    
    # הסרת רווחים מתחילת ומסוף הטקסט
    text_clean = text.strip()
    
    # בדיקה שהטקסט לא ריק אחרי ניקוי
    if not text_clean:
        return False, f"שדה {field_name} לא יכול להיות ריק"
    
    # בדיקה שהטקסט מכיל לפחות תו אחד בעברית
    hebrew_pattern = r'[\u0590-\u05FF\u200f\u200e]'
    if not re.search(hebrew_pattern, text_clean):
        return False, f"שדה {field_name} חייב להכיל טקסט בעברית"
    
    # בדיקה שהטקסט מכיל רק אותיות עבריות, רווחים, מקפים ופסיקים
    valid_pattern = r'^[\u0590-\u05FF\u200f\u200e\s\-,\']+$'
    if not re.match(valid_pattern, text_clean):
        return False, f"שדה {field_name} יכול להכיל רק אותיות עבריות, רווחים, מקפים ופסיקים"
    
    return True, text_clean

def get_cutting_instructions(cart):
    """מחזיר הוראות חיתוך לעגלה"""
    instructions = []
    for product, quantity in cart.items():
        if product in CUTTABLE_PRODUCTS:
            cutting_option = cart.get(f"{product}_cutting", CUTTABLE_PRODUCTS[product]["default"])
            instructions.append(f"{product}: {cutting_option}")
    return instructions

# פונקציה לחישוב מרחק Levenshtein (דמיון בין מילים)
def levenshtein_distance(s1, s2):
    """מחשבת את המרחק בין שתי מילים (כמה שינויים נדרשים להפוך אחת לשנייה)"""
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

# פונקציה לחיפוש חכם עם תיקון שגיאות כתיב
def smart_search(query, products_list, max_distance=3, min_similarity=0.6):
    """מבצע חיפוש חכם עם תיקון שגיאות כתיב והצעת חלופות דומות"""
    query = query.strip().lower()
    results = []
    suggestions = []
    
    # חיפוש מדויק
    exact_matches = [prod for prod in products_list if query in prod.lower()]
    results.extend([(prod, 1.0, "מדויק") for prod in exact_matches])
    
    # חיפוש עם שגיאות כתיב
    for product in products_list:
        product_lower = product.lower()
        
        # חישוב דמיון
        distance = levenshtein_distance(query, product_lower)
        max_len = max(len(query), len(product_lower))
        similarity = 1 - (distance / max_len) if max_len > 0 else 0
        
        # אם הדמיון גבוה מספיק
        if similarity >= min_similarity and distance <= max_distance:
            if product not in [r[0] for r in results]:  # לא להוסיף כפילות
                if similarity >= 0.8:
                    match_type = "דומה מאוד"
                elif similarity >= 0.7:
                    match_type = "דומה"
                else:
                    match_type = "דומה חלקית"
                
                results.append((product, similarity, match_type))
    
    # מיון לפי דמיון (גבוה יותר קודם)
    results.sort(key=lambda x: x[1], reverse=True)
    
    # יצירת הצעות לתיקון שגיאות כתיב
    if not exact_matches and results:
        # מציאת המוצר הדומה ביותר
        best_match = results[0]
        if best_match[1] >= 0.7:  # אם הדמיון גבוה מספיק
            suggestions.append(f"האם התכוונת ל: '{best_match[0]}'?")
        
        # הצעות נוספות אם יש
        if len(results) > 1:
            other_suggestions = [r[0] for r in results[1:4] if r[1] >= 0.6]
            if other_suggestions:
                suggestions.append(f"מוצרים דומים: {', '.join(other_suggestions)}")
    
    return results, suggestions

# הפונקציות לניהול לקוחות עכשיו מיובאות מ-database.py

def main():
    # הוספת CSS ליישור לימין ולשיפור הממשק
    st.markdown("""
    <style>
    /* יישור כל הטקסט לימין */
    .stMarkdown, .stText, .stSelectbox, .stNumberInput, .stButton, .stInfo, .stSuccess, .stWarning, .stError {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור כותרות לימין */
    h1, h2, h3, h4, h5, h6 {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור תיבות קלט לימין */
    .stTextInput > div > div > input {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור תיבות בחירה לימין */
    .stSelectbox > div > div > div {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור כפתורים לימין */
    .stButton > button {
        text-align: center !important;
    }
    
    /* יישור העגלה בסיידבר לימין */
    .css-1d391kg {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור כל הטקסטים בסיידבר */
    .css-1d391kg .stMarkdown, .css-1d391kg .stText {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור כותרות בסיידבר */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור תיבות מידע לימין */
    .stAlert {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור טבלאות לימין */
    .stDataFrame {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור רשימות לימין */
    ul, ol {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור פסקאות לימין */
    p {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור תיבות מידע לימין */
    .stInfo, .stSuccess, .stWarning, .stError {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור עמודות לימין */
    .row-widget {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* יישור תיבות מידע בסיידבר */
    .css-1d391kg .stInfo, .css-1d391kg .stSuccess, .css-1d391kg .stWarning, .css-1d391kg .stError {
        text-align: right !important;
        direction: rtl !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🛒 Zoares - הזמנת מוצרים")
    st.markdown("---")
    
    # טעינת הזמנות
    orders = load_orders()
    
    # ניקוי לקוחות ישנים
    cleanup_old_customers()
    
    # סיידבר לניווט
    st.sidebar.title("ניווט")
    
    # הצגת העגלה המלאה בסיידבר
    if 'cart' in st.session_state and st.session_state.cart:
        cart_count = sum(st.session_state.cart.values())
        st.sidebar.info(f"🛒 עגלת קניות: {cart_count} פריטים")
        
        # הצגת משקל כולל
        total_weight = calculate_cart_weight(st.session_state.cart)
        if total_weight > 0:
            st.sidebar.metric("⚖️ משקל כולל", f"{total_weight:.1f} קג")
        
        # הצגת הוראות חיתוך
        cutting_instructions = get_cutting_instructions(st.session_state.cart)
        if cutting_instructions:
            st.sidebar.subheader("🔪 הוראות חיתוך")
            for instruction in cutting_instructions:
                st.sidebar.info(instruction)
        
        # הצגת פריטי העגלה עם אפשרויות עריכה
        st.sidebar.subheader("פריטי העגלה:")
        for product, quantity in st.session_state.cart.items():
            is_weight_product = product in WEIGHT_PRODUCTS
            unit_text = "קילו" if is_weight_product else "יחידות"
            
            # הצגת שם המוצר וכמות
            st.sidebar.write(f"**{product}**")
            st.sidebar.write(f"כמות: {quantity} {unit_text}")
            
            # הצגת אזהרת משקל מינימום אם רלוונטי
            if product == "עוף שלם":
                st.sidebar.warning("⚠️ משקל מינימום ליחידה: 1.6 קג")
            elif product == "עוף בלי עור" and is_weight_product:
                st.sidebar.warning("⚠️ משקל מינימום: 1.6 קג")
            
            # כפתורים לעריכת כמות
            col1, col2, col3 = st.sidebar.columns(3)
            with col1:
                if st.button("➖", key=f"sidebar_dec_{product}"):
                    if is_weight_product:
                        # בדיקת משקל מינימום לפני הפחתה
                        new_weight = st.session_state.cart[product] - 0.5
                        is_valid_weight, error_message = check_minimum_weight(product, new_weight)
                        if not is_valid_weight and new_weight > 0:
                            st.sidebar.error(error_message)
                        else:
                            if st.session_state.cart[product] > 0.5:
                                st.session_state.cart[product] -= 0.5
                            else:
                                del st.session_state.cart[product]
                    else:
                        if st.session_state.cart[product] > 1:
                            st.session_state.cart[product] -= 1
                        else:
                            del st.session_state.cart[product]
                    st.rerun()
            with col2:
                st.sidebar.write(f"**{quantity}**")
            with col3:
                if st.button("➕", key=f"sidebar_inc_{product}"):
                    if is_weight_product:
                        st.session_state.cart[product] += 0.5
                    else:
                        st.session_state.cart[product] += 1
                    st.rerun()
            
            # כפתור מחיקה
            if st.sidebar.button(f"🗑️ מחק {product}", key=f"sidebar_remove_{product}"):
                del st.session_state.cart[product]
                st.rerun()
            
            st.sidebar.markdown("---")
        
        # כפתור לריקון העגלה
        if st.sidebar.button("🗑️ רוקן עגלה", type="secondary", key="clear_cart_sidebar"):
            st.session_state.cart.clear()
            st.rerun()
    
    # הצגת מידע על עלות משלוח בסיידבר
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚚 עלות משלוח")
    st.sidebar.write("• בני ברק: 20 ש\"ח")
    st.sidebar.write("• מחוץ לבני ברק: 25 ש\"ח")
    
    # --- חיפוש מוצר בסיידבר ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 חיפוש מוצר")
    # איפוס שדה החיפוש בסיידבר לפני יצירת הווידג'ט אם התבקש
    if st.session_state.get("sb_clear_requested", False):
        st.session_state["sb_clear_requested"] = False
        st.session_state["sidebar_product_search"] = ""
    sidebar_search_query = st.sidebar.text_input(
        "הקלד שם מוצר:",
        placeholder="לדוגמה: שניצל עוף, המבורגר הבית, טחון עגל",
        key="sidebar_product_search"
    )
    st.sidebar.caption("לתשומת לבך: יש ללחוץ על כפתור \"חפש\" – מקש Enter לא מפעיל את החיפוש.")
    
    # חיפוש ידני בלבד בסיידבר (הוסר חיפוש אוטומטי)
    
    sb_col1, sb_col2 = st.sidebar.columns([1, 1])
    with sb_col1:
        sb_do_search = st.sidebar.button("🔎 חפש", key="btn_sb_search_product")
    with sb_col2:
        sb_clear = st.sidebar.button("❌ נקה", key="btn_sb_clear_product_search")

    if sb_clear:
        st.session_state["sb_clear_requested"] = True
        st.rerun()

    sb_results = []
    sb_suggestions = []
    # חיפוש ידני בלבד בסיידבר
    sb_should_search = (sb_do_search and sidebar_search_query)
    if sb_should_search:
        # יצירת רשימה של כל המוצרים
        all_products = []
        for category_name, products_in_cat in PRODUCT_CATEGORIES.items():
            for prod in products_in_cat:
                all_products.append((prod, category_name))
        
        # חיפוש חכם עם תיקון שגיאות כתיב
        product_names = [prod for prod, _ in all_products]
        smart_results, sb_suggestions = smart_search(sidebar_search_query, product_names)
        
        # מיפוי התוצאות חזרה לקטגוריות
        for product, similarity, match_type in smart_results:
            category_name = next(cat for prod, cat in all_products if prod == product)
            sb_results.append((product, category_name, similarity, match_type))

    if sb_do_search:
        # הצגת הצעות בסיידבר
        if sb_suggestions:
            for suggestion in sb_suggestions[:2]:  # רק 2 הצעות בסיידבר
                st.sidebar.info(suggestion)
            st.sidebar.markdown("---")
        
        if sb_results:
            st.sidebar.markdown(f"נמצאו {len(sb_results)} תוצאות")
            for (product, category_name, similarity, match_type) in sb_results[:10]:
                # הצגת סוג ההתאמה
                if match_type == "מדויק":
                    st.sidebar.success(f"✅ {product}")
                elif match_type == "דומה מאוד":
                    st.sidebar.info(f"🔍 {product}")
                elif match_type == "דומה":
                    st.sidebar.warning(f"🔍 {product}")
                else:
                    st.sidebar.write(f"🔍 {product}")
                
                # הצגת אחוז הדמיון
                similarity_percent = int(similarity * 100)
                st.sidebar.caption(f"דמיון: {similarity_percent}%")
                
                is_weight_product = product in WEIGHT_PRODUCTS
                is_unit_product = product in UNIT_PRODUCTS

                if is_weight_product:
                    st.sidebar.caption("⚖️ בקילו")
                    min_weight = 1.6 if product in ["עוף שלם", "עוף בלי עור"] else 0.5
                    selected_weight = st.sidebar.number_input(
                        "בחר משקל (קילו):",
                        min_value=float(min_weight),
                        value=float(min_weight),
                        step=0.1,
                        key=f"sb_weight_{product}_{category_name}"
                    )
                    if product in CUTTABLE_PRODUCTS:
                        cutting_options = CUTTABLE_PRODUCTS[product]["options"]
                        default_index = cutting_options.index(CUTTABLE_PRODUCTS[product]["default"])
                        cutting_choice = st.sidebar.selectbox(
                            "חיתוך:",
                            cutting_options,
                            index=default_index,
                            key=f"sb_cutting_{product}_{category_name}"
                        )
                        st.session_state[f"cutting_{product}"] = cutting_choice
                    if st.sidebar.button(f"הוסף - {product}", key=f"sb_add_{product}_{category_name}"):
                        if selected_weight > 0:
                            is_valid_weight, error_message = check_minimum_weight(product, selected_weight)
                            if not is_valid_weight:
                                st.sidebar.error(error_message)
                            else:
                                st.session_state.cart[product] = st.session_state.cart.get(product, 0) + selected_weight
                                st.rerun()

                elif is_unit_product:
                    st.sidebar.caption("📦 ביחידות")
                    if product == "עוף שלם":
                        st.sidebar.info("⚠️ משקל מינימום ליחידה: 1.6 קג")
                        min_units = 1
                    elif product in ["המבורגר הבית", "המבורגר 160 גרם", "המבורגר 220 גרם"]:
                        st.sidebar.info("⚠️ מינימום הזמנה: 5 יחידות")
                        min_units = 5
                    else:
                        min_units = 1
                    selected_units = st.sidebar.number_input(
                        "בחר כמות:",
                        min_value=int(min_units),
                        value=int(min_units),
                        step=1,
                        key=f"sb_units_{product}_{category_name}"
                    )
                    if product in CUTTABLE_PRODUCTS:
                        cutting_options = CUTTABLE_PRODUCTS[product]["options"]
                        default_index = cutting_options.index(CUTTABLE_PRODUCTS[product]["default"])
                        cutting_choice = st.sidebar.selectbox(
                            "חיתוך:",
                            cutting_options,
                            index=default_index,
                            key=f"sb_cutting_units_{product}_{category_name}"
                        )
                        st.session_state[f"cutting_{product}"] = cutting_choice
                    if st.sidebar.button(f"הוסף - {product}", key=f"sb_add_units_{product}_{category_name}"):
                        product_name = product
                        if product in CUTTABLE_PRODUCTS:
                            cutting_choice = st.session_state.get(f"cutting_{product}", CUTTABLE_PRODUCTS[product]["default"])
                            product_name = f"{product} - {cutting_choice}"
                        st.session_state.cart[product_name] = st.session_state.cart.get(product_name, 0) + selected_units
                        st.rerun()

                else:
                    quantity = st.sidebar.number_input(
                        "כמות:",
                        min_value=1,
                        value=1,
                        step=1,
                        key=f"sb_qty_{product}_{category_name}"
                    )
                    if st.sidebar.button(f"הוסף - {product}", key=f"sb_add_qty_{product}_{category_name}"):
                        st.session_state.cart[product] = st.session_state.cart.get(product, 0) + quantity
                        st.rerun()

            if len(sb_results) > 10:
                st.sidebar.info(f"הצגת 10 מתוך {len(sb_results)} תוצאות. צמצם את החיפוש לקבלת עוד.")
        else:
            st.sidebar.info("לא נמצאו מוצרים תואמים.")
    # --- סוף חיפוש מוצר בסיידבר ---

    page = st.sidebar.selectbox(
        "בחר עמוד:",
        ["דף הבית", "הזמנת מוצרים", "מעקב הזמנות"]
    )
    
    if page == "דף הבית":
        show_home_page()
    elif page == "הזמנת מוצרים":
        show_order_page(orders)
    elif page == "מעקב הזמנות":
        show_tracking_page(orders)

def show_home_page():
    """מציג את דף הבית"""
    st.header("🏠 ברוכים הבאים ל-Zoares")
    
    st.markdown("""
    ### 🥩 המוצרים שלנו
    
    אנו מתמחים במכירת מוצרי בשר, עוף, דגים, הודו ומוצרים נוספים באיכות גבוהה.
    
    **🍗 עופות טריים ארוזים בהתאמה אישית:**
    - עוף טרי ואיכותי ארוז לפי בקשת הלקוח
    - מכירה ביחידות ו/או במשקל
    - חיתוך מותאם אישית לכל הזמנה
    - הודו טרי ואיכותי
    
    **הקטגוריות שלנו:**
    - 🍗 עופות - עוף טרי ואיכותי, הודו
    - 🥩 בשר - בשר בקר, כבש, בשר איכותי על האש
    - 🐟 דגים - סלמון, טונה ועוד
    - 🥚 אחר - מוצרים נוספים
    - 🍔 המבורגר הבית - המבורגר ייחודי בטעמו ובניחוחו
    
    ### 🚚 משלוחים
   
    - משלוח עד הבית
    - עלות משלוח: 20 ש"ח לבני ברק, 25 ש"ח מחוץ לבני ברק
    - אימות מספר טלפון אוטומטי
    
    ### 🔪 שירותי חיתוך
    - עוף שלם: שלם, פרוס, פרוס לחלקים
    - בשר בקר: שלם או פרוס
    - חיתוך מותאם אישית לכל הזמנה
    
    ### 📞 יצירת קשר
    - טלפון: 03-5700842
    - וואטסאפ: 052-3656714
    - שעות פעילות (למעט חגים): א'-ה' 6:00-14:00, ו' 6:00-12:00
    """)
    
    # הצגת מוצרים מובילים
    st.subheader("🔥 מוצרים מובילים")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🍗 עופות טריים ארוזים")
        st.write("עוף טרי ואיכותי ארוז בהתאמה אישית ביחידות ו/או במשקל")
    
    with col2:
        st.info("🥩 שניצל ופילה עוף")
        st.write("שניצל ופילה עוף טרי ואיכותי")
    
    with col3:
        st.info("🔥 בשר על האש ובישול")
        st.write("בשר איכותי מוכן לעל האש ובישול")

def show_order_page(orders):
    """מציג את דף ההזמנה"""
    st.header("🛒 הזמנת מוצרים")
    
    # אתחול עגלת הקניות ב-session state
    if 'cart' not in st.session_state:
        st.session_state.cart = {}
    
    # --- חיפוש מוצר (בגוף העמוד) ---
    st.subheader("🔎 חיפוש מוצר")
    
    # סינון לפי קטגוריה
    search_category_filter = st.selectbox(
        "קטגוריה לחיפוש:",
        ["כל הקטגוריות"] + list(PRODUCT_CATEGORIES.keys()),
        key="search_category_filter"
    )
    
    search_query = st.text_input(
        "הקלד שם מוצר:",
        placeholder="לדוגמה: שניצל עוף, המבורגר הבית, טחון עגל",
        key="product_search_main"
    )
    
    # חיפוש ידני בלבד (הוסר חיפוש אוטומטי)
    
    scol1, scol2 = st.columns([1, 1])
    with scol1:
        do_search = st.button("🔎 חפש מוצר", key="btn_search_product_main")
    with scol2:
        clear_search = st.button("❌ נקה חיפוש", key="btn_clear_product_search_main")

    if clear_search:
        st.session_state["product_search_main"] = ""
        st.rerun()

    results = []
    suggestions = []
    # חיפוש ידני בלבד
    should_search = (do_search and search_query)
    if should_search:
        # יצירת רשימה של מוצרים לפי הסינון
        all_products = []
        if search_category_filter == "כל הקטגוריות":
            for category_name, products_in_cat in PRODUCT_CATEGORIES.items():
                for prod in products_in_cat:
                    all_products.append((prod, category_name))
        else:
            # חיפוש רק בקטגוריה שנבחרה
            products_in_cat = PRODUCT_CATEGORIES[search_category_filter]
            for prod in products_in_cat:
                all_products.append((prod, search_category_filter))
        
        # חיפוש חכם עם תיקון שגיאות כתיב
        product_names = [prod for prod, _ in all_products]
        smart_results, suggestions = smart_search(search_query, product_names)
        
        # מיפוי התוצאות חזרה לקטגוריות
        for product, similarity, match_type in smart_results:
            category_name = next(cat for prod, cat in all_products if prod == product)
            results.append((product, category_name, similarity, match_type))

    if do_search:
        st.markdown("---")
        
        # הצגת הצעות לתיקון שגיאות כתיב
        if suggestions:
            st.subheader("💡 הצעות חיפוש")
            for suggestion in suggestions:
                st.info(suggestion)
            st.markdown("---")
        
        if results:
            st.subheader(f"תוצאות חיפוש ({len(results)})")
            cols = st.columns(3)
            for i, (product, category_name, similarity, match_type) in enumerate(results):
                with cols[i % 3]:
                    # הצגת סוג ההתאמה
                    if match_type == "מדויק":
                        st.success(f"✅ {product}")
                    elif match_type == "דומה מאוד":
                        st.info(f"🔍 {product}")
                    elif match_type == "דומה":
                        st.warning(f"🔍 {product}")
                    else:
                        st.write(f"🔍 {product}")
                    
                    # הצגת אחוז הדמיון
                    similarity_percent = int(similarity * 100)
                    st.caption(f"דמיון: {similarity_percent}% ({match_type})")
                    
                    is_weight_product = product in WEIGHT_PRODUCTS
                    is_unit_product = product in UNIT_PRODUCTS

                    if is_weight_product:
                        st.write("⚖️ נמכר בקילו")
                        min_weight = 1.6 if product in ["עוף שלם", "עוף בלי עור"] else 0.5
                        selected_weight = st.number_input(
                            "בחר משקל (קילו):",
                            min_value=float(min_weight),
                            value=float(min_weight),
                            step=0.1,
                            key=f"search_weight_{product}_{category_name}"
                        )
                        if product in CUTTABLE_PRODUCTS:
                            st.write("🔪 אופן חיתוך:")
                            cutting_options = CUTTABLE_PRODUCTS[product]["options"]
                            default_index = cutting_options.index(CUTTABLE_PRODUCTS[product]["default"])
                            cutting_choice = st.selectbox(
                                "בחר אופן חיתוך:",
                                cutting_options,
                                index=default_index,
                                key=f"search_cutting_{product}_{category_name}"
                            )
                            st.session_state[f"cutting_{product}"] = cutting_choice
                        if st.button(f"הוסף לעגלה - {product}", key=f"search_add_{product}_{category_name}"):
                            if selected_weight > 0:
                                is_valid_weight, error_message = check_minimum_weight(product, selected_weight)
                                if not is_valid_weight:
                                    st.error(error_message)
                                else:
                                    st.session_state.cart[product] = st.session_state.cart.get(product, 0) + selected_weight
                                    st.success(f"{product} ({selected_weight} קג) נוסף לעגלה!")
                                    st.rerun()

                    elif is_unit_product:
                        st.write("📦 נמכר ביחידות")
                        if product == "עוף שלם":
                            st.info("⚠️ משקל מינימום ליחידה: 1.6 קג")
                            min_units = 1
                        elif product in ["המבורגר הבית", "המבורגר 160 גרם", "המבורגר 220 גרם"]:
                            st.info("⚠️ מינימום הזמנה: 5 יחידות")
                            min_units = 5
                        else:
                            min_units = 1
                        selected_units = st.number_input(
                            "בחר כמות:",
                            min_value=int(min_units),
                            value=int(min_units),
                            step=1,
                            key=f"search_units_{product}_{category_name}"
                        )
                        if product in CUTTABLE_PRODUCTS:
                            st.write("🔪 אופן חיתוך:")
                            cutting_options = CUTTABLE_PRODUCTS[product]["options"]
                            default_index = cutting_options.index(CUTTABLE_PRODUCTS[product]["default"])
                            cutting_choice = st.selectbox(
                                "בחר אופן חיתוך:",
                                cutting_options,
                                index=default_index,
                                key=f"search_cutting_units_{product}_{category_name}"
                            )
                            st.session_state[f"cutting_{product}"] = cutting_choice
                        if st.button(f"הוסף לעגלה - {product}", key=f"search_add_units_{product}_{category_name}"):
                            product_name = product
                            if product in CUTTABLE_PRODUCTS:
                                cutting_choice = st.session_state.get(f"cutting_{product}", CUTTABLE_PRODUCTS[product]["default"])
                                product_name = f"{product} - {cutting_choice}"
                            st.session_state.cart[product_name] = st.session_state.cart.get(product_name, 0) + selected_units
                            st.success(f"{product_name} ({selected_units} יחידות) נוסף לעגלה!")
                            st.rerun()

                    else:
                        quantity = st.number_input(
                            "כמות:",
                            min_value=1,
                            value=1,
                            step=1,
                            key=f"search_qty_{product}_{category_name}"
                        )
                        if st.button(f"הוסף לעגלה - {product}", key=f"search_add_qty_{product}_{category_name}"):
                            st.session_state.cart[product] = st.session_state.cart.get(product, 0) + quantity
                            st.success(f"{product} ({quantity} יחידות) נוסף לעגלה!")
                            st.rerun()
        else:
            st.info("לא נמצאו מוצרים תואמים לחיפוש.")
    # --- סוף חיפוש מוצר (בגוף העמוד) ---
    
    # בחירת קטגוריה
    st.subheader("📂 בחר קטגוריה")
    category = st.selectbox("קטגוריה:", list(PRODUCT_CATEGORIES.keys()))
    
    # הצגת מוצרים בקטגוריה
    st.subheader(f"📦 מוצרים בקטגוריית {category}")
    
    products = PRODUCT_CATEGORIES[category]
    
    # יצירת עמודות למוצרים
    cols = st.columns(3)
    
    for i, product in enumerate(products):
        col_idx = i % 3
        with cols[col_idx]:
            st.write(f"**{product}**")
            
            # בדיקה אם המוצר נמכר במשקל או ביחידות
            is_weight_product = product in WEIGHT_PRODUCTS
            is_unit_product = product in UNIT_PRODUCTS
            
            if is_weight_product:
                st.write("⚖️ נמכר בקילו")
                # בחירת כמות במשקל - ללא מגבלה
                if product in ["עוף שלם", "עוף בלי עור"]:
                    st.info(f"⚠️ משקל מינימום: 1.6 קג")
                    min_weight = 1.6
                else:
                    min_weight = 0.5
                
                selected_weight = st.number_input(
                    "בחר משקל (קילו):",
                    min_value=float(min_weight),
                    value=float(min_weight),
                    step=0.1,
                    key=f"weight_{product}_{category}"
                )
                
                # הוספת אפשרויות חיתוך למוצרים שניתן לחתוך אותם
                if product in CUTTABLE_PRODUCTS:
                    st.write("🔪 אופן חיתוך:")
                    cutting_options = CUTTABLE_PRODUCTS[product]["options"]
                    default_index = cutting_options.index(CUTTABLE_PRODUCTS[product]["default"])
                    cutting_choice = st.selectbox(
                        "בחר אופן חיתוך:",
                        cutting_options,
                        index=default_index,
                        key=f"cutting_{product}_{category}"
                    )
                    # שמירת הבחירה ב-session state
                    st.session_state[f"cutting_{product}"] = cutting_choice
                
                if st.button(f"הוסף לעגלה - {product}", key=f"add_{product}_{category}"):
                    if selected_weight > 0:
                        # בדיקת משקל מינימום
                        is_valid_weight, error_message = check_minimum_weight(product, selected_weight)
                        if not is_valid_weight:
                            st.error(error_message)
                        else:
                            if product not in st.session_state.cart:
                                st.session_state.cart[product] = selected_weight
                            else:
                                st.session_state.cart[product] += selected_weight
                            st.success(f"{product} ({selected_weight} קג) נוסף לעגלה!")
                            st.rerun()
            
            elif is_unit_product:
                st.write("📦 נמכר ביחידות")
                # בחירת כמות ביחידות - ללא מגבלה
                if product == "עוף שלם":
                    st.info(f"⚠️ משקל מינימום ליחידה: 1.6 קג")
                    min_units = 1
                elif product in ["המבורגר הבית", "המבורגר 160 גרם", "המבורגר 220 גרם"]:
                    st.info(f"⚠️ מינימום הזמנה: 5 יחידות")
                    min_units = 5
                else:
                    min_units = 1
                
                selected_units = st.number_input(
                    "בחר כמות:",
                    min_value=int(min_units),
                    value=int(min_units),
                    step=1,
                    key=f"units_{product}_{category}"
                )
                
                # הוספת אפשרויות חיתוך למוצרי שווארמה
                if product in CUTTABLE_PRODUCTS:
                    st.write("🔪 אופן חיתוך:")
                    cutting_options = CUTTABLE_PRODUCTS[product]["options"]
                    default_index = cutting_options.index(CUTTABLE_PRODUCTS[product]["default"])
                    cutting_choice = st.selectbox(
                        "בחר אופן חיתוך:",
                        cutting_options,
                        index=default_index,
                        key=f"cutting_{product}_{category}"
                    )
                    # שמירת הבחירה ב-session state
                    st.session_state[f"cutting_{product}"] = cutting_choice
                
                if st.button(f"הוסף לעגלה - {product}", key=f"add_{product}_{category}"):
                    if selected_units > 0:
                        # הוספת אפשרות החיתוך לשם המוצר אם זה מוצר שווארמה
                        product_name = product
                        if product in CUTTABLE_PRODUCTS:
                            cutting_choice = st.session_state.get(f"cutting_{product}", CUTTABLE_PRODUCTS[product]["default"])
                            product_name = f"{product} - {cutting_choice}"
                        
                        if product_name not in st.session_state.cart:
                            st.session_state.cart[product_name] = selected_units
                        else:
                            st.session_state.cart[product_name] += selected_units
                        st.success(f"{product_name} ({selected_units} יחידות) נוסף לעגלה!")
                        st.rerun()
            
            else:
                # מוצר רגיל - בחירת כמות פשוטה
                quantity = st.number_input(
                    "כמות:",
                    min_value=1,
                    value=1,
                    step=1,
                    key=f"qty_{product}_{category}"
                )
                
                if st.button(f"הוסף לעגלה - {product}", key=f"add_{product}_{category}"):
                    if product not in st.session_state.cart:
                        st.session_state.cart[product] = quantity
                    else:
                        st.session_state.cart[product] += quantity
                    st.success(f"{product} ({quantity} יחידות) נוסף לעגלה!")
                    st.rerun()
    
    # הצגת פרטי משלוח רק אם יש פריטים בעגלה
    if st.session_state.cart:
        st.markdown("---")
        st.subheader("📋 פרטי משלוח")
        with st.form("delivery_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("שם מלא *", placeholder="לדוגמה: דוד כהן", key="full_name")
                if full_name:
                    is_valid_name, name_message = validate_hebrew_text(full_name, "שם מלא")
                    if is_valid_name:
                        st.success("✅ שם מלא תקין")
                    else:
                        st.error(f"❌ {name_message}")
                
                street_name = st.text_input("שם רחוב *", placeholder="לדוגמה: הרצל", key="street_name")
                if street_name:
                    is_valid_street, street_message = validate_hebrew_text(street_name, "שם רחוב")
                    if is_valid_street:
                        st.success("✅ שם רחוב תקין")
                    else:
                        st.error(f"❌ {street_message}")
                
                street_number = st.text_input("מספר בית *", placeholder="לדוגמה: 15", key="street_number")
                if street_number and not street_number.strip().isdigit():
                    st.error("❌ מספר בית חייב להכיל ספרות בלבד")
                
                floor_number = st.text_input("מספר קומה", placeholder="לדוגמה: 3, קומת קרקע, מרתף", key="floor_number")
                
                city = st.text_input("עיר *", placeholder="לדוגמה: בני ברק", key="city")
                if city:
                    is_valid_city, city_message = validate_hebrew_text(city, "עיר")
                    if is_valid_city:
                        st.success("✅ שם עיר תקין")
                    else:
                        st.error(f"❌ {city_message}")
            
            with col2:
                phone = st.text_input("מספר טלפון *", placeholder="לדוגמה: 050-1234567 או 02-1234567", key="phone")
                if phone:
                    is_valid_phone, clean_phone = validate_phone_number(phone)
                    if is_valid_phone:
                        st.success(f"✅ מספר טלפון תקין: {format_phone_number(clean_phone)}")
                    else:
                        st.error("❌ מספר טלפון אינו תקין")
                
                delivery_notes = st.text_area("הערות לשליח", placeholder="הוראות מיוחדות למשלוח, קוד כניסה לבניין וכו'", key="delivery_notes")
                butcher_notes = st.text_area("הערות לקצב", placeholder="הוראות מיוחדות לקצב, אופן חיתוך, הכנה וכו'", key="butcher_notes")
            st.subheader("✅ אימות הזמנה")
            st.write("**פריטי ההזמנה:**")
            for product, quantity in st.session_state.cart.items():
                is_weight_product = product in WEIGHT_PRODUCTS
                unit_text = "קילו" if is_weight_product else "יחידות"
                cutting_info = ""
                if product in CUTTABLE_PRODUCTS:
                    cutting_key = f"cutting_{product}"
                    if cutting_key in st.session_state:
                        cutting_choice = st.session_state[cutting_key]
                        if cutting_choice != CUTTABLE_PRODUCTS[product]["default"]:
                            cutting_info = f" (חיתוך: {cutting_choice})"
                st.write(f"• {product}: {quantity} {unit_text}{cutting_info}")
            # הצגת עלות משלוח לפי העיר
            delivery_cost = calculate_delivery_cost(st.session_state.cart, city)
            if city and "בני ברק" in city:
                st.info(f"🚚 עלות משלוח: {delivery_cost} ש\"ח (בני ברק)")
            else:
                st.info(f"🚚 עלות משלוח: {delivery_cost} ש\"ח")
            submitted = st.form_submit_button("✅ שלח הזמנה")
            if submitted:
                # בדיקת תקינות כל השדות
                validation_errors = []
                
                # בדיקת שם מלא
                if not full_name:
                    validation_errors.append("שם מלא הוא שדה חובה")
                else:
                    is_valid_name, name_message = validate_hebrew_text(full_name, "שם מלא")
                    if not is_valid_name:
                        validation_errors.append(name_message)
                
                # בדיקת שם רחוב
                if not street_name:
                    validation_errors.append("שם רחוב הוא שדה חובה")
                else:
                    is_valid_street, street_message = validate_hebrew_text(street_name, "שם רחוב")
                    if not is_valid_street:
                        validation_errors.append(street_message)
                
                # בדיקת מספר בית
                if not street_number:
                    validation_errors.append("מספר בית הוא שדה חובה")
                elif not street_number.strip().isdigit():
                    validation_errors.append("מספר בית חייב להכיל ספרות בלבד")
                
                # בדיקת עיר
                if not city:
                    validation_errors.append("עיר היא שדה חובה")
                else:
                    is_valid_city, city_message = validate_hebrew_text(city, "עיר")
                    if not is_valid_city:
                        validation_errors.append(city_message)
                
                # בדיקת טלפון
                if not phone:
                    validation_errors.append("מספר טלפון הוא שדה חובה")
                else:
                    is_valid_phone, clean_phone = validate_phone_number(phone)
                    if not is_valid_phone:
                        validation_errors.append("מספר טלפון אינו תקין")
                
                # אם אין שגיאות, שלח את ההזמנה
                if not validation_errors:
                    # יצירת או מציאת לקוח
                    customer_id = find_or_create_customer(format_phone_number(clean_phone), full_name)
                    
                    new_order = {
                        'id': len(orders) + 1,
                        'customer_id': customer_id,  # קישור ללקוח
                        'customer_name': full_name,
                        'phone': format_phone_number(clean_phone),
                        'address': {
                            'street_name': street_name,
                            'street_number': street_number,
                            'floor_number': floor_number if floor_number else '',
                            'city': city
                        },
                        'delivery_notes': delivery_notes,
                        'butcher_notes': butcher_notes,
                        'cutting_instructions': get_cutting_instructions(st.session_state.cart),
                        'items': st.session_state.cart.copy(),
                        'status': 'pending',
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    # שמירת ההזמנה במסד הנתונים
                    order_id = save_order_with_customer(new_order)
                    st.success("🎉 ההזמנה נשלחה בהצלחה!")
                    st.balloons()
                    # ניקוי העגלה אחרי הצגת הודעת ההצלחה
                    st.session_state.cart.clear()
                    # הוספת דגל שמציין שההזמנה נשלחה בהצלחה
                    st.session_state.order_sent = True
                    st.rerun()
                else:
                    # הצגת כל השגיאות
                    st.error("❌ יש שגיאות בטופס:")
                    for error in validation_errors:
                        st.error(f"• {error}")
    else:
        # בדיקה אם הזמנה נשלחה בהצלחה
        if st.session_state.get('order_sent', False):
            st.success("🎉 ההזמנה נשלחה בהצלחה! תודה על הזמנתך!")
            st.info("💡 תוכל להוסיף מוצרים חדשים לעגלה ולהמשיך להזמין")
            # איפוס הדגל
            st.session_state.order_sent = False
        else:
            st.info("🛒 העגלה ריקה. הוסף מוצרים מהרשימה למעלה כדי להתחיל הזמנה!")

def show_tracking_page(orders):
    """מציג את דף מעקב הזמנות"""
    st.header("📋 מעקב הזמנות")
    
    if not orders:
        st.info("אין הזמנות עדיין")
        return
    
    # חיפוש לפי שם או טלפון
    st.subheader("🔍 חיפוש הזמנה")
    search_term = st.text_input("הקלד שם מלא או מספר טלפון:", key="search_order")
    
    if search_term:
        # חיפוש הזמנות
        filtered_orders = []
        for order in orders:
            if (search_term.lower() in order['customer_name'].lower() or 
                search_term in order['phone']):
                filtered_orders.append(order)
        
        if filtered_orders:
            st.subheader(f"📊 נמצאו {len(filtered_orders)} הזמנות")
            
            for order in filtered_orders:
                with st.expander(f"הזמנה #{order['id']} - {order['customer_name']} ({order['created_at']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**שם:** {order['customer_name']}")
                        st.write(f"**טלפון:** {order['phone']}")
                        
                        # הצגת כתובת עם מספר קומה
                        address_parts = [order['address']['street_name'], order['address']['street_number']]
                        if order['address'].get('floor_number'):
                            address_parts.append(f"קומה {order['address']['floor_number']}")
                        address_parts.append(order['address']['city'])
                        full_address = ", ".join(address_parts)
                        st.write(f"**כתובת:** {full_address}")
                        
                        if order['delivery_notes']:
                            st.write(f"**הערות לשליח:** {order['delivery_notes']}")
                        if order.get('butcher_notes'):
                            st.write(f"**הערות לקצב:** {order['butcher_notes']}")
                    
                    with col2:
                        st.write(f"**סטטוס:** {get_status_hebrew(order['status'])}")
                        # הצגת תאריך בפורמט קריא יותר
                        created_date = order.get('created_at', '')
                        if created_date:
                            try:
                                from datetime import datetime
                                date_obj = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S')
                                formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
                                st.write(f"**תאריך הזמנה:** {formatted_date}")
                            except:
                                st.write(f"**תאריך הזמנה:** {created_date}")
                        else:
                            st.write("**תאריך הזמנה:** לא זמין")
                    
                    # הצגת פריטי ההזמנה
                    st.subheader("📦 פריטי ההזמנה")
                    for item, quantity in order['items'].items():
                        is_weight_product = item in WEIGHT_PRODUCTS
                        unit_text = "קילו" if is_weight_product else "יחידות"
                        st.write(f"• {item} - {quantity} {unit_text}")
                    
                    # הצגת הוראות חיתוך אם קיימות
                    if 'cutting_instructions' in order and order['cutting_instructions']:
                        st.subheader("🔪 הוראות חיתוך")
                        for instruction in order['cutting_instructions']:
                            st.info(instruction)
                    
                    # כפתור הדפסה
                    # בעת שליחת הזמנה לא תתבצע הדפסה אוטומטית ולא יוצג כפתור הדפסה
        else:
            st.warning("לא נמצאו הזמנות")
    else:
        st.info("הקלד שם או מספר טלפון כדי לחפש הזמנות")

def get_status_hebrew(status):
    """מחזיר את הסטטוס בעברית"""
    status_map = {
        'pending': 'ממתין לאישור',
        'processing': 'בטיפול',
        'completed': 'הושלם',
        'cancelled': 'בוטל'
    }
    return status_map.get(status, status)

if __name__ == "__main__":
    main() 
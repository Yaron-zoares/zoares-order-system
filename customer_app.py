import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import webbrowser

# הגדרת כותרת האפליקציה
st.set_page_config(
    page_title="הזמנת מוצרים - Zoares",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# נתיב לקובץ הנתונים
ORDERS_FILE = 'orders.json'

# רשימת מוצרים מאורגנת לפי קטגוריות
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
        "סטייק אנטריקוט",
        "צלעות בקר",
        "בשר כבש",
        "המבורגר בקר",
        "בשר טחון מעורב",
        "בשר עגל",
        "בשר עגל טחון",
        "בשר עגל טחון עם שומן כבש",
        "בשר אסאדו",
        "פילה מדומה",
        "פילה פרמיום",
        "צלעות",
        "בשר שריר",
        "אונטריב",
        "רגל פרה",
        "עצמות",
        "גידים",
        "בשר ראש (לחי)",
        "בשר לחיים (ראש)",
        "אצבעות אנטריקוט",
        "ריבס אנטריקוט",
        "אסאדו עם עצם מקוצב 4 צלעות",
        "צלי כתף",
        "בננות שריר",
        "אנטריקוט פיידלוט פרימיום",
        "כבד אווז",
        "שקדי עגל גרון /לב",
        "עצמות מח",
        "רגל פרה",
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
        "הודו שלם",
        "חזה הודו",
        "שווארמה הודו נקבה",
        "קורקבן הודו",
        "כנפיים הודו",
        "שוקיים הודו",
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

# מוצרים שנמכרים במשקל (בקילו)
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
    "סטייק אנטריקוט": True,
    "צלעות בקר": True,
    "בשר כבש": True,
    "בשר טחון מעורב": True,
    "בשר עגל": True,
    "בשר עגל טחון": True,
    "בשר עגל טחון עם שומן כבש": True,
    "בשר אסאדו": True,
    "פילה מדומה": True,
    "צלעות": True,
    "בשר שריר": True,
    "אונטריב": True,
    "רגל פרה": True,
    "עצמות": True,
    "גידים": True,
    "בשר ראש (לחי)": True,
    "בשר לחיים (ראש)": True,
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

# מוצרים שניתן לחתוך אותם
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

    "סטייק אנטריקוט": {
        "name": "סטייק אנטריקוט", 
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
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
    "בשר עגל": {
        "name": "בשר עגל",
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
    "בשר אסאדו": {
        "name": "בשר אסאדו",
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

# מוצרים שנמכרים ביחידות
UNIT_PRODUCTS = {
    "עוף שלם": True,
    "נקניקיות עוף": True,
    "המבורגר עוף": True,
    "שווארמה עוף (פרגיות)": True,
    "הודו שלם": True,
    "חזה הודו": True,
    "שווארמה הודו נקבה": True,
    "קורקבן הודו": True,
    "כנפיים הודו": True,
    "שוקיים הודו": True,
    "גרון הודו": True,
    "כנפיים עוף": True,
    "ירכיים": True,
    "שוקיים עוף": True,
    "שוקיים הודו": True,
    "לבבות הודו נקבה": True,
    "גרון הודו": True,
    "ביצי הודו": True,
    "המבורגר בקר": True,
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

# הסרת מגבלת משקל - אין מגבלה
# MAX_WEIGHT_LIMIT = 8.0

# מחירים למוצרים (בשקלים)
PRODUCT_PRICES = {
    "עוף שלם": 50.0,
    "חזה עוף": 40.0,
    "שניצל עוף": 35.0,
    "כנפיים": 15.0,
    "כרעיים": 10.0,
    "כרעיים עוף": 12.0,
    "שוקיים עוף": 15.0,
    "קורקבן עוף": 18.0,
    "טחול עוף": 16.0,
    "ירכיים": 18.0,
    "כבד עוף": 20.0,
    "לב עוף": 25.0,
    "עוף טחון": 30.0,
    "טחון מיוחד (שווארמה נקבה, פרגית וחזה עוף)": 35.0,
    "נקניקיות עוף": 10.0,
    "המבורגר עוף": 20.0,
    "שווארמה עוף (פרגיות)": 15.0,
    "הודו שלם": 45.0,
    "חזה הודו": 35.0,
    "שווארמה הודו נקבה": 25.0,
    "קורקבן הודו": 20.0,
    "כנפיים הודו": 18.0,
    "שוקיים הודו": 15.0,
    "לבבות הודו נקבה": 22.0,
    "גרון הודו": 18.0,
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
    "בשר אסאדו": 70.0,
    "פילה מדומה": 80.0,
    "פילה פרמיום": 90.0,
    "צלעות": 75.0,
    "בשר שריר": 60.0,
    "אונטריב": 85.0,
    "רגל פרה": 40.0,
    "עצמות": 25.0,
    "גידים": 45.0,
    "בשר ראש (לחי)": 60.0,
    "סלמון": 80.0,
    "טונה": 70.0,
    "מושט": 65.0,
    "אחר": 50.0,
    "המבורגר": 25.0,
    "המבורגר הבית": 30.0,
    "נקניקיות": 18.0,
    "נקניק חריף": 22.0
}

def load_orders():
    """טוען את ההזמנות מקובץ JSON"""
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_orders(orders):
    """שומר את ההזמנות לקובץ JSON"""
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

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
            # נסה לקבל את בחירת החיתוך מ-session state
            cutting_key = f"cutting_{product}"
            if cutting_key in st.session_state:
                cutting_choice = st.session_state[cutting_key]
                if cutting_choice != CUTTABLE_PRODUCTS[product]["default"]:
                    instructions.append(f"{product}: {cutting_choice}")
            else:
                # אם לא נבחר, השתמש בברירת מחדל
                instructions.append(f"{product}: {CUTTABLE_PRODUCTS[product]['default']}")
    
    return instructions

def main():
    st.title("🛒 Zoares - הזמנת מוצרים")
    st.markdown("---")
    
    # טעינת הזמנות
    orders = load_orders()
    
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
                # בחירת כמות במשקל - מותאם למוצרים עם דרישת מינימום
                if product in ["עוף שלם", "עוף בלי עור"]:
                    weight_options = [1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.5, 4.0, 4.5, 5.0]
                    st.info(f"⚠️ משקל מינימום: 1.6 קג")
                else:
                    weight_options = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
                
                selected_weight = st.selectbox(
                    "בחר משקל (קילו):",
                    weight_options,
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
                # בחירת כמות ביחידות - מותאם למוצרים עם דרישת מינימום
                if product == "עוף שלם":
                    unit_options = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20]
                    st.info(f"⚠️ משקל מינימום ליחידה: 1.6 קג")
                elif product in ["המבורגר הבית", "המבורגר 160 גרם", "המבורגר 220 גרם"]:
                    unit_options = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
                    st.info(f"⚠️ מינימום הזמנה: 5 יחידות")
                else:
                    unit_options = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20]
                
                selected_units = st.selectbox(
                    "בחר כמות:",
                    unit_options,
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
                    new_order = {
                        'id': len(orders) + 1,
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
                    orders.append(new_order)
                    save_orders(orders)
                    st.success("🎉 ההזמנה נשלחה בהצלחה!")
                    st.balloons()
                    st.session_state.cart.clear()
                    st.rerun()
                else:
                    # הצגת כל השגיאות
                    st.error("❌ יש שגיאות בטופס:")
                    for error in validation_errors:
                        st.error(f"• {error}")
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
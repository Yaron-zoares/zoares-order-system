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
        "ירכיים עוף",
        "עוף עם עור",
        "עוף בלי עור",
        "כבד עוף",
        "לב עוף",
        "עוף טחון",
        "נקניקיות עוף",
        "שווארמה עוף (פרגיות)",
        "שווארמה הודו",
        "הודו שלם",
        "חזה הודו",
        "קורקבן הודו",
        "כנפיים הודו",
        "שוקיים הודו",
        "ביצי הודו"
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
        "צלעות",
        "בשר שריר",
        "אונטריב",
        "רגל פרה",
        "עצמות",
        "גידים",
        "בשר ראש (לחי)"
    ],
    "דגים": [
        "סלמון",
        "טונה",
        "מושט",
        "אחר"
    ],
    "אחר": [
        "נקניקיות עוף",
        "נקניקיות חריפות (מרגז)",
        "צ'יפס"
    ],
}

# מוצרים שנמכרים במשקל (בקילו)
WEIGHT_PRODUCTS = {
    "עוף שלם": True,
    "חזה עוף": True,
    "שניצל עוף": True,
    "כנפיים": True,
    "כרעיים עוף": True,
    "ירכיים": True,
    "ירכיים עוף": True,
    "עוף עם עור": True,
    "עוף בלי עור": True,
    "כבד עוף": True,
    "לב עוף": True,
    "עוף טחון": True,
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
    "סלמון": True,
    "טונה מושטפת": True,
   
}

# מוצרים שניתן לחתוך אותם
CUTTABLE_PRODUCTS = {
    "עוף שלם": {
        "name": "עוף שלם",
        "options": ["שלם", "פרוס", "פרוס לחלקים", "קוביות"],
        "default": "שלם"
    },
    "חזה עוף": {
        "name": "חזה עוף",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "כרעיים עוף": {
        "name": "כרעיים עוף",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "ירכיים": {
        "name": "ירכיים",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "ירכיים עוף": {
        "name": "ירכיים עוף",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "עוף עם עור": {
        "name": "עוף עם עור",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
    },
    "עוף בלי עור": {
        "name": "עוף בלי עור",
        "options": ["שלם", "פרוס", "קוביות"],
        "default": "שלם"
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
        "options": ["שיפודים", "רצועות", "פרוס", "שלם"],
        "default": "שלם"
    },
    "שווארמה הודו": {
        "name": "שווארמה הודו",
        "options": ["שיפודים", "רצועות", "פרוס", "שלם"],
        "default": "שלם"
    }
}

# מוצרים שנמכרים ביחידות
UNIT_PRODUCTS = {
    "נקניקיות עוף": True,
    "המבורגר עוף": True,
    "שווארמה עוף (פרגיות)": True,
    "הודו שלם": True,
    "חזה הודו": True,
    "שווארמה הודו": True,
    "קורקבן הודו": True,
    "כנפיים הודו": True,
    "שוקיים הודו": True,
    "גרון הודו": True,
    "כנפיים עוף": True,
    "ביצי הודו": True,
    "המבורגר בקר": True,
    "המבורגר": True,
    "נקניקיות": True,
    "נקניק חריף": True,
    "סלמון": True,
    "טונה": True,
    "מושט": True
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
    "הודו שלם": 45.0,
    "חזה הודו": 35.0,
    "שווארמה הודו": 25.0,
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
    "בשר אסאדו": 70.0,
    "פילה מדומה": 80.0,
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

def calculate_delivery_cost(cart):
    """מחשבת עלות משלוח קבועה"""
    # עלות משלוח קבועה לכל הזמנה
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
    
    # הצגת מספר פריטים בעגלה
    if 'cart' in st.session_state and st.session_state.cart:
        cart_count = sum(st.session_state.cart.values())
        st.sidebar.info(f"🛒 עגלת קניות: {cart_count} פריטים")
        
        # הצגת משקל כולל
        total_weight = calculate_cart_weight(st.session_state.cart)
        if total_weight > 0:
            st.sidebar.metric("⚖️ משקל כולל", f"{total_weight:.1f} ק\"ג")
            
            # הסרת אזהרות משקל - אין מגבלה
        
        # הצגת פריטי העגלה בסיידבר
        st.sidebar.subheader("פריטי העגלה:")
        for product, qty in st.session_state.cart.items():
            is_weight_product = product in WEIGHT_PRODUCTS
            unit_text = "קילו" if is_weight_product else "יחידות"
            st.sidebar.write(f"• {product} x{qty} {unit_text}")
        
        # כפתור לריקון העגלה בסיידבר
        if st.sidebar.button("🗑️ רוקן עגלה", type="secondary", key="clear_cart_sidebar"):
            st.session_state.cart.clear()
            st.rerun()
    
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
    
    **הקטגוריות שלנו:**
    - 🍗 עופות - עוף טרי ואיכותי, הודו
    - 🥩 בשר - בשר בקר, כבש, בשר איכותי על האש
    - 🐟 דגים - סלמון, טונה ועוד
    - 🥚 אחר - מוצרים נוספים
    
    ### 🚚 משלוחים
   
    - משלוח עד הבית
    - עלות משלוח: מוסתר בשלב זה 

    - אימות מספר טלפון אוטומטי
    
    ### 🔪 שירותי חיתוך
    - עוף שלם: שלם, פרוס, פרוס לחלקים
    - בשר בקר: שלם או פרוס
    - חיתוך מותאם אישית לכל הזמנה
    
    ### 📞 יצירת קשר
    - טלפון: 03-5700842
    - וואטסאפ: 052-3656714
    - שעות פעילות (למעט חגים): א'-ה' 6:00-14:00, ו' 6:00-14:00
    """)
    
    # הצגת מוצרים מובילים
    st.subheader("🔥 מוצרים מובילים")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🍗 שניצל ופילה עוף")
        st.write("שניצל ופילה עוף טרי ואיכותי")
    
    with col2:
        st.info("🥩 עוף ובשר טחון")
        st.write("עוף ובשר טחון טרי לקציצות והמבורגרים")
    
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
                # בחירת כמות במשקל
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
                        # הסרת בדיקת משקל - אין מגבלה
                        if product not in st.session_state.cart:
                            st.session_state.cart[product] = selected_weight
                        else:
                            st.session_state.cart[product] += selected_weight
                        st.success(f"{product} ({selected_weight} קילו) נוסף לעגלה!")
                        st.rerun()
            
            elif is_unit_product:
                st.write("📦 נמכר ביחידות")
                # בחירת כמות ביחידות
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
    
    # הצגת העגלה
    if st.session_state.cart:
        st.markdown("---")
        st.subheader("🛒 עגלת הקניות שלך")
        
        # הצגת משקל כולל ואזהרות
        total_weight = calculate_cart_weight(st.session_state.cart)
        if total_weight > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("⚖️ משקל כולל", f"{total_weight:.1f} ק\"ג")
            with col2:
                st.write("📏 אין מגבלת משקל")
            
            # הסרת אזהרות משקל - אין מגבלה
        
        # הצגת הוראות חיתוך
        cutting_instructions = get_cutting_instructions(st.session_state.cart)
        if cutting_instructions:
            st.subheader("🔪 הוראות חיתוך")
            for instruction in cutting_instructions:
                st.info(instruction)
        
        for product, quantity in st.session_state.cart.items():
            price = PRODUCT_PRICES.get(product, 0)
            is_weight_product = product in WEIGHT_PRODUCTS
            unit_text = "קילו" if is_weight_product else "יחידות"
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            with col1:
                st.write(product)
            with col2:
                st.write("מוסתר בשלב זה")
            with col3:
                qty_col1, qty_col2, qty_col3 = st.columns(3)
                with qty_col1:
                    if st.button("➖", key=f"dec_{product}_{category}"):
                        if is_weight_product:
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
                with qty_col2:
                    st.write(f"**{quantity} {unit_text}**")
                with qty_col3:
                    if st.button("➕", key=f"inc_{product}_{category}"):
                        if is_weight_product:
                            st.session_state.cart[product] += 0.5
                            st.rerun()
                        else:
                            st.session_state.cart[product] += 1
                            st.rerun()
            with col4:
                st.write("מוסתר בשלב זה")
            with col5:
                if st.button(f"🗑️", key=f"remove_{product}_{category}"):
                    del st.session_state.cart[product]
                    st.rerun()
        
        st.markdown("---")
        if st.button("🗑️ רוקן עגלה", type="secondary", key="clear_cart_order_page"):
            st.session_state.cart.clear()
            st.rerun()
        
        st.markdown("---")
        st.subheader("📋 פרטי משלוח")
        with st.form("delivery_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("שם מלא *", key="full_name")
                street_name = st.text_input("שם רחוב *", key="street_name")
                street_number = st.text_input("מספר בית *", key="street_number")
                floor_number = st.text_input("מספר קומה", placeholder="לדוגמה: 3, קומת קרקע, מרתף", key="floor_number")
                city = st.text_input("עיר *", key="city")
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
            # הצגת רק עלות משלוח
            delivery_cost = calculate_delivery_cost(st.session_state.cart)
            st.info(f"🚚 עלות משלוח: מוסתר בשלב זה")
            submitted = st.form_submit_button("✅ שלח הזמנה")
            if submitted:
                if full_name and street_name and street_number and city and phone and is_valid_phone:
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
                    st.error("אנא מלא את כל השדות המסומנים ב-*")
    else:
        st.info("העגלה ריקה. הוסף מוצרים כדי להתחיל הזמנה!")

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
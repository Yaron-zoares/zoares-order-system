import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import webbrowser
from io import StringIO
import calendar
import matplotlib.pyplot as plt
from database import (
    init_database, load_orders, save_order, load_closed_orders,
    load_customers, save_customers, find_or_create_customer, 
    update_customer_stats, cleanup_old_customers, cleanup_old_orders,
    update_order, delete_order, move_order_to_closed, get_next_order_id,
    import_existing_data
)

# אתחול מסד הנתונים וייבוא נתונים קיימים
if not os.path.exists('zoares_central.db'):
    init_database()
    import_existing_data()

# הגדרת כותרת האפליקציה
st.set_page_config(
    page_title="מערכת ניהול הזמנות",
    page_icon="🐓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# הגדרות מסד הנתונים המרכזי
# כל הנתונים נשמרים במסד הנתונים SQLite המרכזי

# הגדרות שמירה
ACTIVE_ORDER_RETENTION_DAYS = 20  # ימי עסקים להזמנות פעילות
CLOSED_ORDER_RETENTION_DAYS = 1825  # 5 שנים להזמנות סגורות

# רשימת מוצרים מאורגנת לפי קטגוריות
PRODUCT_CATEGORIES = {
    "עופות": [
        "עוף שלם",
        "חזה עוף",
        "שניצל עוף",
        "כנפיים",
        "כרעיים",
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
    ]
}

# הגדרת מוצרים שנמכרים במשקל (ק"ג) או ביחידות
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

def get_product_unit(product_name):
    """מחזיר את היחידה המתאימה למוצר (ק"ג או יחידות)"""
    # הסרת הוראות חיתוך מהשם אם קיימות
    base_product = product_name.split(' - ')[0] if ' - ' in product_name else product_name
    
    if base_product in WEIGHT_PRODUCTS:
        return "ק\"ג"
    elif base_product in UNIT_PRODUCTS:
        return "יחידות"
    else:
        # ברירת מחדל - בדיקה לפי קטגוריה
        for category, products in PRODUCT_CATEGORIES.items():
            if base_product in products:
                # מוצרי בשר ועוף בדרך כלל נמכרים במשקל
                if category in ["עופות", "בשר"]:
                    return "ק\"ג"
                # מוצרים אחרים בדרך כלל נמכרים ביחידות
                else:
                    return "יחידות"
        # אם לא נמצא, ברירת מחדל ליחידות
        return "יחידות"

def format_quantity_with_unit(quantity, product_name):
    """מעצב כמות עם יחידה מתאימה"""
    unit = get_product_unit(product_name)
    return f"{quantity} {unit}"

# מחירים לפי מוצר (לשימוש בדף הוספת הזמנה ועריכת הזמנות לקוחות)
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
    "בשר ראש (לחי)": 60.0,
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
    "מלח": 5.0
}

# אפשרויות חיתוך למוצרי שווארמה
SHAWARMA_CUTTING_OPTIONS = {
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

# אפשרויות חיתוך למוצרים נוספים
ADDITIONAL_CUTTING_OPTIONS = {
    "עוף בלי עור": {
        "name": "עוף בלי עור",
        "options": ["פרוס", "קוביות", "שלם"],
        "default": "שלם"
    }
}

def is_business_day(date):
    """בודק אם התאריך הוא יום עסקים (לא שבת)"""
    return date.weekday() != 5  # 5 = שבת

def get_business_days_before(target_date, days):
    """מחזיר תאריך לפני מספר ימי עסקים"""
    current_date = target_date
    business_days_counted = 0
    
    while business_days_counted < days:
        current_date -= timedelta(days=1)
        if is_business_day(current_date):
            business_days_counted += 1
    
    return current_date

# הפונקציות לניהול מונה הזמנות מיובאות מ-database.py

# הפונקציות לניהול הזמנות מיובאות מ-database.py

# הפונקציות לניהול הזמנות סגורות מיובאות מ-database.py

# פונקציית הניקוי מיובאת מ-database.py

def generate_order_html(order):
    """מייצר HTML להדפסת הזמנה"""
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>הזמנה #{order['id']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; direction: rtl; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
            .order-info {{ margin-bottom: 20px; }}
            .customer-info {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .items-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            .items-table th, .items-table td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
            .items-table th {{ background-color: #f2f2f2; }}
            .total {{ font-size: 18px; font-weight: bold; text-align: left; }}
            .status {{ padding: 5px 10px; border-radius: 3px; color: white; }}
            .status-pending {{ background-color: #ffc107; }}
            .status-processing {{ background-color: #17a2b8; }}
            .status-completed {{ background-color: #28a745; }}
            .status-cancelled {{ background-color: #dc3545; }}
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🐓 Zoares - הזמנה #{order['id']}</h1>
            <p>תאריך יצירה: {order['created_at']}</p>
        </div>
        
        <div class="customer-info">
            <h3>📋 פרטי לקוח</h3>
            <p><strong>שם:</strong> {order['customer_name']}</p>
    """
    
    # הוספת פרטי כתובת אם קיימים
    if 'address' in order and order['address']:
        address = order['address']
        if isinstance(address, dict):
            html += f"""
            <p><strong>כתובת:</strong> {address.get('street_name', '')} {address.get('street_number', '')}, {address.get('city', '')}</p>
            """
        else:
            html += f"<p><strong>כתובת:</strong> {address}</p>"
    
    # הוספת טלפון אם קיים
    if 'phone' in order and order['phone']:
        html += f"<p><strong>טלפון:</strong> {order['phone']}</p>"
    
    # הוספת הערות אם קיימות
    if 'delivery_notes' in order and order['delivery_notes']:
        html += f"<p><strong>הערות לשליח:</strong> {order['delivery_notes']}</p>"
    if 'butcher_notes' in order and order['butcher_notes']:
        html += f"<p><strong>הערות לקצב:</strong> {order['butcher_notes']}</p>"
    
    html += """
        </div>
        
        <div class="order-info">
            <h3>📦 פריטי ההזמנה</h3>
            <table class="items-table">
                <thead>
                    <tr>
                        <th>מוצר</th>
                        <th>כמות</th>
                        <th>מחיר ליחידה</th>
                        <th>סה"כ</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # הוספת פריטי ההזמנה
    if ('items' in order and 
        order['items'] and 
        isinstance(order['items'], dict)):
        # הזמנת לקוח עם פריטים מרובים
        for item, quantity in order['items'].items():
            price = PRODUCT_PRICES.get(item, 0)
            total = price * quantity
            html += f"""
                <tr>
                    <td>{item}</td>
                    <td>{format_quantity_with_unit(quantity, item)}</td>
                    <td>מוסתר בשלב זה</td>
                    <td>מוסתר בשלב זה</td>
                </tr>
            """
    else:
        # הזמנה רגילה עם מוצר אחד
        product = order.get('product', 'מוצר לא ידוע')
        quantity = order.get('quantity', 0)
        price = order.get('price', 0)
        total = price * quantity
        html += f"""
            <tr>
                <td>{product}</td>
                <td>{format_quantity_with_unit(quantity, product)}</td>
                <td>מוסתר בשלב זה</td>
                <td>מוסתר בשלב זה</td>
            </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    """
    
    # חישוב סה"כ
    delivery_cost = 20.0
    html += f"""
        <div class="total">
            <p><strong>עלות משלוח:</strong> מוסתר בשלב זה</p>
        </div>
        
        <div class="order-info">
            <h3>📊 סטטוס הזמנה</h3>
            <span class="status status-{order['status']}">{get_status_hebrew(order['status'])}</span>
        </div>
        
        <div class="no-print" style="margin-top: 30px; text-align: center;">
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">הדפס הזמנה</button>
        </div>
    </body>
    </html>
    """
    
    return html

def print_order(order):
    """מדפיס הזמנה"""
    html_content = generate_order_html(order)
    
    # שמירת HTML לקובץ זמני
    temp_file = f"order_{order['id']}.html"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # פתיחת הקובץ בדפדפן להדפסה
    try:
        webbrowser.open(f'file://{os.path.abspath(temp_file)}')
        st.success(f"הזמנה #{order['id']} נפתחה להדפסה!")
    except Exception as e:
        st.error(f"שגיאה בפתיחת הקובץ להדפסה: {e}")

def get_status_hebrew(status):
    """מחזיר את הסטטוס בעברית"""
    status_map = {
        "pending": "ממתין",
        "processing": "בטיפול",
        "completed": "הושלם",
        "cancelled": "בוטל"
    }
    return status_map.get(status, status)

def show_order_details(order):
    """מציג פרטי הזמנה מפורטים"""
    st.header(f"📋 פרטי הזמנה #{order['id']}")
    
    # פרטי לקוח
    st.subheader("👤 פרטי לקוח")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**שם:** {order['customer_name']}")
        if 'phone' in order and order['phone']:
            st.write(f"**טלפון:** {order['phone']}")
    
    with col2:
        if 'address' in order and order['address']:
            address = order['address']
            if isinstance(address, dict):
                st.write(f"**כתובת:** {address.get('street_name', '')} {address.get('street_number', '')}")
                st.write(f"**עיר:** {address.get('city', '')}")
            else:
                st.write(f"**כתובת:** {address}")
    
    if 'delivery_notes' in order and order['delivery_notes']:
        st.write(f"**הערות לשליח:** {order['delivery_notes']}")
    if 'butcher_notes' in order and order['butcher_notes']:
        st.write(f"**הערות לקצב:** {order['butcher_notes']}")
    
    # פרטי תאריך ושעה
    st.subheader("📅 פרטי תאריך ושעה")
    col1, col2 = st.columns(2)
    with col1:
        created_date = order.get('created_at', '')
        if created_date:
            try:
                date_obj = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
                st.write(f"**תאריך יצירה:** {formatted_date}")
            except:
                st.write(f"**תאריך יצירה:** {created_date}")
        else:
            st.write("**תאריך יצירה:** לא זמין")
    
    with col2:
        if 'closed_at' in order and order['closed_at']:
            closed_date = order['closed_at']
            try:
                date_obj = datetime.strptime(closed_date, '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
                st.write(f"**תאריך סגירה:** {formatted_date}")
            except:
                st.write(f"**תאריך סגירה:** {closed_date}")
        else:
            st.write("**תאריך סגירה:** הזמנה פעילה")
    
    # פרטי הזמנה
    st.subheader("📦 פריטי ההזמנה")
    
    if ('items' in order and 
        order['items'] and 
        isinstance(order['items'], dict)):
        # הזמנת לקוח עם פריטים מרובים
        items_data = []
        for item, quantity in order['items'].items():
            price = PRODUCT_PRICES.get(item, 0)
            total = price * quantity
            items_data.append({
                'מוצר': item,
                'כמות': format_quantity_with_unit(quantity, item),
                # מחירים מוסתרים בשלב זה
            })
        
        df_items = pd.DataFrame(items_data)
        st.dataframe(df_items, use_container_width=True)
    else:
        # הזמנה רגילה עם מוצר אחד
        product = order.get('product', 'מוצר לא ידוע')
        quantity = order.get('quantity', 0)
        price = order.get('price', 0)
        total = price * quantity
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**מוצר:** {product}")
        with col2:
            st.write(f"**כמות:** {format_quantity_with_unit(quantity, product)}")
        # מחירים מוסתרים בשלב זה
    
    # סיכום
    st.subheader("💰 סיכום")
    delivery_cost = 20.0
    col1, col2 = st.columns(2)
    with col1:
        st.metric("עלות משלוח", "מוסתר בשלב זה")
    with col2:
        st.metric("סטטוס", get_status_hebrew(order['status']))
    
    # כפתורי פעולה
    st.subheader("🔧 פעולות")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🖨️ הדפס הזמנה", key=f"print_{order['id']}"):
            print_order(order)
    
    with col2:
        if st.button("📧 שלח לווטסאפ", key=f"whatsapp_{order['id']}"):
            if 'phone' in order and order['phone']:
                phone = order['phone'].replace('-', '').replace(' ', '')
                if phone.startswith('0'):
                    phone = '972' + phone[1:]
                
                # יצירת הודעה עם פרטי ההזמנה
                message = f"שלום! הזמנה #{order['id']} שלך מוכנה.\n\n"
                message += f"שם: {order['customer_name']}\n"
                
                # הוספת פרטי כתובת
                if 'address' in order and order['address']:
                    address = order['address']
                    if isinstance(address, dict):
                        address_text = f"{address.get('street_name', '')} {address.get('street_number', '')}, {address.get('city', '')}"
                        message += f"כתובת: {address_text}\n"
                
                # הוספת הערות
                if 'delivery_notes' in order and order['delivery_notes']:
                    message += f"הערות לשליח: {order['delivery_notes']}\n"
                if 'butcher_notes' in order and order['butcher_notes']:
                    message += f"הערות לקצב: {order['butcher_notes']}\n"
                
                # הוספת פריטי ההזמנה
                message += "\nפריטי ההזמנה:\n"
                if ('items' in order and 
                    order['items'] and 
                    isinstance(order['items'], dict)):
                    # הזמנת לקוח עם פריטים מרובים
                    for item, quantity in order['items'].items():
                        message += f"• {item}: {format_quantity_with_unit(quantity, item)}\n"
                else:
                    # הזמנה רגילה עם מוצר אחד
                    product = order.get('product', 'מוצר לא ידוע')
                    quantity = order.get('quantity', 0)
                    message += f"• {product}: {format_quantity_with_unit(quantity, product)}\n"
                
                message += f"\nסטטוס: {get_status_hebrew(order['status'])}\n"
                message += f"תאריך הזמנה: {order.get('created_at', '')}\n\n"
                message += "תודה על ההזמנה! 🐓"
                
                # קידוד ההודעה ל-URL
                import urllib.parse
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
                
                st.success("📧 הודעה מוכנה לווטסאפ!")
                st.markdown(f"[💬 פתח ווטסאפ עם הודעה מוכנה]({whatsapp_url})")
                st.info("💡 טיפ: הקישור יפתח את ווטסאפ עם הודעה מוכנה שתוכל לשלוח")
            else:
                st.warning("אין מספר טלפון להזמנה זו")
    
    with col3:
        if st.button("🔙 חזור לרשימה", key=f"back_{order['id']}"):
            st.session_state.selected_order = None
            st.rerun()
    
    st.markdown("---")

def main():
    st.title("🐓 מערכת ניהול הזמנות")
    st.markdown("---")
    
    # ניקוי אוטומטי של הזמנות ישנות
    if 'cleanup_done' not in st.session_state:
        active_removed, closed_removed = cleanup_old_orders()
        if active_removed > 0 or closed_removed > 0:
            st.info(f"🔧 ניקוי אוטומטי: {active_removed} הזמנות פעילות ו-{closed_removed} הזמנות סגורות הועברו/נמחקו")
        st.session_state.cleanup_done = True
    
    # ניקוי לקוחות ישנים
    cleanup_old_customers()
    
    # טעינת הזמנות
    orders = load_orders()
    closed_orders = load_closed_orders()
    
    # סיידבר לניווט
    st.sidebar.title("ניווט")
    page = st.sidebar.selectbox(
        "בחר עמוד:",
        ["הזמנות פעילות", "הזמנות סגורות", "הוספת הזמנה", "עריכת הזמנות", "ניתוח נתונים", "ניהול לקוחות", "ניתוח מתקדם"]
    )
    
    # כפתור ניקוי ידני
    st.sidebar.markdown("---")
    if st.sidebar.button("🧹 ניקוי הזמנות ישנות"):
        active_removed, closed_removed = cleanup_old_orders()
        if active_removed > 0 or closed_removed > 0:
            st.sidebar.success(f"נוקו {active_removed} הזמנות פעילות ו-{closed_removed} הזמנות סגורות")
        else:
            st.sidebar.info("אין הזמנות ישנות לניקוי")
        st.rerun()
    
    # מידע על מונה ההזמנות
    next_order_id = get_next_order_id()
    st.sidebar.markdown("---")
    st.sidebar.info(f"מספר הזמנה הבא: #{next_order_id}")
    st.sidebar.info(f"הזמנות פעילות: {len(orders)}")
    st.sidebar.info(f"הזמנות סגורות: {len(closed_orders)}")
    
    if page == "הזמנות פעילות":
        show_active_orders_page(orders)
    elif page == "הזמנות סגורות":
        show_closed_orders_page(closed_orders)
    elif page == "הוספת הזמנה":
        show_add_order_page(orders)
    elif page == "עריכת הזמנות":
        show_edit_orders_page(orders)
    elif page == "ניתוח נתונים":
        show_analytics_page(orders, closed_orders)
    elif page == "ניהול לקוחות":
        show_customers_page()
    elif page == "ניתוח מתקדם":
        show_enhanced_analytics_page(orders, closed_orders)

def show_active_orders_page(orders):
    """מציג את דף ההזמנות הפעילות"""
    st.header("📋 הזמנות פעילות")
    st.info(f"הזמנות לא סופקות נשמרות עד {ACTIVE_ORDER_RETENTION_DAYS} ימי עסקים")
    st.markdown("""
    **הקטגוריות שלנו:**
    - 🍗 עופות - עוף טרי ואיכותי, הודו
    - 🥩 בשר - בשר בקר, כבש, בשר איכותי על האש
    - 🐟 דגים - סלמון, טונה ועוד
    - 🥚 אחר - מוצרים נוספים
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
    
    st.markdown("---")
    
    # כפתור רענון
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 רענן נתונים"):
            st.rerun()
    
    # בדיקה אם נבחרה הזמנה לצפייה
    if 'selected_order' in st.session_state and st.session_state.selected_order:
        selected_order = st.session_state.selected_order
        show_order_details(selected_order)
        return
    
    if not orders:
        st.info("אין הזמנות עדיין. הוסף הזמנה חדשה!")
        return
    
    # המרה ל-DataFrame
    df = pd.DataFrame(orders)
    
    # הוספת קטגוריה ברירת מחדל להזמנות ישנות
    if 'category' not in df.columns:
        df['category'] = 'עופות'  # ברירת מחדל להזמנות ישנות
    
    # הוספת עמודות חסרות להזמנות לקוחות
    if 'phone' not in df.columns:
        df['phone'] = ''
    if 'address' not in df.columns:
        df['address'] = '{}'
    if 'delivery_notes' not in df.columns:
        df['delivery_notes'] = ''
    if 'items' not in df.columns:
        df['items'] = '{}'
    
    # אפשרויות סינון
    st.subheader("🔍 סינון הזמנות")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # סינון לפי קטגוריה
        all_categories = ["כל הקטגוריות"] + list(PRODUCT_CATEGORIES.keys())
        selected_category = st.selectbox("סינון לפי קטגוריה:", all_categories)
    
    with col2:
        # סינון לפי מוצר
        if selected_category != "כל הקטגוריות":
            category_products = ["כל המוצרים"] + PRODUCT_CATEGORIES[selected_category]
            selected_product = st.selectbox("סינון לפי מוצר:", category_products)
        else:
            if 'product' in df.columns:
                all_products = ["כל המוצרים"] + list(df['product'].dropna().unique())
            else:
                all_products = ["כל המוצרים"]
            selected_product = st.selectbox("סינון לפי מוצר:", all_products)
    
    with col3:
        # סינון לפי סטטוס
        all_statuses = ["כל הסטטוסים", "pending", "processing", "completed", "cancelled"]
        status_labels = {
            "כל הסטטוסים": "כל הסטטוסים",
            "pending": "ממתין",
            "processing": "בטיפול", 
            "completed": "הושלם",
            "cancelled": "בוטל"
        }
        selected_status = st.selectbox("סינון לפי סטטוס:", all_statuses, format_func=lambda x: status_labels[x])
    
    with col4:
        # חיפוש לפי שם לקוח
        search_customer = st.text_input("חיפוש לפי שם לקוח:", "")
    
    # החלת הסינונים
    filtered_df = df.copy()
    
    if selected_category != "כל הקטגוריות":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    if selected_product != "כל המוצרים":
        filtered_df = filtered_df[filtered_df['product'] == selected_product]
    
    if selected_status != "כל הסטטוסים":
        filtered_df = filtered_df[filtered_df['status'] == selected_status]
    
    if search_customer:
        filtered_df = filtered_df[filtered_df['customer_name'].str.contains(search_customer, case=False, na=False)]
    
    # הצגת הנתונים המסוננים
    st.subheader(f"📊 תוצאות ({len(filtered_df)} הזמנות)")
    
    if len(filtered_df) > 0:
        # יצירת עמודות מותאמות לסוגי הזמנות שונים
        display_columns = ["id", "customer_name", "category", "product", "quantity", "price", "status", "created_at"]
        
        # הוספת עמודות נוספות אם קיימות
        if 'phone' in filtered_df.columns:
            display_columns.append("phone")
        if 'address' in filtered_df.columns:
            display_columns.append("address")
        
        # הצגת הטבלה עם כפתורים ללחיצה על שם הלקוח
        for idx, row in filtered_df.iterrows():
            order = row.to_dict()
            
            # יצירת כרטיס הזמנה
            with st.container():
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 2, 1, 1, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**#{order['id']}**")
                
                with col2:
                    # כפתור ללחיצה על שם הלקוח
                    unique_key = f"customer_{order['id']}_{idx}"
                    if st.button(f"👤 {order['customer_name']}", key=unique_key):
                        st.session_state.selected_order = order
                        st.rerun()
                
                with col3:
                    # הצגת מוצר או פריטים
                    if ('items' in order and 
                        order['items'] and 
                        order['items'] != {} and 
                        isinstance(order['items'], (dict, list))):
                        items_count = len(order['items'])
                        st.write(f"📦 {items_count} פריטים")
                    else:
                        product = order.get('product', 'מוצר לא ידוע')
                        st.write(f"📦 {product}")
                
                with col4:
                    # הצגת סטטוס
                    status_hebrew = get_status_hebrew(order['status'])
                    status_colors = {
                        'pending': '🟡',
                        'processing': '🔵', 
                        'completed': '🟢',
                        'cancelled': '🔴'
                    }
                    st.write(f"{status_colors.get(order['status'], '⚪')} {status_hebrew}")
                
                with col5:
                    # הצגת תאריך ושעה
                    created_date = order.get('created_at', '')
                    if created_date:
                        # הצגת רק התאריך (ללא השעה) בפורמט קצר
                        try:
                            date_obj = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S')
                            short_date = date_obj.strftime('%d/%m/%Y')
                            st.write(f"📅 {short_date}")
                        except:
                            st.write(f"📅 {created_date[:10]}")
                    else:
                        st.write("📅 -")
                
                with col6:
                    # כפתור הדפסה מהירה
                    if st.button("🖨️", key=f"quick_print_{order['id']}_{idx}", help="הדפס הזמנה"):
                        print_order(order)
                
                with col7:
                    # כפתור ווטסאפ מהיר
                    if st.button("📧", key=f"quick_whatsapp_{order['id']}_{idx}", help="שלח לווטסאפ"):
                        if 'phone' in order and order['phone']:
                            phone = order['phone'].replace('-', '').replace(' ', '')
                            if phone.startswith('0'):
                                phone = '972' + phone[1:]
                            
                            # יצירת הודעה קצרה
                            message = f"שלום! הזמנה #{order['id']} שלך מוכנה.\n\n"
                            message += f"שם: {order['customer_name']}\n"
                            
                            # הוספת פריטי ההזמנה
                            if ('items' in order and 
                                order['items'] and 
                                isinstance(order['items'], dict)):
                                for item, quantity in order['items'].items():
                                    message += f"• {item}: {format_quantity_with_unit(quantity, item)}\n"
                            else:
                                product = order.get('product', 'מוצר לא ידוע')
                                quantity = order.get('quantity', 0)
                                message += f"• {product}: {format_quantity_with_unit(quantity, product)}\n"
                            
                            message += f"\nסטטוס: {get_status_hebrew(order['status'])}\n"
                            message += "תודה! 🐓"
                            
                            # קידוד ההודעה ל-URL
                            import urllib.parse
                            encoded_message = urllib.parse.quote(message)
                            whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
                            
                            st.markdown(f"[💬 פתח ווטסאפ]({whatsapp_url})")
                        else:
                            st.warning("אין טלפון")
                
                with col8:
                    # כפתור סגירת הזמנה
                    if st.button("✅", key=f"close_order_{order['id']}_{idx}", help="סגור הזמנה"):
                        move_order_to_closed(order)
                        orders[:] = [o for o in orders if o['id'] != order['id']]
                        save_orders(orders)
                        st.success(f"הזמנה #{order['id']} נסגרה והועברה להזמנות סגורות")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.warning("לא נמצאו הזמנות לפי הסינונים שנבחרו")
    
    # סטטיסטיקות מהירות
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("סה״כ הזמנות", len(filtered_df))
    with col2:
        # חישוב סה"כ ערך - התאמה לסוגי הזמנות שונים
        total_value = 0
        for _, row in filtered_df.iterrows():
            if 'total_amount' in row and pd.notna(row['total_amount']):
                total_value += row['total_amount']
            elif 'price' in row and 'quantity' in row and pd.notna(row['price']) and pd.notna(row['quantity']):
                total_value += row['price'] * row['quantity']
        st.metric("ערך כולל (מוסתר)", "מוסתר בשלב זה")
    with col3:
        pending_orders = len([o for o in filtered_df.to_dict('records') if o['status'] == 'pending'])
        st.metric("הזמנות ממתינות", pending_orders)
    with col4:
        completed_orders = len([o for o in filtered_df.to_dict('records') if o['status'] == 'completed'])
        st.metric("הזמנות הושלמו", completed_orders)

def show_closed_orders_page(closed_orders):
    """מציג את דף ההזמנות הסגורות"""
    st.header("📋 הזמנות סגורות")
    st.info(f"הזמנות סגורות נשמרות עד {CLOSED_ORDER_RETENTION_DAYS} ימי עסקים")
    
    if not closed_orders:
        st.info("אין הזמנות סגורות")
        return
    
    # המרה ל-DataFrame
    df = pd.DataFrame(closed_orders)
    
    # הוספת עמודות חסרות
    if 'phone' not in df.columns:
        df['phone'] = ''
    if 'address' not in df.columns:
        df['address'] = '{}'
    if 'delivery_notes' not in df.columns:
        df['delivery_notes'] = ''
    if 'items' not in df.columns:
        df['items'] = '{}'
    if 'closed_at' not in df.columns:
        df['closed_at'] = df['created_at']
    
    # אפשרויות סינון
    st.subheader("🔍 סינון הזמנות סגורות")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # סינון לפי סטטוס
        all_statuses = ["כל הסטטוסים", "pending", "processing", "completed", "cancelled"]
        status_labels = {
            "כל הסטטוסים": "כל הסטטוסים",
            "pending": "ממתין",
            "processing": "בטיפול", 
            "completed": "הושלם",
            "cancelled": "בוטל"
        }
        selected_status = st.selectbox("סינון לפי סטטוס:", all_statuses, format_func=lambda x: status_labels[x], key="closed_status")
    
    with col2:
        # חיפוש לפי שם לקוח
        search_customer = st.text_input("חיפוש לפי שם לקוח:", key="closed_customer_search")
    
    with col3:
        # סינון לפי תאריך סגירה
        date_filter = st.selectbox("סינון לפי תאריך:", ["כל התאריכים", "היום", "אתמול", "השבוע", "החודש"], key="closed_date_filter")
    
    # החלת הסינונים
    filtered_df = df.copy()
    
    if selected_status != "כל הסטטוסים":
        filtered_df = filtered_df[filtered_df['status'] == selected_status]
    
    if search_customer:
        filtered_df = filtered_df[filtered_df['customer_name'].str.contains(search_customer, case=False, na=False)]
    
    # סינון לפי תאריך
    if date_filter != "כל התאריכים":
        today = datetime.now()
        if date_filter == "היום":
            filtered_df = filtered_df[pd.to_datetime(filtered_df['closed_at']).dt.date == today.date()]
        elif date_filter == "אתמול":
            yesterday = today - timedelta(days=1)
            filtered_df = filtered_df[pd.to_datetime(filtered_df['closed_at']).dt.date == yesterday.date()]
        elif date_filter == "השבוע":
            week_ago = today - timedelta(days=7)
            filtered_df = filtered_df[pd.to_datetime(filtered_df['closed_at']) >= week_ago]
        elif date_filter == "החודש":
            month_ago = today - timedelta(days=30)
            filtered_df = filtered_df[pd.to_datetime(filtered_df['closed_at']) >= month_ago]
    
    # הצגת הנתונים המסוננים
    st.subheader(f"📊 תוצאות ({len(filtered_df)} הזמנות סגורות)")
    
    if len(filtered_df) > 0:
        # הצגת הטבלה עם כפתורים ללחיצה על שם הלקוח
        for idx, row in filtered_df.iterrows():
            order = row.to_dict()
            # יצירת כרטיס הזמנה
            with st.container():
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 2, 1, 1, 1, 1, 1, 1])
                with col1:
                    st.write(f"**#{order['id']}**")
                with col2:
                    # כפתור ללחיצה על שם הלקוח
                    unique_key = f"closed_customer_{order['id']}_{idx}"
                    if st.button(f"👤 {order['customer_name']}", key=unique_key):
                        st.session_state.selected_closed_order = order
                        st.rerun()
                with col3:
                    # הצגת מוצר או פריטים
                    if ('items' in order and 
                        order['items'] and 
                        order['items'] != {} and 
                        isinstance(order['items'], (dict, list))):
                        items_count = len(order['items'])
                        st.write(f"📦 {items_count} פריטים")
                    else:
                        product = order.get('product', 'מוצר לא ידוע')
                        st.write(f"📦 {product}")
                
                with col4:
                    # הצגת סטטוס
                    status_hebrew = get_status_hebrew(order['status'])
                    status_colors = {
                        'pending': '🟡',
                        'processing': '🔵', 
                        'completed': '🟢',
                        'cancelled': '🔴'
                    }
                    st.write(f"{status_colors.get(order['status'], '⚪')} {status_hebrew}")
                
                with col5:
                    # תאריך יצירה
                    created_date = order.get('created_at', '')
                    if created_date:
                        try:
                            date_obj = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S')
                            short_date = date_obj.strftime('%d/%m/%Y')
                            st.write(f"📅 {short_date}")
                        except:
                            st.write(f"📅 {created_date[:10]}")
                    else:
                        st.write("📅 -")
                
                with col6:
                    # תאריך סגירה
                    closed_date = order.get('closed_at', order['created_at'])
                    if closed_date:
                        try:
                            date_obj = datetime.strptime(closed_date, '%Y-%m-%d %H:%M:%S')
                            short_date = date_obj.strftime('%d/%m/%Y')
                            st.write(f"🔒 {short_date}")
                        except:
                            st.write(f"🔒 {closed_date[:10]}")
                    else:
                        st.write("🔒 -")
                
                with col7:
                    # כפתור הדפסה מהירה
                    if st.button("🖨️", key=f"closed_quick_print_{order['id']}", help="הדפס הזמנה"):
                        print_order(order)
                
                with col8:
                    # כפתור ווטסאפ מהיר
                    if st.button("📧", key=f"closed_quick_whatsapp_{order['id']}", help="שלח לווטסאפ"):
                        if 'phone' in order and order['phone']:
                            phone = order['phone'].replace('-', '').replace(' ', '')
                            if phone.startswith('0'):
                                phone = '972' + phone[1:]
                            
                            # יצירת הודעה קצרה
                            message = f"שלום! הזמנה #{order['id']} שלך הושלמה.\n\n"
                            message += f"שם: {order['customer_name']}\n"
                            
                            # הוספת פריטי ההזמנה
                            if ('items' in order and 
                                order['items'] and 
                                isinstance(order['items'], dict)):
                                for item, quantity in order['items'].items():
                                    message += f"• {item}: {format_quantity_with_unit(quantity, item)}\n"
                            else:
                                product = order.get('product', 'מוצר לא ידוע')
                                quantity = order.get('quantity', 0)
                                message += f"• {product}: {format_quantity_with_unit(quantity, product)}\n"
                            
                            message += f"\nסטטוס: {get_status_hebrew(order['status'])}\n"
                            message += "תודה! 🐓"
                            
                            # קידוד ההודעה ל-URL
                            import urllib.parse
                            encoded_message = urllib.parse.quote(message)
                            whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
                            
                            st.markdown(f"[💬 פתח ווטסאפ]({whatsapp_url})")
                        else:
                            st.warning("אין טלפון")
                
                st.markdown("---")
    else:
        st.warning("לא נמצאו הזמנות סגורות לפי הסינונים שנבחרו")
    
    # סטטיסטיקות מהירות
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("סה״כ הזמנות סגורות", len(filtered_df))
    with col2:
        # חישוב סה"כ ערך
        total_value = 0
        for _, row in filtered_df.iterrows():
            if 'total_amount' in row and pd.notna(row['total_amount']):
                total_value += row['total_amount']
            elif 'price' in row and 'quantity' in row and pd.notna(row['price']) and pd.notna(row['quantity']):
                total_value += row['price'] * row['quantity']
        st.metric("ערך כולל (מוסתר)", "מוסתר בשלב זה")
    with col3:
        completed_orders = len([o for o in filtered_df.to_dict('records') if o['status'] == 'completed'])
        st.metric("הזמנות שהושלמו", completed_orders)
    with col4:
        cancelled_orders = len([o for o in filtered_df.to_dict('records') if o['status'] == 'cancelled'])
        st.metric("הזמנות שבוטלו", cancelled_orders)
    
    # בדיקה אם נבחרה הזמנה סגורה לצפייה
    if 'selected_closed_order' in st.session_state and st.session_state.selected_closed_order:
        selected_order = st.session_state.selected_closed_order
        show_closed_order_details(selected_order)

def show_closed_order_details(order):
    """מציג פרטי הזמנה סגורה מפורטים"""
    st.header(f"📋 פרטי הזמנה סגורה #{order['id']}")
    
    # פרטי לקוח
    st.subheader("👤 פרטי לקוח")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**שם:** {order['customer_name']}")
        if 'phone' in order and order['phone']:
            st.write(f"**טלפון:** {order['phone']}")
    
    with col2:
        if 'address' in order and order['address']:
            address = order['address']
            if isinstance(address, dict):
                st.write(f"**כתובת:** {address.get('street_name', '')} {address.get('street_number', '')}")
                st.write(f"**עיר:** {address.get('city', '')}")
            else:
                st.write(f"**כתובת:** {address}")
    
    if 'delivery_notes' in order and order['delivery_notes']:
        st.write(f"**הערות לשליח:** {order['delivery_notes']}")
    if 'butcher_notes' in order and order['butcher_notes']:
        st.write(f"**הערות לקצב:** {order['butcher_notes']}")
    
    # פרטי תאריך ושעה
    st.subheader("📅 פרטי תאריך ושעה")
    col1, col2 = st.columns(2)
    with col1:
        created_date = order.get('created_at', '')
        if created_date:
            try:
                date_obj = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
                st.write(f"**תאריך יצירה:** {formatted_date}")
            except:
                st.write(f"**תאריך יצירה:** {created_date}")
        else:
            st.write("**תאריך יצירה:** לא זמין")
    
    with col2:
        closed_date = order.get('closed_at', order['created_at'])
        if closed_date:
            try:
                date_obj = datetime.strptime(closed_date, '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
                st.write(f"**תאריך סגירה:** {formatted_date}")
            except:
                st.write(f"**תאריך סגירה:** {closed_date}")
        else:
            st.write("**תאריך סגירה:** לא זמין")
    
    # פרטי הזמנה
    st.subheader("📦 פריטי ההזמנה")
    
    if ('items' in order and 
        order['items'] and 
        isinstance(order['items'], (dict, list))):
        # הזמנת לקוח עם פריטים מרובים
        items_data = []
        for item, quantity in order['items'].items():
            price = PRODUCT_PRICES.get(item, 0)
            total = price * quantity
            items_data.append({
                'מוצר': item,
                'כמות': format_quantity_with_unit(quantity, item),
                # מחירים מוסתרים בשלב זה
            })
        
        df_items = pd.DataFrame(items_data)
        st.dataframe(df_items, use_container_width=True)
    else:
        # הזמנה רגילה עם מוצר אחד
        product = order.get('product', 'מוצר לא ידוע')
        quantity = order.get('quantity', 0)
        price = order.get('price', 0)
        total = price * quantity
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**מוצר:** {product}")
        with col2:
            st.write(f"**כמות:** {format_quantity_with_unit(quantity, product)}")
        # מחירים מוסתרים בשלב זה
    
    # סיכום
    st.subheader("💰 סיכום")
    delivery_cost = 20.0
    col1, col2 = st.columns(2)
    with col1:
        st.metric("עלות משלוח", "מוסתר בשלב זה")
    with col2:
        st.metric("סטטוס", get_status_hebrew(order['status']))
    
    # כפתורי פעולה
    st.subheader("🔧 פעולות")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🖨️ הדפס הזמנה", key=f"closed_print_{order['id']}"):
            print_order(order)
    
    with col2:
        if st.button("📧 שלח לווטסאפ", key=f"closed_whatsapp_{order['id']}"):
            if 'phone' in order and order['phone']:
                phone = order['phone'].replace('-', '').replace(' ', '')
                if phone.startswith('0'):
                    phone = '972' + phone[1:]
                
                # יצירת הודעה עם פרטי ההזמנה
                message = f"שלום! הזמנה #{order['id']} שלך הושלמה.\n\n"
                message += f"שם: {order['customer_name']}\n"
                
                # הוספת פרטי כתובת
                if 'address' in order and order['address']:
                    address = order['address']
                    if isinstance(address, dict):
                        address_text = f"{address.get('street_name', '')} {address.get('street_number', '')}, {address.get('city', '')}"
                        message += f"כתובת: {address_text}\n"
                
                # הוספת הערות
                if 'delivery_notes' in order and order['delivery_notes']:
                    message += f"הערות לשליח: {order['delivery_notes']}\n"
                if 'butcher_notes' in order and order['butcher_notes']:
                    message += f"הערות לקצב: {order['butcher_notes']}\n"
                
                # הוספת פריטי ההזמנה
                message += "\nפריטי ההזמנה:\n"
                if ('items' in order and 
                    order['items'] and 
                    isinstance(order['items'], dict)):
                    # הזמנת לקוח עם פריטים מרובים
                    for item, quantity in order['items'].items():
                        message += f"• {item}: {format_quantity_with_unit(quantity, item)}\n"
                else:
                    # הזמנה רגילה עם מוצר אחד
                    product = order.get('product', 'מוצר לא ידוע')
                    quantity = order.get('quantity', 0)
                    message += f"• {product}: {format_quantity_with_unit(quantity, product)}\n"
                
                message += f"\nסטטוס: {get_status_hebrew(order['status'])}\n"
                message += f"תאריך הזמנה: {order.get('created_at', '')}\n"
                message += f"תאריך סגירה: {order.get('closed_at', '')}\n\n"
                message += "תודה על ההזמנה! 🐓"
                
                # קידוד ההודעה ל-URL
                import urllib.parse
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
                
                st.success("📧 הודעה מוכנה לווטסאפ!")
                st.markdown(f"[💬 פתח ווטסאפ עם הודעה מוכנה]({whatsapp_url})")
                st.info("💡 טיפ: הקישור יפתח את ווטסאפ עם הודעה מוכנה שתוכל לשלוח")
            else:
                st.warning("אין מספר טלפון להזמנה זו")
    
    with col3:
        if st.button("🔙 חזור לרשימה", key=f"closed_back_{order['id']}"):
            st.session_state.selected_closed_order = None
            st.rerun()
    
    st.markdown("---")

def show_add_order_page(orders):
    """מציג את דף הוספת הזמנה חדשה"""
    st.header("➕ הוספת הזמנה חדשה")
    
    with st.form("add_order_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("שם הלקוח", key="customer_name")
            
            # בחירת קטגוריה
            category = st.selectbox("קטגוריה:", list(PRODUCT_CATEGORIES.keys()), key="category_select")
            
            # בחירת מוצר עם אפשרות למוצר מותאם אישית
            product_choice = st.radio(
                "בחר מוצר:",
                ["מוצר מהרשימה", "מוצר מותאם אישית"],
                horizontal=True
            )
            
            if product_choice == "מוצר מהרשימה":
                product = st.selectbox("שם המוצר", options=PRODUCT_CATEGORIES[category], key="product_select")
                
                # בדיקה אם המוצר הוא שווארמה עם אפשרויות חיתוך
                if product in SHAWARMA_CUTTING_OPTIONS:
                    cutting_option = st.selectbox(
                        "אפשרות חיתוך:",
                        options=SHAWARMA_CUTTING_OPTIONS[product]["options"],
                        index=SHAWARMA_CUTTING_OPTIONS[product]["options"].index(SHAWARMA_CUTTING_OPTIONS[product]["default"])
                    )
                    # הוספת אפשרות החיתוך לשם המוצר
                    product = f"{product} - {cutting_option}"
                # בדיקה אם המוצר הוא מוצר נוסף עם אפשרויות חיתוך
                elif product in ADDITIONAL_CUTTING_OPTIONS:
                    cutting_option = st.selectbox(
                        "אפשרות חיתוך:",
                        options=ADDITIONAL_CUTTING_OPTIONS[product]["options"],
                        index=ADDITIONAL_CUTTING_OPTIONS[product]["options"].index(ADDITIONAL_CUTTING_OPTIONS[product]["default"])
                    )
                    # הוספת אפשרות החיתוך לשם המוצר
                    product = f"{product} - {cutting_option}"
            else:
                product = st.text_input("הקלד שם המוצר", key="product_custom")
        
        with col2:
            # קביעת יחידה לפי המוצר שנבחר
            unit = get_product_unit(product) if 'product' in locals() else "יחידות"
            quantity = st.number_input(f"כמות ({unit})", min_value=1, value=1, key="quantity")
            price = st.number_input("מחיר ליחידה (מושהה)", min_value=0.0, value=0.0, key="price", disabled=True)
        
        status = st.selectbox(
            "סטטוס",
            ["pending", "processing", "completed", "cancelled"],
            format_func=lambda x: {
                "pending": "ממתין",
                "processing": "בטיפול",
                "completed": "הושלם",
                "cancelled": "בוטל"
            }[x]
        )
        
        submitted = st.form_submit_button("הוסף הזמנה")
        
        if submitted:
            if customer_name and product and price > 0:
                new_order = {
                    'id': get_next_order_id(),
                    'customer_name': customer_name,
                    'category': category,
                    'product': product,
                    'quantity': quantity,
                    'price': price,
                    'status': status,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                save_orders(orders)
                st.success("ההזמנה נוספה בהצלחה!")
                
                # הדפסה אוטומטית של ההזמנה
                st.info("🖨️ מדפיס הזמנה...")
                print_order(new_order)
                
                st.rerun()
            else:
                st.error("אנא מלא את כל השדות הנדרשים")

def show_edit_orders_page(orders):
    """מציג את דף עריכת הזמנות"""
    st.header("✏️ עריכת הזמנות")
    
    if not orders:
        st.info("אין הזמנות לעריכה")
        return
    
    # בחירת הזמנה לעריכה
    order_options = {}
    for order in orders:
        # יצירת תיאור הזמנה מותאם לסוג ההזמנה
        if ('items' in order and 
            order['items'] and 
            isinstance(order['items'], (dict, list))):
            # הזמנת לקוח עם פריטים מרובים
            items_desc = ", ".join([f"{item} x{qty}" for item, qty in order['items'].items()])
            order_options[f"{order['id']} - {order['customer_name']} - {items_desc}"] = order
        else:
            # הזמנה רגילה עם מוצר אחד
            product = order.get('product', 'מוצר לא ידוע')
            order_options[f"{order['id']} - {order['customer_name']} - {product}"] = order
    
    selected_order_key = st.selectbox("בחר הזמנה לעריכה:", list(order_options.keys()))
    
    if selected_order_key:
        selected_order = order_options[selected_order_key]
        
        # בדיקה אם זו הזמנת לקוח או הזמנה רגילה
        is_customer_order = ('items' in selected_order and 
                           selected_order['items'] and 
                           isinstance(selected_order['items'], (dict, list)))
        
        if is_customer_order:
            # עריכת הזמנת לקוח
            with st.form("edit_customer_order_form"):
                st.subheader("📋 פרטי לקוח")
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_name = st.text_input("שם הלקוח", value=selected_order['customer_name'])
                    phone = st.text_input("מספר טלפון", value=selected_order.get('phone', ''))
                
                with col2:
                    # כתובת
                    address = selected_order.get('address', {})
                    if isinstance(address, str):
                        address = {}
                    
                    street_name = st.text_input("רחוב", value=address.get('street_name', ''))
                    street_number = st.text_input("מספר בית", value=address.get('street_number', ''))
                    city = st.text_input("עיר", value=address.get('city', ''))
                
                delivery_notes = st.text_area("הערות לשליח", value=selected_order.get('delivery_notes', ''))
                butcher_notes = st.text_area("הערות לקצב", value=selected_order.get('butcher_notes', ''))
                
                st.subheader("📦 פריטי ההזמנה")
                items = selected_order.get('items', {})
                
                # עריכת פריטים
                updated_items = {}
                for item, quantity in items.items():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{item}**")
                    with col2:
                        unit = get_product_unit(item)
                        new_qty = st.number_input(f"כמות ({unit})", min_value=0, value=quantity, key=f"qty_{item}")
                    with col3:
                        st.write("")  # רווח במקום כפתור
                    
                    if new_qty > 0:
                        updated_items[item] = new_qty
                
                st.subheader("📊 סיכום")
                total_amount = sum(PRODUCT_PRICES.get(item, 0) * qty for item, qty in updated_items.items())
                delivery_cost = 20.0 # קבע עלות משלוח קבועה
                total_amount += delivery_cost
                st.info(f"🚚 עלות משלוח: מוסתר בשלב זה")
                
                # סה"כ לתשלום מוסתר בשלב זה
                
                status = st.selectbox(
                    "סטטוס",
                    ["pending", "processing", "completed", "cancelled"],
                    index=["pending", "processing", "completed", "cancelled"].index(selected_order['status']),
                    format_func=lambda x: {
                        "pending": "ממתין",
                        "processing": "בטיפול",
                        "completed": "הושלם",
                        "cancelled": "בוטל"
                    }[x]
                )
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("עדכן הזמנה"):
                        selected_order['customer_name'] = customer_name
                        selected_order['phone'] = phone
                        selected_order['address'] = {
                            'street_name': street_name,
                            'street_number': street_number,
                            'city': city
                        }
                        selected_order['delivery_notes'] = delivery_notes
                        selected_order['butcher_notes'] = butcher_notes
                        selected_order['items'] = updated_items
                        selected_order['total_amount'] = total_amount
                        selected_order['status'] = status
                        
                        update_order(selected_order['id'], selected_order)
                        st.success("ההזמנה עודכנה בהצלחה!")
                        st.rerun()
                
                with col2:
                    if st.form_submit_button("סגור הזמנה", type="secondary"):
                        move_order_to_closed(selected_order)
                        orders[:] = [o for o in orders if o['id'] != selected_order['id']]
                        save_orders(orders)
                        st.success("ההזמנה נסגרה והועברה להזמנות סגורות!")
                        st.rerun()
                
                with col3:
                    if st.form_submit_button("מחק הזמנה", type="secondary"):
                        delete_order(selected_order['id'])
                        orders[:] = [o for o in orders if o['id'] != selected_order['id']]
                        save_orders(orders)
                        st.success("ההזמנה נמחקה בהצלחה!")
                        st.rerun()
        
        else:
            # עריכת הזמנה רגילה
            with st.form("edit_order_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_name = st.text_input("שם הלקוח", value=selected_order['customer_name'])
                    
                    # בחירת קטגוריה
                    current_category = selected_order.get('category', 'עופות')  # ברירת מחדל לעופות
                    category = st.selectbox("קטגוריה:", list(PRODUCT_CATEGORIES.keys()), 
                                          index=list(PRODUCT_CATEGORIES.keys()).index(current_category) 
                                          if current_category in PRODUCT_CATEGORIES else 0,
                                          key="edit_category_select")
                    
                    # בחירת מוצר עם אפשרות למוצר מותאם אישית
                    product_choice = st.radio(
                        "בחר מוצר:",
                        ["מוצר מהרשימה", "מוצר מותאם אישית"],
                        horizontal=True,
                        key="edit_product_choice"
                    )
                    
                    if product_choice == "מוצר מהרשימה":
                        # בדיקה אם המוצר הנוכחי נמצא בקטגוריה הנוכחית
                        current_product = selected_order['product']
                        if current_product in PRODUCT_CATEGORIES[category]:
                            product = st.selectbox("שם המוצר", options=PRODUCT_CATEGORIES[category], 
                                                 index=PRODUCT_CATEGORIES[category].index(current_product), 
                                                 key="edit_product_select")
                        else:
                            product = st.selectbox("שם המוצר", options=PRODUCT_CATEGORIES[category], key="edit_product_select")
                    else:
                        product = st.text_input("הקלד שם המוצר", value=selected_order['product'], key="edit_product_custom")
                
                with col2:
                    unit = get_product_unit(selected_order['product'])
                    quantity = st.number_input(f"כמות ({unit})", min_value=1, value=selected_order['quantity'])
                    price = st.number_input("מחיר ליחידה (מושהה)", min_value=0.0, value=selected_order['price'], disabled=True)
                
                status = st.selectbox(
                    "סטטוס",
                    ["pending", "processing", "completed", "cancelled"],
                    index=["pending", "processing", "completed", "cancelled"].index(selected_order['status']),
                    format_func=lambda x: {
                        "pending": "ממתין",
                        "processing": "בטיפול",
                        "completed": "הושלם",
                        "cancelled": "בוטל"
                    }[x]
                )
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("עדכן הזמנה"):
                        selected_order['customer_name'] = customer_name
                        selected_order['category'] = category
                        selected_order['product'] = product
                        selected_order['quantity'] = quantity
                        selected_order['price'] = price
                        selected_order['status'] = status
                        
                        update_order(selected_order['id'], selected_order)
                        st.success("ההזמנה עודכנה בהצלחה!")
                        st.rerun()
                
                with col2:
                    if st.form_submit_button("סגור הזמנה", type="secondary"):
                        move_order_to_closed(selected_order)
                        orders[:] = [o for o in orders if o['id'] != selected_order['id']]
                        save_orders(orders)
                        st.success("ההזמנה נסגרה והועברה להזמנות סגורות!")
                        st.rerun()
                
                with col3:
                    if st.form_submit_button("מחק הזמנה", type="secondary"):
                        delete_order(selected_order['id'])
                        orders[:] = [o for o in orders if o['id'] != selected_order['id']]
                        save_orders(orders)
                        st.success("ההזמנה נמחקה בהצלחה!")
                        st.rerun()

def show_analytics_page(orders, closed_orders):
    import pandas as pd
    import streamlit as st
    import matplotlib.pyplot as plt

    st.header("📊 ניתוח סטטיסטי של הזמנות")

    # איסוף כל ההזמנות (פעילות וסגורות)
    all_orders = (orders or []) + (closed_orders or [])
    rows = []
    for order in all_orders:
        customer = order.get('customer_name', '')
        phone = order.get('phone', '')
        items = order.get('items', {})
        if not isinstance(items, dict):
            continue  # דלג על הזמנות לא תקינות
        for product, quantity in items.items():
            # מצא קטגוריה
            category = next((cat for cat, plist in PRODUCT_CATEGORIES.items() if product in plist), 'לא ידוע')
            rows.append({
                'customer': customer,
                'phone': phone,
                'product': product,
                'category': category,
                'quantity': quantity,
                'date': order.get('created_at', '')
            })
    if not rows:
        st.info("אין נתונים לניתוח.")
        return
    df = pd.DataFrame(rows)

    # סיכום לפי קטגוריה
    st.subheader("סיכום כמויות לפי קטגוריה")
    cat_sum = df.groupby('category')['quantity'].sum().reset_index().sort_values('quantity', ascending=False)
    # הוספת עמודת יחידות
    cat_sum['יחידות'] = cat_sum['category'].apply(lambda x: "ק\"ג" if x in ["עופות", "בשר"] else "יחידות")
    st.dataframe(cat_sum)
    st.bar_chart(cat_sum.set_index('category'))

    # סיכום לפי פריט
    st.subheader("סיכום כמויות לפי פריט")
    prod_sum = df.groupby('product')['quantity'].sum().reset_index().sort_values('quantity', ascending=False)
    # הוספת עמודת יחידות
    prod_sum['יחידות'] = prod_sum['product'].apply(lambda x: get_product_unit(x))
    st.dataframe(prod_sum)
    st.bar_chart(prod_sum.set_index('product'))

    # סיכום לפי לקוח
    st.subheader("סיכום כמויות לפי לקוח")
    cust_sum = df.groupby(['customer', 'phone'])['quantity'].sum().reset_index().sort_values('quantity', ascending=False)
    # הוספת עמודת יחידות (ברירת מחדל ליחידות)
    cust_sum['יחידות'] = "יחידות"
    st.dataframe(cust_sum)
    st.bar_chart(cust_sum.set_index('customer'))

    # המרת עמודת תאריך
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    # פילוח לפי חודשים
    st.subheader("פילוח הזמנות לפי חודשים")
    df['month'] = df['date'].dt.to_period('M').astype(str)
    month_sum = df.groupby('month')['quantity'].sum().reset_index().sort_values('month')
    # הוספת עמודת יחידות (ברירת מחדל ליחידות)
    month_sum['יחידות'] = "יחידות"
    st.dataframe(month_sum)
    st.bar_chart(month_sum.set_index('month'))

    # פילוח לפי חגי ישראל
    st.subheader("פילוח הזמנות לפי חגי ישראל")
    # טווחי חגים (דוגמה לשנים 2023-2025, אפשר להרחיב)
    holidays = [
        ("פסח",    [("2023-04-05", "2023-04-13"), ("2024-04-22", "2024-04-30"), ("2025-04-12", "2025-04-20")]),
        ("שבועות",  [("2023-05-25", "2023-05-27"), ("2024-06-11", "2024-06-13"), ("2025-06-01", "2025-06-03")]),
        ("ראש השנה",[("2023-09-15", "2023-09-17"), ("2024-10-02", "2024-10-04"), ("2025-09-22", "2025-09-24")]),
        ("סוכות",   [("2023-09-29", "2023-10-07"), ("2024-10-16", "2024-10-24"), ("2025-10-03", "2025-10-11")]),
        ("חנוכה",  [("2023-12-07", "2023-12-15"), ("2024-12-25", "2025-01-02"), ("2025-12-14", "2025-12-22")]),
        ("פורים",  [("2023-03-06", "2023-03-08"), ("2024-03-24", "2024-03-26"), ("2025-03-14", "2025-03-16")]),
    ]
    def get_holiday_name(date):
        for name, ranges in holidays:
            for start, end in ranges:
                if pd.to_datetime(start) <= date <= pd.to_datetime(end):
                    return name
        return "לא חג"
    df['holiday'] = df['date'].apply(get_holiday_name)
    holiday_sum = df.groupby('holiday')['quantity'].sum().reset_index().sort_values('quantity', ascending=False)
    # הוספת עמודת יחידות (ברירת מחדל ליחידות)
    holiday_sum['יחידות'] = "יחידות"
    st.dataframe(holiday_sum)
    st.bar_chart(holiday_sum.set_index('holiday'))

# הפונקציות לניהול לקוחות מיובאות מ-database.py

def show_customers_page():
    """מציג דף ניהול לקוחות"""
    st.header("👥 ניהול לקוחות")
    
    customers = load_customers()
    
    if not customers:
        st.info("אין לקוחות במערכת עדיין.")
        return
    
    # סטטיסטיקות כלליות
    total_customers = len(customers)
    total_orders = sum(c.get('total_orders', 0) for c in customers)
    total_revenue = sum(c.get('total_spent', 0) for c in customers)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("סה״כ לקוחות", total_customers)
    with col2:
        st.metric("סה״כ הזמנות", total_orders)
    with col3:
        st.metric("סה״כ הכנסות", f"₪{total_revenue:,.0f}")
    
    st.subheader("רשימת לקוחות")
    
    # טבלת לקוחות
    customer_data = []
    for customer in customers:
        customer_data.append({
            'מזהה': customer['id'],
            'שם מלא': customer['full_name'],
            'טלפון': customer['phone'],
            'הזמנות': customer.get('total_orders', 0),
            'סכום כולל': f"₪{customer.get('total_spent', 0):,.0f}",
            'תאריך יצירה': customer.get('created_at', ''),
            'הזמנה אחרונה': customer.get('last_order_date', '')
        })
    
    df = pd.DataFrame(customer_data)
    st.dataframe(df, use_container_width=True)
    
    # אפשרות להורדת נתונים
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 הורד נתוני לקוחות",
        data=csv,
        file_name="customers_data.csv",
        mime="text/csv"
    )

def show_enhanced_analytics_page(orders, closed_orders):
    """מציג דף ניתוח מתקדם עם נתוני לקוחות"""
    st.header("📊 ניתוח מתקדם")
    
    customers = load_customers()
    all_orders = orders + closed_orders
    
    # ניתוח לקוחות
    if customers:
        st.subheader("📈 ניתוח לקוחות")
        
        # לקוחות לפי כמות הזמנות
        customer_orders = {}
        for order in all_orders:
            if 'customer_id' in order:
                customer_id = order['customer_id']
                if customer_id not in customer_orders:
                    customer_orders[customer_id] = 0
                customer_orders[customer_id] += 1
        
        if customer_orders:
            # גרף לקוחות לפי כמות הזמנות
            fig, ax = plt.subplots(figsize=(10, 6))
            customer_names = []
            order_counts = []
            
            for customer_id, count in sorted(customer_orders.items(), key=lambda x: x[1], reverse=True)[:10]:
                customer = next((c for c in customers if c['id'] == customer_id), None)
                if customer:
                    customer_names.append(customer['full_name'])
                    order_counts.append(count)
            
            if customer_names:
                ax.bar(range(len(customer_names)), order_counts)
                ax.set_xlabel('לקוחות')
                ax.set_ylabel('כמות הזמנות')
                ax.set_title('לקוחות לפי כמות הזמנות')
                ax.set_xticks(range(len(customer_names)))
                ax.set_xticklabels(customer_names, rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
    
    # ניתוח מוצרים עם קישור ללקוחות
    st.subheader("🛒 ניתוח מוצרים")
    
    product_stats = {}
    for order in all_orders:
        for product, quantity in order.get('items', {}).items():
            if product not in product_stats:
                product_stats[product] = {
                    'total_quantity': 0,
                    'total_orders': 0,
                    'customers': set()
                }
            product_stats[product]['total_quantity'] += quantity
            product_stats[product]['total_orders'] += 1
            if 'customer_id' in order:
                product_stats[product]['customers'].add(order['customer_id'])
    
    if product_stats:
        # טבלת מוצרים פופולריים
        product_data = []
        for product, stats in sorted(product_stats.items(), key=lambda x: x[1]['total_quantity'], reverse=True):
            product_data.append({
                'מוצר': product,
                'כמות כוללת': f"{stats['total_quantity']} {get_product_unit(product)}",
                'כמות הזמנות': stats['total_orders'],
                'לקוחות ייחודיים': len(stats['customers'])
            })
        
        df_products = pd.DataFrame(product_data)
        st.dataframe(df_products, use_container_width=True)
    
    # ניתוח זמנים
    st.subheader("📅 ניתוח זמנים")
    
    if all_orders:
        # הזמנות לפי חודש
        monthly_orders = {}
        for order in all_orders:
            if 'created_at' in order:
                try:
                    order_date = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
                    month_key = order_date.strftime('%Y-%m')
                    if month_key not in monthly_orders:
                        monthly_orders[month_key] = 0
                    monthly_orders[month_key] += 1
                except:
                    continue
        
        if monthly_orders:
            fig, ax = plt.subplots(figsize=(12, 6))
            months = sorted(monthly_orders.keys())
            counts = [monthly_orders[month] for month in months]
            
            ax.plot(months, counts, marker='o')
            ax.set_xlabel('חודש')
            ax.set_ylabel('כמות הזמנות')
            ax.set_title('הזמנות לפי חודש')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

if __name__ == "__main__":
    main()


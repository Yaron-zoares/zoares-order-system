import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import webbrowser
from io import StringIO
import calendar

# הגדרת כותרת האפליקציה
st.set_page_config(
    page_title="מערכת ניהול הזמנות",
    page_icon="🐓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# נתיבים לקבצי הנתונים
ORDERS_FILE = 'orders.json'
CLOSED_ORDERS_FILE = 'closed_orders.json'
COUNTER_FILE = 'order_counter.json'

# הגדרות שמירה
ACTIVE_ORDER_RETENTION_DAYS = 20  # ימי עסקים להזמנות לא סופקות
CLOSED_ORDER_RETENTION_DAYS = 60  # ימי עסקים להזמנות סגורות

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

def load_order_counter():
    """טוען את מונה ההזמנות"""
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"next_order_id": 1}

def save_order_counter(counter):
    """שומר את מונה ההזמנות"""
    with open(COUNTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(counter, f, ensure_ascii=False, indent=2)

def get_next_order_id():
    """מחזיר את מספר ההזמנה הבא"""
    counter = load_order_counter()
    next_id = counter["next_order_id"]
    counter["next_order_id"] += 1
    save_order_counter(counter)
    return next_id

def load_orders():
    """טוען את ההזמנות הפעילות מקובץ JSON"""
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_closed_orders():
    """טוען את ההזמנות הסגורות מקובץ JSON"""
    if os.path.exists(CLOSED_ORDERS_FILE):
        with open(CLOSED_ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_orders(orders):
    """שומר את ההזמנות הפעילות לקובץ JSON"""
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def save_closed_orders(closed_orders):
    """שומר את ההזמנות הסגורות לקובץ JSON"""
    with open(CLOSED_ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(closed_orders, f, ensure_ascii=False, indent=2)

def move_order_to_closed(order):
    """מעביר הזמנה להזמנות סגורות"""
    closed_orders = load_closed_orders()
    
    # הוספת תאריך סגירה
    order['closed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    closed_orders.append(order)
    save_closed_orders(closed_orders)

def cleanup_old_orders():
    """מנקה הזמנות ישנות לפי מדיניות השמירה"""
    today = datetime.now()
    
    # ניקוי הזמנות פעילות ישנות (לא סופקות)
    orders = load_orders()
    cutoff_date_active = get_business_days_before(today, ACTIVE_ORDER_RETENTION_DAYS)
    
    orders_to_remove = []
    for order in orders:
        order_date = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
        if order_date < cutoff_date_active and order['status'] != 'completed':
            orders_to_remove.append(order)
    
    for order in orders_to_remove:
        orders.remove(order)
        move_order_to_closed(order)
    
    if orders_to_remove:
        save_orders(orders)
    
    # ניקוי הזמנות סגורות ישנות
    closed_orders = load_closed_orders()
    cutoff_date_closed = get_business_days_before(today, CLOSED_ORDER_RETENTION_DAYS)
    
    closed_orders_to_remove = []
    for order in closed_orders:
        closed_date = datetime.strptime(order.get('closed_at', order['created_at']), '%Y-%m-%d %H:%M:%S')
        if closed_date < cutoff_date_closed:
            closed_orders_to_remove.append(order)
    
    for order in closed_orders_to_remove:
        closed_orders.remove(order)
    
    if closed_orders_to_remove:
        save_closed_orders(closed_orders)
    
    return len(orders_to_remove), len(closed_orders_to_remove)

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
                    <td>{quantity}</td>
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
                <td>{quantity}</td>
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
                'כמות': quantity,
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
            st.write(f"**כמות:** {quantity}")
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
                        message += f"• {item}: {quantity}\n"
                else:
                    # הזמנה רגילה עם מוצר אחד
                    product = order.get('product', 'מוצר לא ידוע')
                    quantity = order.get('quantity', 0)
                    message += f"• {product}: {quantity}\n"
                
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
    
    # טעינת הזמנות
    orders = load_orders()
    closed_orders = load_closed_orders()
    
    # סיידבר לניווט
    st.sidebar.title("ניווט")
    page = st.sidebar.selectbox(
        "בחר עמוד:",
        ["הזמנות פעילות", "הזמנות סגורות", "הוספת הזמנה", "עריכת הזמנות", "ניתוח נתונים"]
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
    counter = load_order_counter()
    st.sidebar.markdown("---")
    st.sidebar.info(f"מספר הזמנה הבא: #{counter['next_order_id']}")
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
                                    message += f"• {item}: {quantity}\n"
                            else:
                                product = order.get('product', 'מוצר לא ידוע')
                                quantity = order.get('quantity', 0)
                                message += f"• {product}: {quantity}\n"
                            
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
                                    message += f"• {item}: {quantity}\n"
                            else:
                                product = order.get('product', 'מוצר לא ידוע')
                                quantity = order.get('quantity', 0)
                                message += f"• {product}: {quantity}\n"
                            
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
                'כמות': quantity,
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
            st.write(f"**כמות:** {quantity}")
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
                        message += f"• {item}: {quantity}\n"
                else:
                    # הזמנה רגילה עם מוצר אחד
                    product = order.get('product', 'מוצר לא ידוע')
                    quantity = order.get('quantity', 0)
                    message += f"• {product}: {quantity}\n"
                
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
            quantity = st.number_input("כמות", min_value=1, value=1, key="quantity")
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
                
                orders.append(new_order)
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
                        new_qty = st.number_input(f"כמות", min_value=0, value=quantity, key=f"qty_{item}")
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
                        
                        save_orders(orders)
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
                    quantity = st.number_input("כמות", min_value=1, value=selected_order['quantity'])
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
                        
                        save_orders(orders)
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
                        orders[:] = [o for o in orders if o['id'] != selected_order['id']]
                        save_orders(orders)
                        st.success("ההזמנה נמחקה בהצלחה!")
                        st.rerun()

def show_analytics_page(orders, closed_orders):
    """מציג את דף ניתוח הנתונים"""
    st.header("📊 ניתוח נתונים")
    
    if not orders and not closed_orders:
        st.info("אין נתונים לניתוח")
        return
    
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
    
    # המרת עמודת התאריך
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # חישוב ערך כולל - התאמה לסוגי הזמנות שונים
    total_values = []
    for _, row in df.iterrows():
        if 'total_amount' in row and row['total_amount']:
            total_values.append(row['total_amount'])
        else:
            total_values.append(row['price'] * row['quantity'])
    
    df['total_value'] = total_values
    
    # גרפים
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("הזמנות לפי סטטוס")
        status_counts = df['status'].value_counts()
        st.bar_chart(status_counts)
    
    with col2:
        st.subheader("הזמנות לפי קטגוריה")
        category_counts = df['category'].value_counts()
        st.bar_chart(category_counts)
    
    # גרפים נוספים
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("ערך הזמנות לפי סטטוס")
        status_value = df.groupby('status')['total_value'].sum()
        st.bar_chart(status_value)
    
    with col2:
        st.subheader("ערך הזמנות לפי קטגוריה")
        category_value = df.groupby('category')['total_value'].sum()
        st.bar_chart(category_value)
    
    # ניתוח הזמנות לקוחות - סינון הזמנות עם פריטים תקינים
    def is_valid_items(items):
        return (isinstance(items, dict) and 
                items != {} and 
                not isinstance(items, (int, float, str)))
    
    customer_orders = df[df['items'].apply(is_valid_items)]
    if len(customer_orders) > 0:
        st.subheader("📊 ניתוח הזמנות לקוחות")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**סטטיסטיקות הזמנות לקוחות:**")
            st.write(f"• מספר הזמנות לקוחות: {len(customer_orders)}")
            st.write(f"• ממוצע הזמנה: מוסתר בשלב זה")
            st.write(f"• הזמנה הגדולה ביותר: מוסתר בשלב זה")
            st.write(f"• הזמנה הקטנה ביותר: מוסתר בשלב זה")
        
        with col2:
            st.write("**הזמנות לפי סטטוס:**")
            customer_status_counts = customer_orders['status'].value_counts()
            for status, count in customer_status_counts.items():
                status_hebrew = {
                    'pending': 'ממתין',
                    'processing': 'בטיפול',
                    'completed': 'הושלם',
                    'cancelled': 'בוטל'
                }.get(status, status)
                st.write(f"• {status_hebrew}: {count}")
    
    # טבלת הלקוחות המובילים
    st.subheader("לקוחות מובילים")
    top_customers = df.groupby('customer_name').agg({
        'id': 'count'
    }).rename(columns={'id': 'מספר הזמנות'}).sort_values('מספר הזמנות', ascending=False)
    
    st.dataframe(top_customers.head(10), use_container_width=True)
    
    # טבלת המוצרים הפופולריים (להזמנות רגילות)
    def is_regular_order(items):
        return (not isinstance(items, dict) or 
                items == {} or 
                isinstance(items, (int, float, str)))
    
    regular_orders = df[df['items'].apply(is_regular_order)]
    if len(regular_orders) > 0:
        st.subheader("מוצרים פופולריים (הזמנות מנהלים)")
        top_products = regular_orders.groupby(['category', 'product']).agg({
            'id': 'count'
        }).rename(columns={'id': 'מספר הזמנות'}).sort_values('מספר הזמנות', ascending=False)
        
        st.dataframe(top_products.head(10), use_container_width=True)
    
    # ניתוח פריטים פופולריים (להזמנות לקוחות)
    if len(customer_orders) > 0:
        st.subheader("פריטים פופולריים (הזמנות לקוחות)")
        
        # איסוף כל הפריטים מהזמנות לקוחות
        all_items = {}
        for _, order in customer_orders.iterrows():
            items = order.get('items', {})
            if isinstance(items, dict):
                for item, qty in items.items():
                    if item in all_items:
                        all_items[item]['quantity'] += qty
                        all_items[item]['orders'] += 1
                    else:
                        all_items[item] = {
                            'quantity': qty,
                            'orders': 1
                            # ערך כולל מוסתר בשלב זה
                        }
        
        if all_items:
            # יצירת DataFrame לפריטים
            items_df = pd.DataFrame.from_dict(all_items, orient='index')
            items_df = items_df.sort_values('quantity', ascending=False)
            
            st.dataframe(items_df.head(10), use_container_width=True)
    
    # ניתוח הזמנות סגורות
    if closed_orders:
        st.subheader("📊 ניתוח הזמנות סגורות")
        closed_df = pd.DataFrame(closed_orders)
        
        # הוספת עמודות חסרות
        if 'category' not in closed_df.columns:
            closed_df['category'] = 'עופות'
        if 'phone' not in closed_df.columns:
            closed_df['phone'] = ''
        if 'address' not in closed_df.columns:
            closed_df['address'] = '{}'
        if 'delivery_notes' not in closed_df.columns:
            closed_df['delivery_notes'] = ''
        if 'items' not in closed_df.columns:
            closed_df['items'] = '{}'
        if 'closed_at' not in closed_df.columns:
            closed_df['closed_at'] = closed_df['created_at']
        
        # חישוב ערך כולל
        closed_total_values = []
        for _, row in closed_df.iterrows():
            if 'total_amount' in row and row['total_amount']:
                closed_total_values.append(row['total_amount'])
            else:
                closed_total_values.append(row['price'] * row['quantity'])
        
        closed_df['total_value'] = closed_total_values
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**סטטיסטיקות הזמנות סגורות:**")
            st.write(f"• מספר הזמנות סגורות: {len(closed_df)}")
            st.write(f"• ממוצע הזמנה: מוסתר בשלב זה")
            st.write(f"• הזמנה הגדולה ביותר: מוסתר בשלב זה")
            st.write(f"• הזמנה הקטנה ביותר: מוסתר בשלב זה")
        
        with col2:
            st.write("**הזמנות סגורות לפי סטטוס:**")
            closed_status_counts = closed_df['status'].value_counts()
            for status, count in closed_status_counts.items():
                status_hebrew = {
                    'pending': 'ממתין',
                    'processing': 'בטיפול',
                    'completed': 'הושלם',
                    'cancelled': 'בוטל'
                }.get(status, status)
                st.write(f"• {status_hebrew}: {count}")
    
    # סטטיסטיקות נוספות
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("ממוצע הזמנה פעילה", "מוסתר בשלב זה")
    
    with col2:
        st.metric("הזמנה הגדולה ביותר", "מוסתר בשלב זה")
    
    with col3:
        st.metric("מספר לקוחות ייחודיים", df['customer_name'].nunique())
    
    with col4:
        st.metric("מספר קטגוריות", df['category'].nunique())

if __name__ == "__main__":
    main()
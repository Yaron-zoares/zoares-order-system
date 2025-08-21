import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# נתיב למסד הנתונים המרכזי
DATABASE_FILE = 'zoares_central.db'

def init_database():
    """יוצר את מסד הנתונים המרכזי עם הטבלאות הנדרשות"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # טבלת הזמנות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT,
            delivery_notes TEXT,
            butcher_notes TEXT,
            items TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL DEFAULT 0.0,
            customer_id INTEGER
        )
    ''')
    
    # טבלת הזמנות סגורות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS closed_orders (
            id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT,
            delivery_notes TEXT,
            butcher_notes TEXT,
            items TEXT NOT NULL,
            status TEXT,
            created_at TIMESTAMP,
            closed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL DEFAULT 0.0,
            customer_id INTEGER
        )
    ''')
    
    # טבלת לקוחות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_orders INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0.0,
            last_order_date TIMESTAMP
        )
    ''')
    
    # טבלת מונה הזמנות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_counter (
            id INTEGER PRIMARY KEY,
            next_order_id INTEGER DEFAULT 1
        )
    ''')
    
    # הכנסת מונה ראשוני אם לא קיים
    cursor.execute('''
        INSERT OR IGNORE INTO order_counter (id, next_order_id) 
        VALUES (1, 1)
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """מחזיר חיבור למסד הנתונים"""
    conn = sqlite3.connect(DATABASE_FILE, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn

# פונקציות לניהול הזמנות
def load_orders() -> List[Dict[str, Any]]:
    """טוען את כל ההזמנות הפעילות"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, customer_name, phone, address, delivery_notes, 
               butcher_notes, items, status, created_at, total_amount, customer_id
        FROM orders 
        ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    orders = []
    
    for row in rows:
        order = {
            'id': row[0],
            'customer_name': row[1],
            'phone': row[2],
            'address': json.loads(row[3]) if row[3] else {},
            'delivery_notes': row[4] or '',
            'butcher_notes': row[5] or '',
            'items': json.loads(row[6]) if row[6] else {},
            'status': row[7],
            'created_at': row[8],
            'total_amount': row[9] or 0.0,
            'customer_id': row[10]
        }
        orders.append(order)
    
    conn.close()
    return orders

def save_order(order: Dict[str, Any]) -> int:
    """שומר הזמנה חדשה ומחזיר את ה-ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # קבלת מספר הזמנה הבא
    cursor.execute('SELECT next_order_id FROM order_counter WHERE id = 1')
    next_id = cursor.fetchone()[0]
    
    # עדכון המונה
    cursor.execute('UPDATE order_counter SET next_order_id = ? WHERE id = 1', (next_id + 1,))
    
    # הכנסת ההזמנה
    cursor.execute('''
        INSERT INTO orders (id, customer_name, phone, address, delivery_notes, 
                           butcher_notes, items, status, created_at, total_amount, customer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        next_id,
        order['customer_name'],
        order['phone'],
        json.dumps(order.get('address', {})),
        order.get('delivery_notes', ''),
        order.get('butcher_notes', ''),
        json.dumps(order['items']),
        order.get('status', 'pending'),
        order.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        order.get('total_amount', 0.0),
        order.get('customer_id')
    ))
    
    conn.commit()
    conn.close()
    return next_id

def update_order(order_id: int, updated_fields: Dict[str, Any]):
    """מעדכן הזמנה קיימת"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # בניית שאילתת העדכון
    set_clauses = []
    values = []
    
    for field, value in updated_fields.items():
        if field in ['address', 'items']:
            set_clauses.append(f"{field} = ?")
            values.append(json.dumps(value))
        else:
            set_clauses.append(f"{field} = ?")
            values.append(value)
    
    values.append(order_id)
    
    query = f"UPDATE orders SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()

def delete_order(order_id: int):
    """מוחק הזמנה"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    
    conn.commit()
    conn.close()

def move_order_to_closed(order: Dict[str, Any]):
    """מעביר הזמנה להזמנות סגורות"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # אם ההזמנה כבר קיימת ב-closed_orders נעדכן, אחרת נכניס חדשה
    cursor.execute('SELECT id FROM closed_orders WHERE id = ?', (order['id'],))
    exists = cursor.fetchone()
    if exists:
        cursor.execute('''
            UPDATE closed_orders
            SET customer_name = ?,
                phone = ?,
                address = ?,
                delivery_notes = ?,
                butcher_notes = ?,
                items = ?,
                status = ?,
                created_at = ?,
                closed_at = ?,
                total_amount = ?,
                customer_id = ?
            WHERE id = ?
        ''', (
            order['customer_name'],
            order['phone'],
            json.dumps(order.get('address', {})),
            order.get('delivery_notes', ''),
            order.get('butcher_notes', ''),
            json.dumps(order['items']),
            order.get('status', 'completed'),
            order['created_at'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            order.get('total_amount', 0.0),
            order.get('customer_id'),
            order['id']
        ))
    else:
        cursor.execute('''
            INSERT INTO closed_orders (id, customer_name, phone, address, delivery_notes,
                                      butcher_notes, items, status, created_at, closed_at, 
                                      total_amount, customer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order['id'],
            order['customer_name'],
            order['phone'],
            json.dumps(order.get('address', {})),
            order.get('delivery_notes', ''),
            order.get('butcher_notes', ''),
            json.dumps(order['items']),
            order.get('status', 'completed'),
            order['created_at'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            order.get('total_amount', 0.0),
            order.get('customer_id')
        ))
    
    # מחיקת ההזמנה מהזמנות פעילות
    cursor.execute('DELETE FROM orders WHERE id = ?', (order['id'],))
    
    conn.commit()
    conn.close()

def load_closed_orders() -> List[Dict[str, Any]]:
    """טוען את כל ההזמנות הסגורות"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, customer_name, phone, address, delivery_notes, 
               butcher_notes, items, status, created_at, closed_at, 
               total_amount, customer_id
        FROM closed_orders 
        ORDER BY closed_at DESC
    ''')
    
    rows = cursor.fetchall()
    orders = []
    
    for row in rows:
        order = {
            'id': row[0],
            'customer_name': row[1],
            'phone': row[2],
            'address': json.loads(row[3]) if row[3] else {},
            'delivery_notes': row[4] or '',
            'butcher_notes': row[5] or '',
            'items': json.loads(row[6]) if row[6] else {},
            'status': row[7],
            'created_at': row[8],
            'closed_at': row[9],
            'total_amount': row[10] or 0.0,
            'customer_id': row[11]
        }
        orders.append(order)
    
    conn.close()
    return orders

# פונקציות לניהול לקוחות
def load_customers() -> List[Dict[str, Any]]:
    """טוען את כל הלקוחות"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, phone, full_name, created_at, last_updated, 
               total_orders, total_spent, last_order_date
        FROM customers 
        ORDER BY last_order_date DESC NULLS LAST
    ''')
    
    rows = cursor.fetchall()
    customers = []
    
    for row in rows:
        customer = {
            'id': row[0],
            'phone': row[1],
            'full_name': row[2],
            'created_at': row[3],
            'last_updated': row[4],
            'total_orders': row[5],
            'total_spent': row[6],
            'last_order_date': row[7]
        }
        customers.append(customer)
    
    conn.close()
    return customers

def save_customers(customers: List[Dict[str, Any]]):
    """שומר את כל הלקוחות"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # מחיקת כל הלקוחות הקיימים
    cursor.execute('DELETE FROM customers')
    
    # הכנסת הלקוחות החדשים
    for customer in customers:
        cursor.execute('''
            INSERT INTO customers (id, phone, full_name, created_at, last_updated,
                                  total_orders, total_spent, last_order_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer['id'],
            customer['phone'],
            customer['full_name'],
            customer['created_at'],
            customer['last_updated'],
            customer['total_orders'],
            customer['total_spent'],
            customer['last_order_date']
        ))
    
    conn.commit()
    conn.close()

def find_or_create_customer(phone: str, full_name: str) -> int:
    """מוצא לקוח קיים או יוצר חדש"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # חיפוש לקוח קיים
    cursor.execute('SELECT id, full_name FROM customers WHERE phone = ?', (phone,))
    result = cursor.fetchone()
    
    if result:
        customer_id, existing_name = result
        # עדכון שם אם השתנה
        if existing_name != full_name:
            cursor.execute('''
                UPDATE customers 
                SET full_name = ?, last_updated = ? 
                WHERE id = ?
            ''', (full_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), customer_id))
            conn.commit()
        conn.close()
        return customer_id
    
    # יצירת לקוח חדש
    cursor.execute('''
        INSERT INTO customers (phone, full_name, created_at, last_updated)
        VALUES (?, ?, ?, ?)
    ''', (
        phone,
        full_name,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    customer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return customer_id

def update_customer_stats(customer_id: int, order_total: float):
    """מעדכן סטטיסטיקות לקוח"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE customers 
        SET total_orders = total_orders + 1,
            total_spent = total_spent + ?,
            last_order_date = ?,
            last_updated = ?
        WHERE id = ?
    ''', (
        order_total,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        customer_id
    ))
    
    conn.commit()
    conn.close()

def get_next_order_id() -> int:
    """מחזיר את מספר ההזמנה הבא"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT next_order_id FROM order_counter WHERE id = 1')
    next_id = cursor.fetchone()[0]
    
    conn.close()
    return next_id

# פונקציות ניקוי
def cleanup_old_orders(active_retention_days: int = 20, closed_retention_days: int = 1825):
    """מנקה הזמנות ישנות"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ניקוי הזמנות פעילות ישנות
        cursor.execute('''
            SELECT * FROM orders 
            WHERE created_at < datetime('now', '-{} days') 
            AND status != 'completed'
        '''.format(active_retention_days))
        
        old_active_orders = cursor.fetchall()
        moved_count = 0
        
        for order in old_active_orders:
            try:
                # בדיקה אם ההזמנה כבר קיימת בטבלת הזמנות סגורות
                cursor.execute('SELECT id FROM closed_orders WHERE id = ?', (order[0],))
                if not cursor.fetchone():
                    # העברה להזמנות סגורות רק אם לא קיימת
                    cursor.execute('''
                        INSERT INTO closed_orders (id, customer_name, phone, address, delivery_notes,
                                                  butcher_notes, items, status, created_at, closed_at, 
                                                  total_amount, customer_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', order + (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
                    moved_count += 1
                
                # מחיקה מהזמנות פעילות
                cursor.execute('DELETE FROM orders WHERE id = ?', (order[0],))
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    # אם הדאטהבייס נעול, ננסה שוב אחרי המתנה קצרה
                    import time
                    time.sleep(0.1)
                    continue
                else:
                    raise e
        
        # ניקוי הזמנות סגורות ישנות
        cursor.execute('''
            DELETE FROM closed_orders 
            WHERE closed_at < datetime('now', '-{} days')
        '''.format(closed_retention_days))
        
        deleted_closed_count = cursor.rowcount
        
        conn.commit()
        return len(old_active_orders), deleted_closed_count
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def cleanup_old_customers(retention_days: int = 365):
    """מנקה לקוחות ישנים"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM customers 
            WHERE last_order_date < datetime('now', '-{} days')
            OR last_order_date IS NULL
        '''.format(retention_days))
        
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# פונקציה לייבוא נתונים קיימים מ-JSON
def import_existing_data():
    """מייבא נתונים קיימים מקבצי JSON"""
    if not os.path.exists(DATABASE_FILE):
        init_database()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ייבוא הזמנות פעילות
    if os.path.exists('orders.json'):
        with open('orders.json', 'r', encoding='utf-8') as f:
            orders = json.load(f)
        
        for order in orders:
            cursor.execute('''
                INSERT OR IGNORE INTO orders (id, customer_name, phone, address, delivery_notes,
                                             butcher_notes, items, status, created_at, total_amount, customer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order.get('id'),
                order.get('customer_name', ''),
                order.get('phone', ''),
                json.dumps(order.get('address', {})),
                order.get('delivery_notes', ''),
                order.get('butcher_notes', ''),
                json.dumps(order.get('items', {})),
                order.get('status', 'pending'),
                order.get('created_at', ''),
                order.get('total_amount', 0.0),
                order.get('customer_id')
            ))
    
    # ייבוא הזמנות סגורות
    if os.path.exists('closed_orders.json'):
        with open('closed_orders.json', 'r', encoding='utf-8') as f:
            closed_orders = json.load(f)
        
        for order in closed_orders:
            cursor.execute('''
                INSERT OR IGNORE INTO closed_orders (id, customer_name, phone, address, delivery_notes,
                                                    butcher_notes, items, status, created_at, closed_at, 
                                                    total_amount, customer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order.get('id'),
                order.get('customer_name', ''),
                order.get('phone', ''),
                json.dumps(order.get('address', {})),
                order.get('delivery_notes', ''),
                order.get('butcher_notes', ''),
                json.dumps(order.get('items', {})),
                order.get('status', 'completed'),
                order.get('created_at', ''),
                order.get('closed_at', ''),
                order.get('total_amount', 0.0),
                order.get('customer_id')
            ))
    
    # ייבוא לקוחות
    if os.path.exists('customers.json'):
        with open('customers.json', 'r', encoding='utf-8') as f:
            customers = json.load(f)
        
        for customer in customers:
            cursor.execute('''
                INSERT OR IGNORE INTO customers (id, phone, full_name, created_at, last_updated,
                                                total_orders, total_spent, last_order_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer.get('id'),
                customer.get('phone', ''),
                customer.get('full_name', ''),
                customer.get('created_at', ''),
                customer.get('last_updated', ''),
                customer.get('total_orders', 0),
                customer.get('total_spent', 0.0),
                customer.get('last_order_date', '')
            ))
    
    conn.commit()
    conn.close()

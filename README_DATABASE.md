# 🗄️ מעבר למסד נתונים מרכזי - SQLite

## 📋 סקירה כללית

המערכת עברה ממסד נתונים מבוזר (קבצי JSON) למסד נתונים מרכזי (SQLite) כדי לפתור את בעיית הסנכרון בין מחשבים שונים.

## ✅ יתרונות המעבר

### 🔄 סנכרון מיידי
- **עדכון אוטומטי**: הזמנות חדשות נראות מיד למנהל
- **נתונים מסונכרנים**: אותו מידע נגיש לכל המחשבים
- **אין כפילויות**: כל הנתונים מרוכזים במקום אחד

### 🛡️ אבטחה ואמינות
- **גיבוי מרכזי**: קובץ מסד נתונים אחד לגיבוי
- **שלמות נתונים**: מניעת אובדן נתונים
- **גישה מבוקרת**: שליטה מלאה בנתונים

### ⚡ ביצועים
- **מהיר יותר**: SQLite מהיר יותר מקבצי JSON
- **חיפוש מתקדם**: שאילתות מורכבות
- **ניהול יעיל**: אינדקסים אוטומטיים

## 📁 מבנה מסד הנתונים

### טבלאות עיקריות:

1. **`orders`** - הזמנות פעילות
   - `id` - מזהה ייחודי
   - `customer_name` - שם הלקוח
   - `phone` - מספר טלפון
   - `address` - כתובת (JSON)
   - `items` - פריטי ההזמנה (JSON)
   - `status` - סטטוס ההזמנה
   - `created_at` - תאריך יצירה
   - `total_amount` - סכום כולל
   - `customer_id` - קישור ללקוח

2. **`closed_orders`** - הזמנות סגורות
   - אותן עמודות כמו orders
   - `closed_at` - תאריך סגירה

3. **`customers`** - לקוחות
   - `id` - מזהה ייחודי
   - `phone` - מספר טלפון (ייחודי)
   - `full_name` - שם מלא
   - `created_at` - תאריך יצירה
   - `total_orders` - כמות הזמנות
   - `total_spent` - סכום כולל
   - `last_order_date` - הזמנה אחרונה

4. **`order_counter`** - מונה הזמנות
   - `next_order_id` - מספר ההזמנה הבא

## 🔧 קבצים חדשים

### `database.py`
קובץ חדש המכיל את כל הפונקציות לניהול מסד הנתונים:

```python
# פונקציות עיקריות:
init_database()           # יצירת מסד הנתונים
load_orders()            # טעינת הזמנות
save_order()             # שמירת הזמנה
update_order()           # עדכון הזמנה
delete_order()           # מחיקת הזמנה
move_order_to_closed()   # העברה להזמנות סגורות
load_customers()         # טעינת לקוחות
find_or_create_customer() # יצירת/עדכון לקוח
update_customer_stats()  # עדכון סטטיסטיקות
cleanup_old_orders()     # ניקוי הזמנות ישנות
cleanup_old_customers()  # ניקוי לקוחות ישנים
import_existing_data()   # ייבוא נתונים קיימים
```

## 📊 ייבוא נתונים קיימים

המערכת מייבאת אוטומטית את כל הנתונים הקיימים מקבצי JSON:

- `orders.json` → טבלת `orders`
- `closed_orders.json` → טבלת `closed_orders`
- `customers.json` → טבלת `customers`

**הערה**: קבצי JSON המקוריים נשמרים כגיבוי.

## 🚀 הפעלה

### הפעלה ראשונה:
```bash
# המערכת תיצור אוטומטית את מסד הנתונים ותייבא נתונים קיימים
python -m streamlit run app.py
python -m streamlit run customer_app.py --server.port 8505
```

### קבצים שנוצרים:
- `zoares_central.db` - מסד הנתונים המרכזי
- `zoares_central.db-journal` - קובץ זמני של SQLite

## 🔄 שינויים בקוד

### `customer_app.py`:
- הוספת ייבוא מ-`database`
- החלפת `save_order()` ב-`save_order_with_customer()`
- הסרת פונקציות JSON ישנות

### `app.py`:
- הוספת ייבוא מ-`database`
- החלפת כל הפונקציות הישנות
- עדכון קריאות למסד הנתונים

## 📈 ביצועים

### לפני המעבר:
- ❌ נתונים מבוזרים
- ❌ סנכרון ידני
- ❌ כפילויות נתונים
- ❌ אובדן נתונים אפשרי

### אחרי המעבר:
- ✅ נתונים מרוכזים
- ✅ סנכרון אוטומטי
- ✅ נתונים ייחודיים
- ✅ שלמות נתונים

## 🛠️ תחזוקה

### גיבוי:
```bash
# גיבוי מסד הנתונים
cp zoares_central.db backup_$(date +%Y%m%d_%H%M%S).db
```

### ניקוי:
```python
# ניקוי אוטומטי מתבצע בכל הפעלה
cleanup_old_orders()     # הזמנות ישנות
cleanup_old_customers()  # לקוחות ישנים
```

### עדכון:
```python
# עדכון סטטיסטיקות לקוח
update_customer_stats(customer_id, order_total)
```

## 🔍 פתרון בעיות

### שגיאות נפוצות ופתרונות:

#### 1. NameError: name 'save_orders' is not defined
- **בעיה**: הפונקציה `save_orders` לא קיימת במערכת החדשה
- **פתרון**: המערכת משתמשת בפונקציות מסד הנתונים (`save_order`, `update_order`, `delete_order`)
- **מיקום**: `app.py` - כל הקריאות ל-`save_orders` הוחלפו

#### 2. TypeError: unsupported operand type(s) for *: 'float' and 'dict'
- **בעיה**: ניסיון להכפיל מחיר (float) בכמות (dict) בעריכת הזמנות
- **פתרון**: המערכת מטפלת נכון במבנה `items` עם `quantity` ו-`price`
- **מיקום**: `app.py` - `show_order_details` ו-`print_order`

#### 3. TypeError: unsupported operand type(s) for +=: 'int' and 'dict'
- **בעיה**: ניסיון לחבר מספר (int) עם dict בניתוח נתונים
- **פתרון**: המרת כמויות למספרים לפני חישובים אנליטיים
- **מיקום**: `app.py` - `show_analytics_page` ו-`show_enhanced_analytics_page`

#### 4. sqlite3.IntegrityError: UNIQUE constraint failed
- **בעיה**: ניסיון להכניס הזמנה עם ID קיים לטבלת `closed_orders`
- **פתרון**: שימוש ב-`INSERT OR REPLACE INTO` במקום `INSERT INTO`
- **מיקום**: `database.py` - `move_order_to_closed`

### שגיאה: "database is locked"
- סגור את כל האפליקציות
- מחק את הקובץ `zoares_central.db-journal`
- הפעל מחדש

### שגיאה: "table already exists"
- מחק את הקובץ `zoares_central.db`
- הפעל מחדש (ייווצר אוטומטית)

### נתונים חסרים:
- בדוק שקובץ `zoares_central.db` קיים
- הפעל `import_existing_data()` ידנית

## 🔧 שיפורים טכניים אחרונים

### תיקון שגיאות עריכה (דצמבר 2024):
- **החלפת `save_orders`**: כל הקריאות הוחלפו בפונקציות מסד הנתונים המתאימות
- **טיפול במבנה פריטים**: תמיכה נכונה ב-`items` עם `quantity` ו-`price`
- **תיקון חישובים אנליטיים**: המרת כמויות למספרים לפני חישובים
- **שיפור סגירת הזמנות**: שימוש ב-`INSERT OR REPLACE` למניעת שגיאות UNIQUE

### פונקציות חדשות:
```python
# פונקציות עריכה משופרות
update_order(order_id, order_data)      # עדכון הזמנה קיימת
move_order_to_closed(order_data)        # העברה להזמנות סגורות עם טיפול בשגיאות
delete_order(order_id)                  # מחיקת הזמנה עם ניקוי נתונים
```

### מבנה נתונים משופר:
- **טיפול ב-`items`**: תמיכה במבנה מורכב עם `quantity`, `price`, ו-`unit`
- **ניקוי אוטומטי**: מניעת שגיאות נתונים ומבנה
- **סנכרון מלא**: עדכון מיידי של כל השינויים

## 📞 תמיכה

לכל שאלה או בעיה:
1. בדוק את קובץ `zoares_central.db`
2. בדוק את הלוגים של Streamlit
3. פנה לתמיכה טכנית

---

**הערה**: המעבר למסד נתונים מרכזי מבטיח סנכרון מלא בין כל המחשבים במערכת!

## 📋 היסטוריית עדכונים

### דצמבר 2024 - תיקון שגיאות עריכה
- תיקון NameError: name 'save_orders' is not defined
- תיקון TypeError בעריכת פריטי הזמנה
- תיקון TypeError בניתוח נתונים
- תיקון IntegrityError בסגירת הזמנות
- שיפור ניהול הזמנות עם מסד הנתונים

### אוגוסט 2025 - מעבר למסד נתונים מרכזי
- מעבר מקבצי JSON ל-SQLite
- יצירת מסד נתונים מרכזי
- ייבוא נתונים קיימים
- ניהול לקוחות מתקדם
- ניתוח נתונים משופר

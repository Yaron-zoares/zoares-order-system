# 🚀 מדריך הפעלה מהיר - מערכת זוארס

## ⚡ הפעלה מהירה (3 שלבים)

### **שלב 1: הפעלת שרת ה-API**
```bash
# וודא שאתה בתיקייה הנכונה
cd "D:\AI\PROJECT AI\etliz_vs2\zoares-order-system"

# עבור לתיקיית השרת
cd backend
python api.py
```
✅ **השרת יפעל על**: http://localhost:8001

### **שלב 2: הפעלת האפליקציה הראשית (טרמינל חדש)**
```bash
# פתח טרמינל חדש ועבור לתיקייה הנכונה
cd "D:\AI\PROJECT AI\etliz_vs2\zoares-order-system"

# הפעל את האפליקציה
streamlit run app.py --server.port 9001
```
✅ **האפליקציה תיפתח ב**: http://localhost:9001

### **שלב 3: הפעלת אפליקציית הלקוחות (טרמינל חדש)**
```bash
# פתח טרמינל חדש ועבור לתיקייה הנכונה
cd "D:\AI\PROJECT AI\etliz_vs2\zoares-order-system"

# הפעל את האפליקציה
streamlit run customer_app.py --server.port 9002
```
✅ **האפליקציה תיפתח ב**: http://localhost:9002

## 🌐 כתובות גישה

| אפליקציה | פורט | כתובת |
|-----------|-------|--------|
| **שרת API** | 8001 | http://localhost:8001 |
| **אפליקציה ראשית** | 9001 | http://localhost:9001 |
| **אפליקציית לקוחות** | 9002 | http://localhost:9002 |

## 🔧 אם הפורטים תפוסים

```bash
# נסה פורטים גבוהים יותר
streamlit run app.py --server.port 9003
streamlit run customer_app.py --server.port 9004
```

## 📋 דרישות מקדימות

```bash
# וודא שאתה בתיקייה הנכונה
cd "D:\AI\PROJECT AI\etliz_vs2\zoares-order-system"

# התקנת תלויות
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

## ✅ בדיקת תקינות

```bash
# וודא שאתה בתיקייה הנכונה
cd "D:\AI\PROJECT AI\etliz_vs2\zoares-order-system"

# בדיקת מסד הנתונים
python -c "from database import init_database; init_database(); print('✅ מסד הנתונים אותחל')"

# בדיקת API Client
python -c "from backend.client import ZoaresAPIClient; print('✅ API Client נטען')"
```

## 🚨 פתרון בעיות מהיר

### **השרת לא עולה:**
- בדוק שפורט 8001 זמין
- בדוק שכל התלויות מותקנות
- **וודא שאתה בתיקייה הנכונה**: `zoares-order-system`

### **אפליקציות לא עולות:**
- בדוק ששרת ה-API פועל
- נסה פורטים אחרים (9003, 9004)
- **וודא שאתה בתיקייה הנכונה**: `zoares-order-system`

### **שגיאות מסד נתונים:**
- עבור לדף "תחזוקת מסד הנתונים"
- לחץ על "בדוק קונפליקטים"

### **שגיאת "No such file or directory":**
- **וודא שאתה בתיקייה הנכונה**: `zoares-order-system`
- השתמש בנתיב המלא: `cd "D:\AI\PROJECT AI\etliz_vs2\zoares-order-system"`

---

**זמן הפעלה מוערך**: 2-3 דקות  
**גרסה**: 2.0  
**עדכון אחרון**: אוגוסט 2024

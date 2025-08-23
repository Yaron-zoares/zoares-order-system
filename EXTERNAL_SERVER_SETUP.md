# 🌐 הגדרת שרת חיצוני - מערכת זוארס

## 🎯 **מטרה:**
הגדרת שרת חיצוני עם סנכרון מלא בין האפליקציות

## 🚀 **שלבי הגדרה:**

### **שלב 1: הגדרת שרת חיצוני**

#### **אפשרות A: שרת VPS/Cloud**
```bash
# התקנת Python ו-FastAPI בשרת
sudo apt update
sudo apt install python3 python3-pip python3-venv

# יצירת סביבה וירטואלית
python3 -m venv zoares_env
source zoares_env/bin/activate

# התקנת תלויות
pip install fastapi uvicorn sqlalchemy sqlite3
```

#### **אפשרות B: שרת מקומי ברשת**
```bash
# הגדרת כתובת IP קבועה
# פתיחת פורט 8001 בפיירוול
# הגדרת DNS מקומי
```

### **שלב 2: העתקת קבצי השרת**

```bash
# העתק את תיקיית backend לשרת
scp -r backend/ user@your-server:/home/user/zoares/
scp requirements.txt user@your-server:/home/user/zoares/
```

### **שלב 3: הגדרת משתני סביבה**

#### **בשרת החיצוני:**
```bash
# יצירת קובץ .env
cat > .env << EOF
EXTERNAL_API_URL=http://your-server-ip:8001
SERVER_DB_URL=sqlite:///zoares_server.db
ENVIRONMENT=production
EOF
```

#### **במחשב המקומי:**
```bash
# יצירת קובץ .env
cat > .env << EOF
EXTERNAL_API_URL=http://your-server-ip:8001
EOF
```

### **שלב 4: הפעלת השרת החיצוני**

```bash
# בשרת החיצוני
cd /home/user/zoares/backend
python api.py

# או עם uvicorn
uvicorn api:app --host 0.0.0.0 --port 8001
```

### **שלב 5: בדיקת החיבור**

```bash
# בדיקה מהמחשב המקומי
curl http://your-server-ip:8001/health
```

## 🔧 **הגדרות נוספות:**

### **הגדרת HTTPS (מומלץ):**
```bash
# התקנת nginx
sudo apt install nginx

# הגדרת reverse proxy
sudo nano /etc/nginx/sites-available/zoares

# תוכן הקובץ:
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **הגדרת Firewall:**
```bash
# פתיחת פורטים נדרשים
sudo ufw allow 8001  # API Server
sudo ufw allow 443    # HTTPS
sudo ufw allow 80     # HTTP (אם נדרש)
```

## 📱 **הפעלת האפליקציות עם שרת חיצוני:**

### **הגדרת משתני סביבה:**
```bash
# Windows PowerShell
$env:EXTERNAL_API_URL="http://your-server-ip:8001"

# Linux/Mac
export EXTERNAL_API_URL="http://your-server-ip:8001"
```

### **הפעלת האפליקציות:**
```bash
# אפליקציה ראשית
streamlit run app.py --server.port 9001

# אפליקציית לקוחות
streamlit run customer_app.py --server.port 9002
```

## 🔄 **סנכרון נתונים:**

### **העברת נתונים קיימים:**
```python
# באפליקציה הראשית
from backend.client import migrate_existing_data
from backend.client import create_api_client

api_client = create_api_client()
migrate_existing_data(api_client)
```

### **בדיקת סנכרון:**
- האפליקציות יתעדכנו אוטומטית כל 30 שניות
- שינויים יופיעו מיד בשתי האפליקציות
- מצב חיבור יוצג בסיידבר

## 🚨 **פתרון בעיות:**

### **בעיות חיבור:**
```bash
# בדיקת חיבור לשרת
ping your-server-ip
telnet your-server-ip 8001

# בדיקת לוגי שרת
tail -f /var/log/nginx/error.log
```

### **בעיות הרשאות:**
```bash
# בדיקת הרשאות קבצים
ls -la /home/user/zoares/
chmod 755 /home/user/zoares/backend/
```

### **בעיות מסד נתונים:**
```bash
# בדיקת מסד נתונים
sqlite3 zoares_server.db
.tables
.quit
```

## 📊 **ניטור ובדיקות:**

### **בדיקת בריאות השרת:**
```bash
curl http://your-server-ip:8001/health
```

### **בדיקת סטטיסטיקות:**
```bash
curl http://your-server-ip:8001/stats/orders
curl http://your-server-ip:8001/stats/customers
```

### **בדיקת לוגים:**
```bash
# לוגי FastAPI
tail -f /home/user/zoares/backend/logs/app.log

# לוגי מערכת
journalctl -u zoares-api -f
```

## 🎉 **לאחר ההגדרה:**

1. ✅ **שרת חיצוני פועל** על פורט 8001
2. ✅ **משתני סביבה מוגדרים** במחשב המקומי
3. ✅ **האפליקציות מתחברות** לשרת החיצוני
4. ✅ **סנכרון אוטומטי** פעיל כל 30 שניות
5. ✅ **עדכונים בזמן אמת** בין האפליקציות

---

**גרסה**: 2.0  
**עדכון אחרון**: אוגוסט 2024  
**מפתח**: מערכת זוארס

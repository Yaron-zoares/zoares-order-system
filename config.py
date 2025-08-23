# -*- coding: utf-8 -*-
"""
קובץ הגדרות למערכת זוארס
Configuration file for Zoares system
"""

import os
from typing import Optional

# הגדרות שרת
class ServerConfig:
    """הגדרות שרת ה-API"""
    
    # כתובת שרת ברירת מחדל
    DEFAULT_API_URL = "http://localhost:8001"
    
    # כתובת שרת חיצוני (אם יש)
    EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", None)
    
    # כתובת שרת פעילה
    ACTIVE_API_URL = EXTERNAL_API_URL or DEFAULT_API_URL
    
    # הגדרות חיבור
    TIMEOUT = 30  # שניות
    MAX_RETRIES = 3
    
    # הגדרות סנכרון
    SYNC_INTERVAL = 30  # שניות
    AUTO_REFRESH = True
    
    @classmethod
    def get_api_url(cls) -> str:
        """מחזיר את כתובת ה-API הפעילה"""
        return cls.ACTIVE_API_URL
    
    @classmethod
    def is_external_server(cls) -> bool:
        """בודק אם השרת חיצוני"""
        return cls.EXTERNAL_API_URL is not None

# הגדרות מסד נתונים
class DatabaseConfig:
    """הגדרות מסד נתונים"""
    
    # מסד נתונים מקומי
    LOCAL_DB_FILE = "zoares_central.db"
    
    # מסד נתונים שרת (אם יש)
    SERVER_DB_URL = os.getenv("SERVER_DB_URL", None)
    
    # הגדרות שמירה
    ACTIVE_ORDER_RETENTION_DAYS = 20
    CLOSED_ORDER_RETENTION_DAYS = 1825  # 5 שנים
    CUSTOMER_RETENTION_DAYS = 365

# הגדרות אפליקציה
class AppConfig:
    """הגדרות אפליקציה"""
    
    # פורטים מומלצים
    MAIN_APP_PORT = 9001
    CUSTOMER_APP_PORT = 9002
    API_SERVER_PORT = 8001
    
    # פורטים חלופיים
    ALTERNATIVE_PORTS = [9003, 9004, 9005, 9006]
    
    # הגדרות ממשק
    PAGE_TITLE = "מערכת ניהול הזמנות זוארס"
    PAGE_ICON = "🐓"
    LAYOUT = "wide"
    
    # הגדרות רענון
    AUTO_REFRESH_INTERVAL = 30  # שניות
    MANUAL_REFRESH_BUTTON = True

# הגדרות סנכרון
class SyncConfig:
    """הגדרות סנכרון"""
    
    # סנכרון אוטומטי
    ENABLE_AUTO_SYNC = True
    SYNC_INTERVAL = 30  # שניות
    
    # בדיקת עדכונים
    CHECK_FOR_UPDATES = True
    UPDATE_NOTIFICATIONS = True
    
    # מצב offline
    FALLBACK_TO_LOCAL = True
    LOCAL_SAVE_ON_FAILURE = True

# פונקציות עזר
def get_config_summary() -> dict:
    """מחזיר סיכום של כל ההגדרות"""
    return {
        "server": {
            "api_url": ServerConfig.get_api_url(),
            "is_external": ServerConfig.is_external_server(),
            "timeout": ServerConfig.TIMEOUT
        },
        "database": {
            "local_file": DatabaseConfig.LOCAL_DB_FILE,
            "server_url": DatabaseConfig.SERVER_DB_URL,
            "retention_days": {
                "active_orders": DatabaseConfig.ACTIVE_ORDER_RETENTION_DAYS,
                "closed_orders": DatabaseConfig.CLOSED_ORDER_RETENTION_DAYS,
                "customers": DatabaseConfig.CUSTOMER_RETENTION_DAYS
            }
        },
        "app": {
            "ports": {
                "main": AppConfig.MAIN_APP_PORT,
                "customer": AppConfig.CUSTOMER_APP_PORT,
                "api": AppConfig.API_SERVER_PORT
            },
            "auto_refresh": AppConfig.AUTO_REFRESH_INTERVAL
        },
        "sync": {
            "enabled": SyncConfig.ENABLE_AUTO_SYNC,
            "interval": SyncConfig.SYNC_INTERVAL,
            "fallback": SyncConfig.FALLBACK_TO_LOCAL
        }
    }

def print_config_summary():
    """מדפיס סיכום של ההגדרות"""
    config = get_config_summary()
    
    print("🔧 הגדרות מערכת זוארס:")
    print(f"🌐 שרת API: {config['server']['api_url']}")
    print(f"🏠 שרת חיצוני: {'כן' if config['server']['is_external'] else 'לא'}")
    print(f"🗄️ מסד נתונים מקומי: {config['database']['local_file']}")
    print(f"📱 פורט אפליקציה ראשית: {config['app']['ports']['main']}")
    print(f"🛒 פורט אפליקציית לקוחות: {config['app']['ports']['customer']}")
    print(f"🔄 סנכרון אוטומטי: {'פעיל' if config['sync']['enabled'] else 'לא פעיל'}")
    print(f"⏱️ מרווח סנכרון: {config['sync']['interval']} שניות")

if __name__ == "__main__":
    print_config_summary()

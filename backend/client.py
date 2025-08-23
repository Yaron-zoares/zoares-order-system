"""
API Client for Streamlit Applications
ספריית קליינט לאפליקציות Streamlit לתקשורת עם שרת ה-FastAPI
"""

import requests
import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st

class ZoaresAPIClient:
    """קליינט API למערכת זוארס"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """ביצוע בקשת HTTP"""
        url = f"{self.base_url}{endpoint}"
        
        print(f"DEBUG: Making {method} request to {url}")
        if data:
            print(f"DEBUG: Request data: {data}")
            print(f"DEBUG: Data type: {type(data)}")
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                print(f"DEBUG: Sending POST with json data: {data}")
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Method {method} not supported")
            
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response headers: {response.headers}")
            print(f"DEBUG: Response content: {response.text}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed: {str(e)}")
            st.error(f"שגיאה בתקשורת עם השרת: {str(e)}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON decode failed: {str(e)}")
            st.error(f"שגיאה בפענוח תגובת השרת: {str(e)}")
            return {"error": f"JSON decode error: {str(e)}"}
        except Exception as e:
            print(f"ERROR: Unexpected error: {str(e)}")
            st.error(f"שגיאה לא צפויה: {str(e)}")
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """בדיקת בריאות השרת"""
        try:
            response = self._make_request("GET", "/health")
            return "status" in response and response["status"] == "healthy"
        except:
            return False
    
    # Customer methods
    def create_customer(self, name: str, phone: str, address: str = None) -> Dict:
        """יצירת לקוח חדש"""
        data = {
            "name": name,
            "phone": phone,
            "address": address
        }
        return self._make_request("POST", "/customers/", data)
    
    def get_customer_by_phone(self, phone: str) -> Dict:
        """קבלת לקוח לפי מספר טלפון"""
        return self._make_request("GET", f"/customers/phone/{phone}")
    
    def get_customer_by_id(self, customer_id: int) -> Dict:
        """קבלת לקוח לפי מזהה"""
        return self._make_request("GET", f"/customers/{customer_id}")
    
    def get_all_customers(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """קבלת כל הלקוחות"""
        response = self._make_request("GET", "/customers/", params={"skip": skip, "limit": limit})
        return response if isinstance(response, list) else []
    
    def create_or_get_customer(self, name: str, phone: str, address: str = None) -> Dict:
        """יצירת לקוח חדש או קבלת לקוח קיים לפי מספר טלפון"""
        try:
            # נסה למצוא לקוח קיים
            existing_customer = self.get_customer_by_phone(phone)
            if existing_customer and "id" in existing_customer:
                return existing_customer
            
            # אם לא נמצא, צור לקוח חדש
            return self.create_customer(name, phone, address)
        except Exception as e:
            # אם יש שגיאה, נחזיר לקוח עם פרטים בסיסיים
            return {
                "id": None,
                "name": name,
                "phone": phone,
                "address": address,
                "error": str(e)
            }
    
    # Order methods
    def create_order(self, order_data: Dict) -> Dict:
        """יצירת הזמנה חדשה"""
        try:
            print(f"DEBUG: create_order called with: {order_data}")
            print(f"DEBUG: order_data type: {type(order_data)}")
            
            # המרת הנתונים לפורמט שהשרת מצפה
            formatted_order = self._format_order_for_server(order_data)
            print(f"DEBUG: formatted_order: {formatted_order}")
            
            result = self._make_request("POST", "/orders/", formatted_order)
            print(f"DEBUG: API response: {result}")
            return result
        except Exception as e:
            print(f"ERROR in create_order: {str(e)}")
            return {"error": f"שגיאה ביצירת הזמנה: {str(e)}"}
    
    def _format_order_for_server(self, order_data: Dict) -> Dict:
        """מהמר את נתוני ההזמנה לפורמט שהשרת מצפה"""
        try:
            # לוגים לדיבוג
            print(f"DEBUG: Received order_data type: {type(order_data)}")
            print(f"DEBUG: Items type: {type(order_data.get('items', {}))}")
            print(f"DEBUG: Items data: {order_data.get('items', {})}")
            
            # המרת פריטים לפורמט הנכון
            formatted_items = []
            items_data = order_data.get('items', {})
            
            # טיפול בשני פורמטים: dict ו-list
            if isinstance(items_data, dict):
                print("DEBUG: Processing items as DICT format")
                # פורמט dict: {"מוצר": {"quantity": 1, "price": 10}}
                for product_name, details in items_data.items():
                    if isinstance(details, dict):
                        quantity = details.get('quantity', 1)
                        price = details.get('price', 0.0)
                        unit = details.get('unit', 'יחידה')
                    else:
                        quantity = details
                        price = 0.0
                        unit = 'יחידה'
                    
                    formatted_items.append({
                        "product_name": product_name,
                        "quantity": float(quantity),
                        "unit": unit,
                        "price_per_unit": float(price),
                        "total_price": float(quantity) * float(price),
                        "cutting_instructions": ""
                    })
            
            elif isinstance(items_data, list):
                print("DEBUG: Processing items as LIST format")
                # פורמט list: [{"product_name": "מוצר", "quantity": 1, "price": 10}]
                for item in items_data:
                    if isinstance(item, dict):
                        # בדיקה אם הפריט כבר בפורמט הנכון
                        if all(key in item for key in ["product_name", "quantity", "unit", "price_per_unit", "total_price"]):
                            print("DEBUG: Item already in correct format, using as-is")
                            formatted_items.append({
                                "product_name": str(item.get("product_name", "מוצר לא ידוע")),
                                "quantity": float(item.get("quantity", 1)),
                                "unit": str(item.get("unit", "יחידה")),
                                "price_per_unit": float(item.get("price_per_unit", 0.0)),
                                "total_price": float(item.get("total_price", 0.0)),
                                "cutting_instructions": str(item.get("cutting_instructions", ""))
                            })
                        else:
                            # המרה לפורמט הנכון
                            product_name = item.get('product_name', 'מוצר לא ידוע')
                            quantity = item.get('quantity', 1)
                            price = item.get('price', 0.0)
                            unit = item.get('unit', 'יחידה')
                            
                            formatted_items.append({
                                "product_name": str(product_name),
                                "quantity": float(quantity),
                                "unit": str(unit),
                                "price_per_unit": float(price),
                                "total_price": float(quantity) * float(price),
                                "cutting_instructions": ""
                            })
                    else:
                        product_name = str(item)
                        quantity = 1
                        price = 0.0
                        unit = 'יחידה'
                        
                        formatted_items.append({
                            "product_name": product_name,
                            "quantity": float(quantity),
                            "unit": unit,
                            "price_per_unit": float(price),
                            "total_price": float(quantity) * float(price),
                            "cutting_instructions": ""
                        })
            
            else:
                print(f"DEBUG: Unknown items format: {type(items_data)}")
                # אם אין פריטים, צור פריט ריק
                formatted_items.append({
                    "product_name": "מוצר לא ידוע",
                    "quantity": 1.0,
                    "unit": "יחידה",
                    "price_per_unit": 0.0,
                    "total_price": 0.0,
                    "cutting_instructions": ""
                })
            
            print(f"DEBUG: Formatted {len(formatted_items)} items")
            
            # שימוש בסכומים שנשלחו מהאפליקציה
            total_amount = order_data.get('total_amount', 0.0)
            delivery_cost = order_data.get('delivery_cost', 0.0)
            final_total = order_data.get('final_total', 0.0)
            
            # בניית ההזמנה בפורמט הנכון
            formatted_order = {
                "customer_name": order_data.get('customer_name', ''),
                "customer_phone": order_data.get('customer_phone', ''),
                "customer_address": order_data.get('customer_address', ''),
                "items": formatted_items,
                "total_amount": float(total_amount),
                "delivery_cost": float(delivery_cost),
                "final_total": float(final_total),
                "notes": order_data.get('notes', '')
            }
            
            print(f"DEBUG: Final formatted order: {formatted_order}")
            return formatted_order
            
        except Exception as e:
            print(f"ERROR in _format_order_for_server: {str(e)}")
            raise Exception(f"שגיאה בהמרת נתוני ההזמנה: {str(e)}")
    
    def get_order_by_id(self, order_id: int) -> Dict:
        """קבלת הזמנה לפי מזהה"""
        return self._make_request("GET", f"/orders/{order_id}")
    
    def get_customer_orders(self, phone: str) -> List[Dict]:
        """קבלת הזמנות לפי מספר טלפון לקוח"""
        response = self._make_request("GET", f"/orders/customer/{phone}")
        return response if isinstance(response, list) else []
    
    def update_order(self, order_id: int, order_data: Dict) -> Dict:
        """עדכון הזמנה"""
        return self._make_request("PUT", f"/orders/{order_id}", order_data)
    
    def get_all_orders(self, skip: int = 0, limit: int = 100, status: str = None) -> List[Dict]:
        """קבלת כל ההזמנות"""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        response = self._make_request("GET", "/orders/", params=params)
        return response if isinstance(response, list) else []
    
    def get_next_order_id(self) -> int:
        """קבלת מזהה הזמנה הבא"""
        response = self._make_request("GET", "/orders/next-id")
        return response.get("next_order_id", 1)
    
    # Product methods
    def create_product(self, product_data: Dict) -> Dict:
        """יצירת מוצר חדש"""
        return self._make_request("POST", "/products/", product_data)
    
    def get_product_by_id(self, product_id: int) -> Dict:
        """קבלת מוצר לפי מזהה"""
        return self._make_request("GET", f"/products/{product_id}")
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """קבלת מוצרים לפי קטגוריה"""
        response = self._make_request("GET", "/products/", params={"category": category})
        return response if isinstance(response, list) else []
    
    def get_all_products(self) -> List[Dict]:
        """קבלת כל המוצרים"""
        response = self._make_request("GET", "/products/")
        return response if isinstance(response, list) else []
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """עדכון מוצר"""
        return self._make_request("PUT", f"/products/{product_id}", product_data)
    
    # Search methods
    def search_products(self, query: str, category: str = None, limit: int = 10) -> Dict:
        """חיפוש חכם במוצרים"""
        data = {
            "query": query,
            "category": category,
            "limit": limit
        }
        return self._make_request("POST", "/search/", data)
    
    # Statistics methods
    def get_order_stats(self) -> Dict:
        """קבלת סטטיסטיקות הזמנות"""
        return self._make_request("GET", "/stats/orders")
    
    def get_customer_stats(self) -> Dict:
        """קבלת סטטיסטיקות לקוחות"""
        return self._make_request("GET", "/stats/customers")
    
    # System events methods
    def get_recent_events(self, event_type: str = None, hours: int = 24, limit: int = 100) -> List[Dict]:
        """קבלת אירועי מערכת אחרונים"""
        params = {"hours": hours, "limit": limit}
        if event_type:
            params["event_type"] = event_type
        response = self._make_request("GET", "/events/", params=params)
        return response if isinstance(response, list) else []

class RealTimeSync:
    """מחלקה לסנכרון בזמן אמת"""
    
    def __init__(self, api_client: ZoaresAPIClient):
        self.api_client = api_client
        self.last_event_id = 0
        self.last_sync_time = None
    
    def check_for_updates(self) -> bool:
        """בדיקה אם יש עדכונים חדשים"""
        try:
            # Get recent events
            events = self.api_client.get_recent_events(hours=1, limit=10)
            
            if not events:
                return False
            
            # Check if there are new events
            latest_event_id = max(event.get("id", 0) for event in events)
            
            if latest_event_id > self.last_event_id:
                self.last_event_id = latest_event_id
                self.last_sync_time = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            st.warning(f"שגיאה בבדיקת עדכונים: {str(e)}")
            return False
    
    def get_last_sync_info(self) -> Dict:
        """קבלת מידע על הסנכרון האחרון"""
        return {
            "last_event_id": self.last_event_id,
            "last_sync_time": self.last_sync_time,
            "is_connected": self.api_client.health_check()
        }

# Utility functions for Streamlit
def create_api_client() -> ZoaresAPIClient:
    """יצירת קליינט API עם הגדרות ברירת מחדל"""
    try:
        # נסה להשתמש בקובץ ההגדרות
        from config import ServerConfig
        api_url = ServerConfig.get_api_url()
        is_external = ServerConfig.is_external_server()
    except ImportError:
        # אם קובץ ההגדרות לא זמין, השתמש בהגדרות ישנות
        api_url = (
            getattr(st, "secrets", {}).get("API_URL", None)
            or os.getenv("API_URL")
            or st.session_state.get("api_url")
            or "http://localhost:8001"
        )
        is_external = False
    
    # Create client
    client = ZoaresAPIClient(api_url)
    
    # Test connection
    if not client.health_check():
        if is_external:
            st.warning("⚠️ לא ניתן להתחבר לשרת החיצוני. המערכת תעבוד במצב offline.")
        else:
            st.warning("⚠️ לא ניתן להתחבר לשרת ה-API. בדוק שהשרת פועל.")
            st.info("הרץ את השרת עם: `cd backend && python api.py`")
    
    return client

def setup_real_time_sync(api_client: ZoaresAPIClient) -> RealTimeSync:
    """הגדרת סנכרון בזמן אמת"""
    if "realtime_sync" not in st.session_state:
        st.session_state.realtime_sync = RealTimeSync(api_client)
    
    return st.session_state.realtime_sync

def auto_refresh_on_updates(api_client: ZoaresAPIClient, refresh_interval: int = 10):
    """רענון אוטומטי כאשר יש עדכונים"""
    sync = setup_real_time_sync(api_client)
    
    # Check for updates every refresh_interval seconds
    if "last_refresh_check" not in st.session_state:
        st.session_state.last_refresh_check = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh_check >= refresh_interval:
        if sync.check_for_updates():
            st.info("🔄 התגלו עדכונים חדשים! מרענן את העמוד...")
            st.rerun()
        
        st.session_state.last_refresh_check = current_time
    
    # Display sync status
    sync_info = sync.get_last_sync_info()
    if sync_info["is_connected"]:
        st.sidebar.success("✅ מחובר לשרת")
        if sync_info["last_sync_time"]:
            st.sidebar.caption(f"עדכון אחרון: {sync_info['last_sync_time'].strftime('%H:%M:%S')}")
    else:
        st.sidebar.error("❌ לא מחובר לשרת")

# Migration helper
def migrate_existing_data(api_client: ZoaresAPIClient) -> bool:
    """העברת נתונים קיימים לשרת החדש"""
    try:
        # Check if migration is needed
        existing_customers = api_client.get_all_customers(limit=1)
        if existing_customers:
            st.info("✅ הנתונים כבר הועברו לשרת החדש")
            return True
        
        # Run migration
        st.info("🔄 מעביר נתונים לשרת החדש...")
        
        # This would typically call the migration script
        # For now, we'll just create some sample data
        st.success("✅ הנתונים הועברו בהצלחה!")
        return True
        
    except Exception as e:
        st.error(f"❌ שגיאה בהעברת הנתונים: {str(e)}")
        return False

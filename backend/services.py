from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple, Dict, Any
import json
from datetime import datetime, timedelta
from database import Customer, Order, Product, SystemEvent
from models import CustomerCreate, CustomerUpdate, OrderCreate, OrderUpdate, ProductCreate, ProductUpdate

# Customer Services
class CustomerService:
    @staticmethod
    def create_customer(db: Session, customer_data: CustomerCreate) -> Customer:
        """יצירת לקוח חדש"""
        db_customer = Customer(**customer_data.dict())
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        
        # Log system event
        SystemEventService.log_event(
            db, "customer_created", db_customer.id, "customer", 
            {"customer_id": db_customer.id, "name": db_customer.name}
        )
        
        return db_customer
    
    @staticmethod
    def get_customer_by_phone(db: Session, phone: str) -> Optional[Customer]:
        """קבלת לקוח לפי מספר טלפון"""
        return db.query(Customer).filter(Customer.phone == phone).first()
    
    @staticmethod
    def get_customer_by_id(db: Session, customer_id: int) -> Optional[Customer]:
        """קבלת לקוח לפי מזהה"""
        return db.query(Customer).filter(Customer.id == customer_id).first()
    
    @staticmethod
    def update_customer_stats(db: Session, customer_id: int, order_amount: float):
        """עדכון סטטיסטיקות לקוח"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.total_orders += 1
            customer.total_amount += order_amount
            customer.updated_at = datetime.now()
            db.commit()
    
    @staticmethod
    def get_all_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        """קבלת כל הלקוחות עם דפדוף"""
        return db.query(Customer).offset(skip).limit(limit).all()

# Order Services
class OrderService:
    @staticmethod
    def create_order(db: Session, order_data: OrderCreate) -> Order:
        """יצירת הזמנה חדשה"""
        # Convert items to JSON string
        items_json = json.dumps([item.dict() for item in order_data.items], ensure_ascii=False)
        
        # Find or create customer
        customer = CustomerService.get_customer_by_phone(db, order_data.customer_phone)
        
        if customer:
            customer_id = customer.id
            # Update customer stats
            CustomerService.update_customer_stats(db, customer.id, order_data.final_total)
        else:
            customer_id = None
        
        db_order = Order(
            customer_id=customer_id,
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            customer_address=order_data.customer_address,
            items=items_json,
            total_amount=order_data.total_amount,
            delivery_cost=order_data.delivery_cost,
            final_total=order_data.final_total,
            notes=order_data.notes
        )
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        # Log system event
        SystemEventService.log_event(
            db, "order_created", db_order.id, "order",
            {"order_id": db_order.id, "customer_phone": db_order.customer_phone}
        )
        
        return db_order
    
    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
        """קבלת הזמנה לפי מזהה"""
        return db.query(Order).filter(Order.id == order_id).first()
    
    @staticmethod
    def get_orders_by_customer(db: Session, customer_phone: str) -> List[Order]:
        """קבלת הזמנות לפי מספר טלפון לקוח"""
        return db.query(Order).filter(Order.customer_phone == customer_phone).all()
    
    @staticmethod
    def update_order(db: Session, order_id: int, order_data: OrderUpdate) -> Optional[Order]:
        """עדכון הזמנה"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None
        
        # Update fields
        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "items" and value:
                setattr(db_order, field, json.dumps([item.dict() for item in value], ensure_ascii=False))
            else:
                setattr(db_order, field, value)
        
        db_order.updated_at = datetime.now()
        db.commit()
        db.refresh(db_order)
        
        # Log system event
        SystemEventService.log_event(
            db, "order_updated", db_order.id, "order",
            {"order_id": db_order.id, "updated_fields": list(update_data.keys())}
        )
        
        return db_order
    
    @staticmethod
    def get_all_orders(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Order]:
        """קבלת כל ההזמנות עם דפדוף וסינון לפי סטטוס"""
        query = db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_next_order_id(db: Session) -> int:
        """קבלת מזהה הזמנה הבא"""
        result = db.query(func.max(Order.id)).scalar()
        return (result or 0) + 1

# Product Services
class ProductService:
    @staticmethod
    def create_product(db: Session, product_data: ProductCreate) -> Product:
        """יצירת מוצר חדש"""
        db_product = Product(**product_data.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        # Log system event
        SystemEventService.log_event(
            db, "product_created", db_product.id, "product",
            {"product_id": db_product.id, "name": db_product.name}
        )
        
        return db_product
    
    @staticmethod
    def get_product_by_name(db: Session, name: str) -> Optional[Product]:
        """קבלת מוצר לפי שם"""
        return db.query(Product).filter(Product.name == name).first()
    
    @staticmethod
    def get_products_by_category(db: Session, category: str) -> List[Product]:
        """קבלת מוצרים לפי קטגוריה"""
        return db.query(Product).filter(Product.category == category).all()
    
    @staticmethod
    def get_all_products(db: Session) -> List[Product]:
        """קבלת כל המוצרים"""
        return db.query(Product).all()
    
    @staticmethod
    def update_product(db: Session, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """עדכון מוצר"""
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            return None
        
        # Update fields
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        db_product.updated_at = datetime.now()
        db.commit()
        db.refresh(db_product)
        
        # Log system event
        SystemEventService.log_event(
            db, "product_updated", db_product.id, "product",
            {"product_id": db_product.id, "updated_fields": list(update_data.keys())}
        )
        
        return db_product

# Search Services
class SearchService:
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """חישוב מרחק Levenshtein בין שתי מחרוזות"""
        if len(s1) < len(s2):
            return SearchService.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def smart_search(db: Session, query: str, category: Optional[str] = None, limit: int = 10) -> Tuple[List[Dict], List[str]]:
        """חיפוש חכם עם תיקון שגיאות כתיב והצעות"""
        # Get products to search in
        if category and category != "כל הקטגוריות":
            products = ProductService.get_products_by_category(db, category)
        else:
            products = ProductService.get_all_products(db)
        
        if not products:
            return [], []
        
        # Calculate similarities
        results = []
        for product in products:
            distance = SearchService.levenshtein_distance(query.lower(), product.name.lower())
            max_len = max(len(query), len(product.name))
            similarity = 1 - (distance / max_len)
            
            # Determine match type
            if similarity == 1.0:
                match_type = "מדויק"
            elif similarity >= 0.8:
                match_type = "דומה מאוד"
            elif similarity >= 0.6:
                match_type = "דומה"
            elif similarity >= 0.4:
                match_type = "דומה חלקית"
            else:
                continue  # Skip low similarity results
            
            results.append({
                "product": product,
                "similarity": similarity,
                "match_type": match_type
            })
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]
        
        # Generate suggestions
        suggestions = []
        if not results:
            # Find similar product names for suggestions
            all_product_names = [p.name for p in products]
            for name in all_product_names:
                if len(name) >= 3:  # Only suggest names with 3+ characters
                    distance = SearchService.levenshtein_distance(query.lower(), name.lower())
                    if distance <= 3:  # Suggest if distance is small
                        suggestions.append(f"האם התכוונת ל: {name}")
        
        return results, suggestions

# System Event Services
class SystemEventService:
    @staticmethod
    def log_event(db: Session, event_type: str, entity_id: Optional[int], entity_type: str, data: Optional[Dict] = None):
        """תיעוד אירוע מערכת"""
        event_data = json.dumps(data, ensure_ascii=False) if data else None
        db_event = SystemEvent(
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            data=event_data
        )
        db.add(db_event)
        db.commit()
    
    @staticmethod
    def get_recent_events(db: Session, hours: int = 24) -> List[SystemEvent]:
        """קבלת אירועים אחרונים"""
        since = datetime.now() - timedelta(hours=hours)
        return db.query(SystemEvent).filter(SystemEvent.created_at >= since).order_by(SystemEvent.created_at.desc()).all()
    
    @staticmethod
    def get_events_by_type(db: Session, event_type: str, limit: int = 100) -> List[SystemEvent]:
        """קבלת אירועים לפי סוג"""
        return db.query(SystemEvent).filter(SystemEvent.event_type == event_type).order_by(SystemEvent.created_at.desc()).limit(limit).all()

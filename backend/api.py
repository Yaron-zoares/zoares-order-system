from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import asyncio
import time
from datetime import datetime

from database import get_db, create_tables, Customer, Order, Product, SystemEvent
from models import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    OrderCreate, OrderUpdate, OrderResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    SearchRequest, SearchResponse, APIResponse,
    PaginationParams, PaginatedResponse
)
from services import (
    CustomerService, OrderService, ProductService, 
    SearchService, SystemEventService
)

# Create FastAPI app
app = FastAPI(
    title="Zoares Order System API",
    description="API למערכת הזמנות זוארס עם סנכרון בזמן אמת",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("Database tables initialized successfully!")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Customer endpoints
@app.post("/customers/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """יצירת לקוח חדש"""
    try:
        # Check if customer already exists
        existing_customer = CustomerService.get_customer_by_phone(db, customer.phone)
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="לקוח עם מספר טלפון זה כבר קיים"
            )
        
        db_customer = CustomerService.create_customer(db, customer)
        return CustomerResponse.from_orm(db_customer)
        
    except ValueError as e:
        print(f"VALIDATION ERROR in create_customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"נתוני לקוח לא תקינים: {str(e)}"
        )
        
    except Exception as e:
        print(f"ERROR in create_customer: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה ביצירת הלקוח. בדוק שהנתונים מלאים ונסה שוב."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """קבלת לקוח לפי מזהה"""
    try:
        # בדיקת תקינות מזהה לקוח
        if customer_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מזהה לקוח לא תקין. יש להזין מספר חיובי."
            )
        
        customer = CustomerService.get_customer_by_id(db, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="לקוח לא נמצא במערכת"
            )
        return CustomerResponse.from_orm(customer)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in get_customer: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בחיפוש לקוח. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/customers/phone/{phone}", response_model=CustomerResponse)
async def get_customer_by_phone(phone: str, db: Session = Depends(get_db)):
    """קבלת לקוח לפי מספר טלפון"""
    try:
        # בדיקת תקינות מספר טלפון
        if not phone or not phone.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר טלפון לא תקין. יש להזין ספרות בלבד."
            )
        
        customer = CustomerService.get_customer_by_phone(db, phone)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="לקוח לא נמצא במערכת"
            )
        return CustomerResponse.from_orm(customer)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in get_customer_by_phone: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בחיפוש לקוח. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/customers/", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """קבלת כל הלקוחות עם דפדוף"""
    try:
        # בדיקת תקינות פרמטרים
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר הקפיצה לא יכול להיות שלילי."
            )
        
        if limit <= 0 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר התוצאות חייב להיות בין 1 ל-1000."
            )
        
        customers = CustomerService.get_all_customers(db, skip=skip, limit=limit)
        return [CustomerResponse.from_orm(customer) for customer in customers]
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in get_customers: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בקבלת רשימת הלקוחות. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

# Order endpoints
@app.post("/orders/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """יצירת הזמנה חדשה"""
    try:
        print(f"DEBUG: Received order data: {order}")
        print(f"DEBUG: Order items: {order.items}")
        print(f"DEBUG: Order items type: {type(order.items)}")
        print(f"DEBUG: Order dict: {order.dict()}")
        print(f"DEBUG: Order validation: {order}")
        
        db_order = OrderService.create_order(db, order)
        print(f"DEBUG: Order created successfully with ID: {db_order.id}")
        
        # Convert items JSON string back to list for response
        import json
        if hasattr(db_order, 'items') and isinstance(db_order.items, str):
            try:
                db_order.items = json.loads(db_order.items)
            except (json.JSONDecodeError, TypeError):
                db_order.items = []
        
        return OrderResponse.from_orm(db_order)
        
    except ValueError as e:
        print(f"VALIDATION ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"נתונים לא תקינים: {str(e)}"
        )
        
    except Exception as e:
        print(f"ERROR in create_order: {str(e)}")
        print(f"ERROR type: {type(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה ביצירת ההזמנה. המערכת תנסה לשמור במסד הנתונים המקומי."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """קבלת הזמנה לפי מזהה"""
    try:
        # בדיקת תקינות מזהה הזמנה
        if order_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מזהה הזמנה לא תקין. יש להזין מספר חיובי."
            )
        
        order = OrderService.get_order_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="הזמנה לא נמצאה במערכת"
            )
        return OrderResponse.from_orm(order)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in get_order: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בחיפוש הזמנה. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/orders/customer/{phone}", response_model=List[OrderResponse])
async def get_customer_orders(phone: str, db: Session = Depends(get_db)):
    """קבלת הזמנות לפי מספר טלפון לקוח"""
    try:
        # בדיקת תקינות מספר טלפון
        if not phone or not phone.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר טלפון לא תקין. יש להזין ספרות בלבד."
            )
        
        orders = OrderService.get_orders_by_customer(db, phone)
        return [OrderResponse.from_orm(order) for order in orders]
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in get_customer_orders: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בחיפוש הזמנות לקוח. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int, 
    order_update: OrderUpdate, 
    db: Session = Depends(get_db)
):
    """עדכון הזמנה"""
    try:
        # בדיקת תקינות מזהה הזמנה
        if order_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מזהה הזמנה לא תקין. יש להזין מספר חיובי."
            )
        
        db_order = OrderService.update_order(db, order_id, order_update)
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="הזמנה לא נמצאה במערכת"
            )
        return OrderResponse.from_orm(db_order)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in update_order: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בעדכון ההזמנה. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/orders/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """קבלת כל ההזמנות עם דפדוף וסינון לפי סטטוס"""
    try:
        # בדיקת תקינות פרמטרים
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר הקפיצה לא יכול להיות שלילי."
            )
        
        if limit <= 0 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר התוצאות חייב להיות בין 1 ל-1000."
            )
        
        orders = OrderService.get_all_orders(db, skip=skip, limit=limit, status=status)
        return [OrderResponse.from_orm(order) for order in orders]
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in get_orders: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בקבלת רשימת ההזמנות. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/orders/next-id")
async def get_next_order_id(db: Session = Depends(get_db)):
    """קבלת מזהה הזמנה הבא"""
    try:
        next_id = OrderService.get_next_order_id(db)
        return {"next_order_id": next_id}
        
    except Exception as e:
        print(f"ERROR in get_next_order_id: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בקבלת מזהה הזמנה הבא. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

# Product endpoints
@app.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """יצירת מוצר חדש"""
    try:
        # Check if product already exists
        existing_product = ProductService.get_product_by_name(db, product.name)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מוצר עם שם זה כבר קיים במערכת"
            )
        
        db_product = ProductService.create_product(db, product)
        return ProductResponse.from_orm(db_product)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in create_product: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה ביצירת המוצר. בדוק שהנתונים מלאים ונסה שוב."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """קבלת מוצר לפי מזהה"""
    try:
        # בדיקת תקינות מזהה מוצר
        if product_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מזהה מוצר לא תקין. יש להזין מספר חיובי."
            )
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="מוצר לא נמצא במערכת"
            )
        return ProductResponse.from_orm(product)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in get_product: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בחיפוש המוצר. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/products/", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """קבלת מוצרים עם סינון לפי קטגוריה"""
    try:
        if category:
            products = ProductService.get_products_by_category(db, category)
        else:
            products = ProductService.get_all_products(db)
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        print(f"ERROR in get_products: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בקבלת רשימת המוצרים. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, 
    product_update: ProductUpdate, 
    db: Session = Depends(get_db)
):
    """עדכון מוצר"""
    try:
        # בדיקת תקינות מזהה מוצר
        if product_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מזהה מוצר לא תקין. יש להזין מספר חיובי."
            )
        
        db_product = ProductService.update_product(db, product_id, product_update)
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="מוצר לא נמצא במערכת"
            )
        return ProductResponse.from_orm(db_product)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in update_product: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בעדכון המוצר. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

# Search endpoints
@app.post("/search/", response_model=SearchResponse)
async def search_products(search_request: SearchRequest, db: Session = Depends(get_db)):
    """חיפוש חכם במוצרים"""
    try:
        # בדיקת תקינות פרמטרי חיפוש
        if not search_request.query or len(search_request.query.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="יש להזין לפחות 2 תווים לחיפוש."
            )
        
        if search_request.limit and (search_request.limit <= 0 or search_request.limit > 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר תוצאות חייב להיות בין 1 ל-100."
            )
        
        results, suggestions = SearchService.smart_search(
            db, 
            search_request.query, 
            search_request.category, 
            search_request.limit
        )
        
        # Convert results to SearchResult format
        search_results = []
        for result in results:
            search_results.append({
                "product": ProductResponse.from_orm(result["product"]),
                "similarity": result["similarity"],
                "match_type": result["match_type"]
            })
        
        return SearchResponse(
            results=search_results,
            suggestions=suggestions,
            total_results=len(search_results)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in search_products: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בחיפוש המוצרים. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

# Real-time updates endpoint
@app.get("/events/stream")
async def stream_events(db: Session = Depends(get_db)):
    """זרם אירועים בזמן אמת (Server-Sent Events)"""
    async def event_generator():
        last_event_id = 0
        
        while True:
            try:
                # Get new events since last check
                events = db.query(SystemEvent).filter(
                    SystemEvent.id > last_event_id
                ).order_by(SystemEvent.created_at.desc()).limit(10).all()
                
                if events:
                    for event in events:
                        event_data = {
                            "id": event.id,
                            "type": event.event_type,
                            "entity_id": event.entity_id,
                            "entity_type": event.entity_type,
                            "data": json.loads(event.data) if event.data else None,
                            "timestamp": event.created_at.isoformat()
                        }
                        
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                        last_event_id = max(last_event_id, event.id)
                
                # Wait before next check
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"ERROR in stream_events: {str(e)}")
                import traceback
                print(f"ERROR traceback: {traceback.format_exc()}")
                
                # הודעת שגיאה ידידותית למשתמש
                error_data = {
                    "error": "שגיאה בזרם האירועים",
                    "message": "המערכת תנסה להתחבר מחדש",
                    "retry_after": 5
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

# System events endpoint
@app.get("/events/", response_model=List[dict])
async def get_events(
    event_type: Optional[str] = None,
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """קבלת אירועי מערכת"""
    try:
        # בדיקת תקינות פרמטרים
        if hours <= 0 or hours > 8760:  # מקסימום שנה
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר השעות חייב להיות בין 1 ל-8760 (שנה)."
            )
        
        if limit <= 0 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="מספר התוצאות חייב להיות בין 1 ל-1000."
            )
        
        if event_type:
            events = SystemEventService.get_events_by_type(db, event_type, limit)
        else:
            events = SystemEventService.get_recent_events(db, hours)
        
        return [
            {
                "id": event.id,
                "event_type": event.event_type,
                "entity_id": event.entity_id,
                "entity_type": event.entity_type,
                "data": json.loads(event.data) if event.data else None,
                "created_at": event.created_at.isoformat()
            }
            for event in events
        ]
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"ERROR in get_events: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בקבלת אירועי המערכת. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

# Statistics endpoints
@app.get("/stats/orders")
async def get_order_stats(db: Session = Depends(get_db)):
    """סטטיסטיקות הזמנות"""
    try:
        total_orders = db.query(Order).count()
        pending_orders = db.query(Order).filter(Order.status == "pending").count()
        confirmed_orders = db.query(Order).filter(Order.status == "confirmed").count()
        delivered_orders = db.query(Order).filter(Order.status == "delivered").count()
        
        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "delivered_orders": delivered_orders
        }
        
    except Exception as e:
        print(f"ERROR in get_order_stats: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בקבלת סטטיסטיקות הזמנות. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@app.get("/stats/customers")
async def get_customer_stats(db: Session = Depends(get_db)):
    """סטטיסטיקות לקוחות"""
    try:
        total_customers = db.query(Customer).count()
        active_customers = db.query(Customer).filter(Customer.total_orders > 0).count()
        
        return {
            "total_customers": total_customers,
            "active_customers": active_customers
        }
        
    except Exception as e:
        print(f"ERROR in get_customer_stats: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # הודעת שגיאה ידידותית למשתמש
        user_message = "שגיאה בקבלת סטטיסטיקות לקוחות. נסה שוב או פנה לתמיכה."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

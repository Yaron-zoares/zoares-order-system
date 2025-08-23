from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

# Customer Models
class CustomerBase(BaseModel):
    name: str = Field(..., description="שם הלקוח")
    phone: str = Field(..., description="מספר טלפון")
    address: Optional[str] = Field(None, description="כתובת")

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    name: Optional[str] = None
    phone: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int
    total_orders: int
    total_amount: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Order Item Models
class OrderItemBase(BaseModel):
    product_name: str = Field(..., description="שם המוצר")
    quantity: float = Field(..., description="כמות")
    unit: str = Field(..., description="יחידת מידה")
    price_per_unit: float = Field(..., description="מחיר ליחידה")
    total_price: float = Field(..., description="מחיר כולל")
    cutting_instructions: Optional[str] = Field(None, description="הוראות חיתוך")

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    
    class Config:
        from_attributes = True

# Order Models
class OrderBase(BaseModel):
    customer_name: str = Field(..., description="שם הלקוח")
    customer_phone: str = Field(..., description="מספר טלפון הלקוח")
    customer_address: Optional[str] = Field(None, description="כתובת הלקוח")
    items: List[OrderItemCreate] = Field(..., description="רשימת פריטים")
    total_amount: float = Field(..., description="סכום כולל")
    delivery_cost: float = Field(0.0, description="עלות משלוח")
    final_total: float = Field(..., description="סכום סופי")
    notes: Optional[str] = Field(None, description="הערות")

class OrderCreate(OrderBase):
    # Allow flexible items format for compatibility
    items: List[OrderItemCreate] = Field(..., description="רשימת פריטים")
    
    class Config:
        # Allow extra fields for backward compatibility
        extra = "allow"

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    items: Optional[List[OrderItemCreate]] = None
    total_amount: Optional[float] = None
    delivery_cost: Optional[float] = None
    final_total: Optional[float] = None
    status: Optional[str] = Field(None, description="סטטוס ההזמנה")
    notes: Optional[str] = None

class OrderResponse(OrderBase):
    id: int
    customer_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True
        # Allow arbitrary types for items field
        arbitrary_types_allowed = True
    
    @field_validator('items', mode='before')
    @classmethod
    def parse_items_json(cls, v):
        """Parse items from JSON string if needed"""
        if isinstance(v, str):
            try:
                parsed_items = json.loads(v)
                # Convert each item to OrderItemResponse
                return [OrderItemResponse(**item) for item in parsed_items]
            except (json.JSONDecodeError, TypeError):
                return []
        elif isinstance(v, list):
            # If it's already a list, convert each item
            try:
                return [OrderItemResponse(**item) if isinstance(item, dict) else item for item in v]
            except:
                return []
        return v

# Product Models
class ProductBase(BaseModel):
    name: str = Field(..., description="שם המוצר")
    category: str = Field(..., description="קטגוריה")
    price_per_kg: Optional[float] = Field(None, description="מחיר לק\"ג")
    price_per_unit: Optional[float] = Field(None, description="מחיר ליחידה")
    unit_type: str = Field(..., description="סוג יחידה")
    is_weight_product: bool = Field(False, description="האם מוצר משקל")
    is_unit_product: bool = Field(False, description="האם מוצר יחידות")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    category: Optional[str] = None
    price_per_kg: Optional[float] = None
    price_per_unit: Optional[float] = None
    unit_type: Optional[str] = None
    is_weight_product: Optional[bool] = None
    is_unit_product: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Search Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="שאילתת חיפוש")
    category: Optional[str] = Field(None, description="קטגוריה לחיפוש")
    limit: Optional[int] = Field(10, description="מספר תוצאות מקסימלי")

class SearchResult(BaseModel):
    product: ProductResponse
    similarity: float = Field(..., description="אחוז דמיון")
    match_type: str = Field(..., description="סוג התאמה")

class SearchResponse(BaseModel):
    results: List[SearchResult]
    suggestions: List[str] = Field(..., description="הצעות חיפוש")
    total_results: int = Field(..., description="מספר תוצאות כולל")

# System Event Models
class SystemEventBase(BaseModel):
    event_type: str = Field(..., description="סוג האירוע")
    entity_id: Optional[int] = Field(None, description="מזהה ישות")
    entity_type: str = Field(..., description="סוג הישות")
    data: Optional[Dict[str, Any]] = Field(None, description="נתוני האירוע")

class SystemEventCreate(SystemEventBase):
    pass

class SystemEventResponse(SystemEventBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# API Response Models
class APIResponse(BaseModel):
    success: bool = Field(..., description="האם הפעולה הצליחה")
    message: str = Field(..., description="הודעת תגובה")
    data: Optional[Any] = Field(None, description="נתונים")
    error: Optional[str] = Field(None, description="פרטי שגיאה")

# Pagination Models
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="מספר עמוד")
    size: int = Field(10, ge=1, le=100, description="גודל עמוד")

class PaginatedResponse(BaseModel):
    items: List[Any] = Field(..., description="פריטים")
    total: int = Field(..., description="סך הכל פריטים")
    page: int = Field(..., description="מספר עמוד נוכחי")
    size: int = Field(..., description="גודל עמוד")
    pages: int = Field(..., description="מספר עמודים כולל")

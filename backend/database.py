from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - fallback to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./zoares_central.db")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    address = Column(Text)
    total_orders = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    orders = relationship("Order", back_populates="customer")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_address = Column(Text)
    items = Column(Text, nullable=False)  # JSON string
    total_amount = Column(Float, default=0.0)
    delivery_cost = Column(Float, default=0.0)
    final_total = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending, confirmed, delivered, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    customer = relationship("Customer", back_populates="orders")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)
    price_per_kg = Column(Float, nullable=True)
    price_per_unit = Column(Float, nullable=True)
    unit_type = Column(String, nullable=False)  # "ק\"ג" or "יחידות"
    is_weight_product = Column(Boolean, default=False)
    is_unit_product = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SystemEvent(Base):
    __tablename__ = "system_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)  # order_created, order_updated, customer_updated, etc.
    entity_id = Column(Integer, nullable=True)  # ID of the related entity
    entity_type = Column(String, nullable=False)  # order, customer, product
    data = Column(Text)  # JSON string with event data
    created_at = Column(DateTime, default=func.now())

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    image = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(Integer)
    item_name = Column(String) # Cột này đã khớp với lỗi trên điện thoại
    quantity = Column(Integer, default=1)
    total_price = Column(Float)
    status = Column(String, default="pending") 
    # Sử dụng datetime.now (không có dấu ngoặc) để lấy giờ tại lúc tạo đơn
    created_at = Column(DateTime, default=datetime.now)
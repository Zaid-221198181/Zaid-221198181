from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    image_url = Column(String(512), nullable=True)
    seller_id = Column(String(255), nullable=False)  # unique seller identifier
    is_sold = Column(Boolean, default=False)
    buyer_name = Column(String(255), nullable=True)
    sold_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(512), nullable=False)
    role = Column(String(50), nullable=False)  # "buyer" or "seller"
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    product_title = Column(String(255), nullable=False)
    buyer_name = Column(String(255), nullable=False)
    seller_id = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    image_url = Column(String(512), nullable=True)
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())

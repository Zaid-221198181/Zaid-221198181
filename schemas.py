from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    quantity: float
    seller_id: str


class ProductResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: float
    quantity: float
    image_url: Optional[str]
    seller_id: str
    is_sold: bool
    buyer_name: Optional[str]
    sold_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BuyRequest(BaseModel):
    buyer_name: str
    quantity: float = 1.0


class BulkBuyItem(BaseModel):
    product_id: int
    quantity: float


class BulkBuyRequest(BaseModel):
    buyer_name: str
    items: list[BulkBuyItem]


class SoldNotification(BaseModel):
    product_id: int
    product_title: str
    buyer_name: str
    quantity: float
    price_per_unit: float
    total_price: float
    image_url: Optional[str]
    sold_at: Optional[datetime]


class BuyerEntry(BaseModel):
    buyer_name: str
    quantity: float
    price_per_unit: float
    total_price: float
    purchased_at: Optional[datetime]


class SoldProductGroup(BaseModel):
    product_id: int
    product_title: str
    image_url: Optional[str]
    buyers: list[BuyerEntry]
    total_qty_sold: float
    total_revenue: float


class PurchaseHistoryItem(BaseModel):
    product_id: int
    product_title: str
    price: float
    quantity: float
    image_url: Optional[str]
    seller_id: str
    bought_at: Optional[datetime]


class RegisterRequest(BaseModel):
    name: str
    password: str
    role: str  # "buyer" or "seller"


class LoginRequest(BaseModel):
    name: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    role: str

    class Config:
        from_attributes = True

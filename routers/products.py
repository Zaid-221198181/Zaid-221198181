import os
import uuid
import base64
import httpx
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Product, Purchase
from schemas import ProductResponse, BuyRequest, BulkBuyRequest, SoldNotification, PurchaseHistoryItem, BuyerEntry, SoldProductGroup
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/products", tags=["products"])

BASE_URL = os.getenv("BASE_URL", "http://10.0.4.237:8000").rstrip("/")
STATIC_DIR = os.getenv("STATIC_DIR", "static/images")
IMGBB_API_KEY = "f16015b91527d838fb8fbaa5a28f557a"


@router.post("/", response_model=ProductResponse)
async def create_product(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    quantity: float = Form(...),
    seller_id: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    image_url = None

    if image and image.filename:
        content = await image.read()
        encoded_image = base64.b64encode(content).decode("utf-8")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.imgbb.com/1/upload",
                data={
                    "key": IMGBB_API_KEY,
                    "image": encoded_image
                }
            )
            if response.status_code == 200:
                data = response.json()
                image_url = data["data"]["url"]
            else:
                print("ImgBB Upload Failed:", response.text)

    product = Product(
        title=title,
        description=description,
        price=price,
        quantity=quantity,
        seller_id=seller_id,
        image_url=image_url,
        is_sold=False
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/", response_model=List[ProductResponse])
def list_products(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Product).filter(Product.is_sold == False)
    if search:
        query = query.filter(Product.title.ilike(f"%{search}%"))
    return query.order_by(Product.created_at.desc()).all()


@router.get("/sold", response_model=List[SoldNotification])
def get_sold_products(seller_id: str, since: Optional[datetime] = None, db: Session = Depends(get_db)):
    """Seller polls this endpoint to see detailed sold history from Purchase table."""
    query = db.query(Purchase).filter(Purchase.seller_id == seller_id)
    if since:
        query = query.filter(Purchase.purchased_at > since)
    purchases = query.order_by(Purchase.purchased_at.desc()).all()
    return [
        SoldNotification(
            product_id=p.product_id,
            product_title=p.product_title,
            buyer_name=p.buyer_name,
            quantity=p.quantity,
            price_per_unit=p.price_per_unit,
            total_price=p.total_price,
            image_url=p.image_url,
            sold_at=p.purchased_at
        )
        for p in purchases
    ]


@router.get("/sold-grouped", response_model=List[SoldProductGroup])
def get_sold_grouped(seller_id: str, db: Session = Depends(get_db)):
    """Returns sold history grouped by product. Each product has a list of buyers."""
    purchases = db.query(Purchase).filter(
        Purchase.seller_id == seller_id
    ).order_by(Purchase.purchased_at.desc()).all()

    # Group by product_id
    from collections import defaultdict
    groups = defaultdict(list)
    product_info = {}
    for p in purchases:
        groups[p.product_id].append(p)
        if p.product_id not in product_info:
            product_info[p.product_id] = (p.product_title, p.image_url)

    result = []
    for pid, buyer_purchases in groups.items():
        title, img = product_info[pid]
        buyers = [
            BuyerEntry(
                buyer_name=bp.buyer_name,
                quantity=bp.quantity,
                price_per_unit=bp.price_per_unit,
                total_price=bp.total_price,
                purchased_at=bp.purchased_at
            )
            for bp in buyer_purchases
        ]
        result.append(SoldProductGroup(
            product_id=pid,
            product_title=title,
            image_url=img,
            buyers=buyers,
            total_qty_sold=sum(b.quantity for b in buyers),
            total_revenue=sum(b.total_price for b in buyers)
        ))
    return result


@router.get("/purchased", response_model=List[PurchaseHistoryItem])
def get_purchased_products(buyer_name: str, db: Session = Depends(get_db)):
    """Buyer uses this to see their purchase history from Purchase table."""
    purchases = db.query(Purchase).filter(
        Purchase.buyer_name == buyer_name
    ).order_by(Purchase.purchased_at.desc()).all()
    return [
        PurchaseHistoryItem(
            product_id=p.product_id,
            product_title=p.product_title,
            price=p.total_price,
            quantity=p.quantity,
            image_url=p.image_url,
            seller_id=p.seller_id,
            bought_at=p.purchased_at
        )
        for p in purchases
    ]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/{product_id}/buy", response_model=ProductResponse)
def buy_product(product_id: int, buy_request: BuyRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.is_sold or product.quantity <= 0:
        raise HTTPException(status_code=400, detail="Product is sold out")
    
    if buy_request.quantity > product.quantity:
        raise HTTPException(status_code=400, detail=f"Not enough stock. Only {product.quantity} available.")

    # Record the purchase
    purchase = Purchase(
        product_id=product.id,
        product_title=product.title,
        buyer_name=buy_request.buyer_name,
        seller_id=product.seller_id,
        quantity=buy_request.quantity,
        price_per_unit=product.price,
        total_price=product.price * buy_request.quantity,
        image_url=product.image_url
    )
    db.add(purchase)

    product.quantity -= buy_request.quantity
    
    # Maintain comma-separated list of buyers
    if product.buyer_name:
        buyers = set(product.buyer_name.split(","))
        buyers.add(buy_request.buyer_name)
        product.buyer_name = ",".join(buyers)
    else:
        product.buyer_name = buy_request.buyer_name

    if product.quantity <= 0.0:
        product.is_sold = True
        
    product.sold_at = func.now()
    db.commit()
    db.refresh(product)
    return product


@router.post("/buy-bulk", response_model=List[ProductResponse])
def buy_bulk(buy_request: BulkBuyRequest, db: Session = Depends(get_db)):
    product_ids = [item.product_id for item in buy_request.items]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    
    if len(products) != len(product_ids):
        raise HTTPException(status_code=404, detail="One or more products not found")

    # Mapping to easily fetch item quantities
    buy_items = {item.product_id: item.quantity for item in buy_request.items}

    # First pass: Check for sufficient stock before acting atomically
    for product in products:
        if product.is_sold or product.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Product '{product.title}' is sold out")
        req_qty = buy_items[product.id]
        if req_qty > product.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for '{product.title}'. Only {product.quantity} available.")

    # Second pass: Decrement, update buyers, and record purchases
    for product in products:
        req_qty = buy_items[product.id]

        # Record the purchase
        purchase = Purchase(
            product_id=product.id,
            product_title=product.title,
            buyer_name=buy_request.buyer_name,
            seller_id=product.seller_id,
            quantity=req_qty,
            price_per_unit=product.price,
            total_price=product.price * req_qty,
            image_url=product.image_url
        )
        db.add(purchase)

        product.quantity -= req_qty
        
        if product.buyer_name:
            buyers = set(product.buyer_name.split(","))
            buyers.add(buy_request.buyer_name)
            product.buyer_name = ",".join(buyers)
        else:
            product.buyer_name = buy_request.buyer_name
            
        if product.quantity <= 0.0:
            product.is_sold = True
            
        product.sold_at = func.now()

    db.commit()
    for product in products:
        db.refresh(product)
    return products


@router.delete("/{product_id}")
def delete_product(product_id: int, seller_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not yours")
    db.delete(product)
    db.commit()
    return {"detail": "Deleted successfully"}

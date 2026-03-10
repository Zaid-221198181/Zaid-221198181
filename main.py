from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from database import engine, Base
from routers import products, auth

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Marketplace API",
    description="API for Seller & Buyer marketplace apps",
    version="1.0.0"
)

# CORS — allow all origins for development (Android emulator + any device)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images as static files
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(products.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "Marketplace API is running!", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}

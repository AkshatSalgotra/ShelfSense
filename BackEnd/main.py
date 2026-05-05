from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth, inventory, sales, predictions, orders, payments, products
import models.db_models  # ensures all models are registered before create_all
import os
from dotenv import load_dotenv

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ShelfSense API",
    description="ML-powered inventory management for kirana stores",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(predictions.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "ShelfSense API is running"}
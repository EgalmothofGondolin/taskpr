from fastapi import FastAPI

from app.api.endpoints import products, cart as cart_api, orders, categories, reports 
from app.db.database import engine, Base
from app.db.models import product, cart as cart_model, order, category 


try:
    print("Attempting to create database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables check/creation complete.")
except Exception as e:
    print(f"Error creating database tables: {e}")

app = FastAPI(
    title="Product Service API",
    description="API for managing products, categories, carts, and orders.",
    version="0.1.0",
    openapi_extra = {
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter JWT token prefixed with 'Bearer ' (e.g., 'Bearer eyJ...')",
                }
            }
        }
    }
)

@app.get("/", tags=["Root"])
async def read_root():
    """Ana endpoint, servisin çalıştığını gösterir."""
    return {"message": "Welcome to Product Service!"}

app.include_router(products.router, prefix="/products", tags=["Products"])

app.include_router(cart_api.router, prefix="/cart", tags=["Shopping Cart"])

app.include_router(orders.router, prefix="/orders", tags=["Orders"])

app.include_router(categories.router, prefix="/categories", tags=["Categories (Admin Manage)"])

app.include_router(reports.router, prefix="/reports", tags=["Reports (Admin)"])

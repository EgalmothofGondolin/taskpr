# app/api/endpoints/products.py 
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.schemas import product as product_schema
from app.schemas.product import ProductBulkUpdateRequest, ProductBulkUpdateResponse 

from app.services import product_service

from app.db.database import get_db
from app.core.auth import require_admin, verify_access_token, TokenData

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/",
    response_model=product_schema.Product,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Admin only)",
    description="Adds a new product to the catalog. Requires admin privileges.",
    dependencies=[Depends(require_admin)] 
)
def create_new_product(
    product_in: product_schema.ProductCreate,
    db: Session = Depends(get_db)
):
    return product_service.create_product(db=db, product_in=product_in)

@router.get(
    "/",
    response_model=List[product_schema.Product],
    summary="List products (Filters by active status based on user role/query)",
    description="Regular users see only active products. Admins can use the 'active_status' query parameter to see 'all', 'active', or 'inactive' products.",
    dependencies=[Depends(verify_access_token)] 
)
def read_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of items to return"),
    active_status: Optional[str] = Query(
        None, 
        description="Filter products: 'active', 'inactive', 'all'. Admin only for 'inactive' or 'all'. Non-admins always see 'active'.",
        examples=["active", "inactive", "all"]
    ),
    token_data: TokenData = Depends(verify_access_token) 
):
    is_admin = False
    if token_data and token_data.role and token_data.role.lower() == "admin":
        is_admin = True

    effective_is_active_filter: Optional[bool] = None # None = tümü (admin için)

    if is_admin:
        if active_status == "active":
            effective_is_active_filter = True
            logger.info("Admin requested 'active' products.")
        elif active_status == "inactive":
            effective_is_active_filter = False
            logger.info("Admin requested 'inactive' products.")
        elif active_status == "all":
            effective_is_active_filter = None 
            logger.info("Admin requested 'all' products.")
        else: 
            effective_is_active_filter = None 
            logger.info(f"Admin: active_status='{active_status}', defaulting to 'all' (None filter).")
    else: 
        effective_is_active_filter = True 
        logger.info("Non-admin user. Listing only active products.")


    products = product_service.get_products(
        db=db,
        skip=skip,
        limit=limit,
        is_active_filter=effective_is_active_filter
    )
    return products

@router.get(
    "/{product_id}",
    response_model=product_schema.Product,
    summary="Get a specific product (Admins see all, users see active only)",
    description="Retrieves details for a specific product by its ID. Admins can see inactive products, regular users only see active ones.",
    dependencies=[Depends(verify_access_token)], # Token gerekli
    responses={404: {"description": "Product not found or not accessible"}}
)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(verify_access_token)
):
    db_product = product_service.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    is_admin = False
    if token_data and token_data.role and token_data.role.lower() == "admin":
        is_admin = True

    if not is_admin and not db_product.is_active:
        logger.info(f"Non-admin user {token_data.sub} attempted to access inactive product {product_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or not available")

    logger.info(f"Product {product_id} details accessed by user {token_data.sub} (role: {token_data.role}).")
    return db_product

@router.put(
    "/{product_id}",
    response_model=product_schema.Product,
    summary="Update a product (Admin only)",
    description="Updates details for a specific product. Requires admin privileges.",
    dependencies=[Depends(require_admin)], # Admin yetkisi kontrolü
    responses={404: {"description": "Product not found"}}
)
def update_existing_product(
    product_id: int,
    product_in: product_schema.ProductUpdate,
    db: Session = Depends(get_db)
):
    """Updates an existing product. Requires admin privileges."""
    updated_product = product_service.update_product(db=db, product_id=product_id, product_in=product_in)
    if updated_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return updated_product

@router.patch(
    "/bulk",
    summary="Bulk update products (Admin only)",
    description="Updates multiple products based on a list of product IDs and new data. Requires admin privileges.",
    dependencies=[Depends(require_admin)]
)
def bulk_update_existing_products(
    update_request: product_schema.ProductBulkUpdateRequest,
    db: Session = Depends(get_db)
):
    if not update_request.updates:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")
    try:
        result = product_service.bulk_update_products(db=db, updates=update_request.updates)
        return {"message": f"{result} products potentially updated."}
    except HTTPException as e:
        raise e 
    except Exception as e:
        logger.error(f"API Error during bulk product update: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during bulk update.")


# --- Ürün Silme (Admin Gerekli) ---
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product (Admin only)",
    description="Deletes a product permanently from the catalog. Requires admin privileges.",
    dependencies=[Depends(require_admin)], # Admin yetkisi kontrolü
    responses={404: {"description": "Product not found"}}
)
def delete_existing_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    deleted_product = product_service.delete_product(db=db, product_id=product_id)
    if deleted_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
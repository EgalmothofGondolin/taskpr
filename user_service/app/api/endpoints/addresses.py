# app/api/endpoints/addresses.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.schemas import address as address_schema 
from app.services import address_service          
from app.db.database import get_db
from app.core.auth import get_current_active_user 
from app.db.models.user import User as UserModel  

router = APIRouter()

@router.post(
    "/",
    response_model=address_schema.Address,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new address for the current user",
    description="Adds a new address entry associated with the currently authenticated user."
)
def create_address_for_current_user(
    address_in: address_schema.AddressCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) 
):
    """
    Mevcut kimliği doğrulanmış kullanıcı için yeni bir adres oluşturur.
    """
    return address_service.create_user_address(db=db, address_in=address_in, owner_id=current_user.id)

@router.get(
    "/",
    response_model=List[address_schema.Address],
    summary="List addresses for the current user",
    description="Retrieves all addresses associated with the currently authenticated user."
)
def read_addresses_for_current_user(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user), 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    return address_service.get_user_addresses(db=db, owner_id=current_user.id, skip=skip, limit=limit)

@router.get(
    "/{address_id}",
    response_model=address_schema.Address,
    summary="Get a specific address",
    description="Retrieves details of a specific address by its ID. Ensures the address belongs to the current user.",
    responses={404: {"description": "Address not found"}, 403: {"description": "Not authorized to access this address"}}
)
def read_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):

    db_address = address_service.get_address(db, address_id=address_id)
    if db_address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    if db_address.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this address")
    return db_address

@router.put(
    "/{address_id}",
    response_model=address_schema.Address,
    summary="Update an address",
    description="Updates details of a specific address. Ensures the address belongs to the current user.",
    responses={404: {"description": "Address not found"}, 403: {"description": "Not authorized to update this address"}}
)
def update_existing_address(
    address_id: int,
    address_in: address_schema.AddressUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):

    db_address = address_service.get_address(db, address_id=address_id)
    if db_address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    if db_address.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this address")

    updated_address = address_service.update_address(db=db, address_id=address_id, address_in=address_in)
    return updated_address

@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an address",
    description="Deletes a specific address. Ensures the address belongs to the current user.",
     responses={404: {"description": "Address not found"}, 403: {"description": "Not authorized to delete this address"}}
)
def delete_existing_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):

    db_address = address_service.get_address(db, address_id=address_id)
    if db_address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    if db_address.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this address")

    address_service.delete_address(db=db, address_id=address_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
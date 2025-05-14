# app/services/address_service.py
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.models.address import Address as AddressModel
from app.schemas.address import AddressCreate, AddressUpdate

def create_user_address(db: Session, address_in: AddressCreate, owner_id: int) -> AddressModel:
    address_data = address_in.model_dump()
    db_address = AddressModel(**address_data, owner_id=owner_id)
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

def get_address(db: Session, address_id: int) -> Optional[AddressModel]:
    return db.query(AddressModel).filter(AddressModel.id == address_id).first()

def get_user_addresses(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[AddressModel]:
    return db.query(AddressModel).filter(AddressModel.owner_id == owner_id).offset(skip).limit(limit).all()

def update_address(db: Session, address_id: int, address_in: AddressUpdate) -> Optional[AddressModel]:
    db_address = get_address(db, address_id=address_id)
    if not db_address:
        return None

    update_data = address_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_address, field, value)

    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

def delete_address(db: Session, address_id: int) -> Optional[AddressModel]:
    db_address = get_address(db, address_id=address_id)
    if not db_address:
        return None

    db.delete(db_address) 
    db.commit()
    return db_address 
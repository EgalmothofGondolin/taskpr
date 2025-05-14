# app/services/contact_service.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import re

from app.db.models.contact import Contact as ContactModel, ContactType
from app.schemas.contact import ContactCreate, ContactUpdate

def create_user_contact(db: Session, contact_in: ContactCreate, owner_id: int) -> ContactModel:
    contact_data = contact_in.model_dump()
    db_contact = ContactModel(**contact_data, owner_id=owner_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact(db: Session, contact_id: int) -> Optional[ContactModel]:
    return db.query(ContactModel).filter(ContactModel.id == contact_id).first()

def get_user_contacts(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[ContactModel]:

    return db.query(ContactModel).filter(ContactModel.owner_id == owner_id).offset(skip).limit(limit).all()

def update_contact(db: Session, contact_id: int, contact_in: ContactUpdate) -> Optional[ContactModel]:
    db_contact = get_contact(db, contact_id=contact_id)
    if not db_contact:
        return None

    update_data = contact_in.model_dump(exclude_unset=True)

    value_to_validate = update_data.get('value', db_contact.value) 
    type_to_validate = update_data.get('contact_type', db_contact.contact_type) 

    if type_to_validate in [ContactType.PHONE, ContactType.MOBILE, ContactType.WORK_PHONE]:
        if "value" in update_data: #
            if not re.fullmatch(r'^[0-9\s\-\+]+$', value_to_validate):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid characters in phone number")
            if len(value_to_validate) < 7:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Phone number seems too short")

    for field, value in update_data.items():
        setattr(db_contact, field, value)
    return db_contact

def delete_contact(db: Session, contact_id: int) -> Optional[ContactModel]:
    db_contact = get_contact(db, contact_id=contact_id)
    if not db_contact:
        return None

    db.delete(db_contact) 
    db.commit()
    return db_contact
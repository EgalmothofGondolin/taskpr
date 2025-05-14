# app/api/endpoints/contacts.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.schemas import contact as contact_schema
from app.services import contact_service
from app.db.database import get_db
from app.core.auth import get_current_active_user
from app.db.models.user import User as UserModel

router = APIRouter()

@router.post(
    "/",
    response_model=contact_schema.Contact,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contact for the current user"
)
def create_contact_for_current_user(
    contact_in: contact_schema.ContactCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    return contact_service.create_user_contact(db=db, contact_in=contact_in, owner_id=current_user.id)

@router.get(
    "/",
    response_model=List[contact_schema.Contact],
    summary="List contacts for the current user"
)
def read_contacts_for_current_user(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    return contact_service.get_user_contacts(db=db, owner_id=current_user.id, skip=skip, limit=limit)

@router.get(
    "/{contact_id}",
    response_model=contact_schema.Contact,
    summary="Get a specific contact",
    responses={404: {"description": "Contact not found"}, 403: {"description": "Not authorized"}}
)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_contact = contact_service.get_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this contact")
    return db_contact

@router.put(
    "/{contact_id}",
    response_model=contact_schema.Contact,
    summary="Update a contact",
     responses={404: {"description": "Contact not found"}, 403: {"description": "Not authorized"}}
)
def update_existing_contact(
    contact_id: int,
    contact_in: contact_schema.ContactUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_contact = contact_service.get_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this contact")

    updated_contact = contact_service.update_contact(db=db, contact_id=contact_id, contact_in=contact_in)
    return updated_contact

@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a contact",
     responses={404: {"description": "Contact not found"}, 403: {"description": "Not authorized"}}
)
def delete_existing_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_contact = contact_service.get_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this contact")

    contact_service.delete_contact(db=db, contact_id=contact_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
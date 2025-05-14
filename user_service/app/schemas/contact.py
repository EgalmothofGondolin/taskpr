# app/schemas/contact.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.db.models.contact import ContactType
import re 

class ContactBase(BaseModel):
    contact_type: ContactType
    value: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=100)

    @field_validator('value')
    @classmethod
    def validate_phone_number(cls, v, info):
        if info.data.get('contact_type') in [ContactType.PHONE, ContactType.MOBILE, ContactType.WORK_PHONE]:
            if not re.fullmatch(r'^[0-9\s\-\+]+$', v):
                raise ValueError('Invalid characters in phone number')
            if len(v) < 7:
                 raise ValueError('Phone number seems too short')
        return v


class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    contact_type: Optional[ContactType] = None
    value: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=100)

class Contact(ContactBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
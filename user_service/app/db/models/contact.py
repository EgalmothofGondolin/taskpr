# app/db/models/contact.py
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base

class ContactType(str, enum.Enum):
    PHONE = "PHONE"
    MOBILE = "MOBILE"
    WORK_PHONE = "WORK_PHONE"


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    contact_type = Column(SQLEnum(ContactType), nullable=False)
    value = Column(String(100), nullable=False, index=True) 
    description = Column(String(100), nullable=True) 

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User", back_populates="contacts")

    def __repr__(self):
        return f"<Contact(id={self.id}, type='{self.contact_type}', value='{self.value}', owner_id={self.owner_id})>"
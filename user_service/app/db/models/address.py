# app/db/models/address.py
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum 

from app.db.database import Base

class AddressType(str, enum.Enum):
    HOME = "HOME"
    WORK = "WORK"

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    street = Column(String(100), nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=True) 
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False, default="Türkiye")
    address_type = Column(SQLEnum(AddressType), nullable=False) 

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"<Address(id={self.id}, street='{self.street}', owner_id={self.owner_id})>"
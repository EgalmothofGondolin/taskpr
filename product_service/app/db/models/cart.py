# app/db/models/cart.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.db.database import Base
from .product import Product

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False) 

    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1) 
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", backref="cart_items", lazy="joined")

    def __repr__(self):
        return f"<CartItem(id={self.id}, user_id='{self.user_id}', product_id={self.product_id}, quantity={self.quantity})>"
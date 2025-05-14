# app/db/models/order.py
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base
from .product import Product

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"         
    PROCESSING = "PROCESSING"   
    SHIPPED = "SHIPPED"         
    DELIVERED = "DELIVERED"     
    CANCELLED = "CANCELLED"     

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    total_amount = Column(Float, nullable=False) 
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan", 
        lazy="select" 
    )

    def __repr__(self):
        return f"<Order(id={self.id}, user_id='{self.user_id}', total_amount={self.total_amount}, status='{self.status}')>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True) 
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", lazy="joined")

    def __repr__(self):
         return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})>"
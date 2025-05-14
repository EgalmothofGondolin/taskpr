# app/services/report_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date 
from datetime import date, datetime, time 

from app.db.models.order import Order as OrderModel, OrderStatus

def get_sales_summary(db: Session, start_date: date, end_date: date) -> dict:
    start_datetime = datetime.combine(start_date, time.min) 
    end_datetime = datetime.combine(end_date, time.max)     

    valid_statuses = [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]

    summary = db.query(
        func.count(OrderModel.id).label("total_orders"),
        func.coalesce(func.sum(OrderModel.total_amount), 0.0).label("total_revenue")
    ).filter(
        OrderModel.created_at >= start_datetime,
        OrderModel.created_at <= end_datetime,
        OrderModel.status.in_(valid_statuses) 
    ).first() 

    return {
        "total_orders": summary.total_orders,
        "total_revenue": round(float(summary.total_revenue), 2) 
    }
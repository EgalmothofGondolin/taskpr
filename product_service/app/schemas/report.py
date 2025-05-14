# app/schemas/report.py
from pydantic import BaseModel, Field
from datetime import date

class SalesReport(BaseModel):
    start_date: date
    end_date: date
    total_orders: int = Field(..., ge=0)
    total_revenue: float = Field(..., ge=0.0)

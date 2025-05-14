# app/api/endpoints/reports.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta 
import logging


from app.schemas import report as report_schema 
from app.services import report_service          
from app.db.database import get_db
from app.core.auth import require_admin 

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/sales/summary",
    response_model=report_schema.SalesReport,
    summary="Get Sales Summary Report (Admin only)",
    description="Retrieves a summary of sales figures (total orders and revenue) within a specified date range.",
    dependencies=[Depends(require_admin)] 
)
def get_sales_summary_report(
    start_date: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30), 
        description="Start date for the report (YYYY-MM-DD)"
    ),
    end_date: date = Query(
        default_factory=date.today, 
        description="End date for the report (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db)
):
    try:
        summary_data = report_service.get_sales_summary(
            db=db, start_date=start_date, end_date=end_date
        )
        return report_schema.SalesReport(
            start_date=start_date,
            end_date=end_date,
            **summary_data 
        )
    except Exception as e:
        logger.error(f"Error generating sales summary report: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate sales report")
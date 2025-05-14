# app/api/endpoints/permissions.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.schemas import permission as permission_schema 
from app.services import role_permission_service 
from app.db.database import get_db
from app.core.auth import get_current_active_superuser 

router = APIRouter()

@router.get(
    "/",
    response_model=List[permission_schema.Permission],
    summary="List all permissions (Admin only)",
    dependencies=[Depends(get_current_active_superuser)] 
)
def read_permissions(db: Session = Depends(get_db)):
    permissions = role_permission_service.get_permissions(db=db)
    return permissions


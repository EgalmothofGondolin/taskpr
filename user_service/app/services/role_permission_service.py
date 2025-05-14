# app/services/role_permission_service.py
from sqlalchemy.orm import Session, selectinload 
from typing import List, Optional, Union, Set
from fastapi import HTTPException, status

from app.db.models.role import Role as RoleModel
from app.db.models.permission import Permission as PermissionModel
from app.db.models.user import User as UserModel
from app.schemas.role import RoleCreate, RoleUpdate 

def get_roles(db: Session) -> List[RoleModel]:
    return db.query(RoleModel).options(selectinload(RoleModel.permissions)).all()

def get_permissions(db: Session) -> List[PermissionModel]:
    return db.query(PermissionModel).all()

def get_role_by_name(db: Session, name: str) -> Optional[RoleModel]:
    return db.query(RoleModel).filter(RoleModel.name == name).first()

def get_permission_by_name(db: Session, name: str) -> Optional[PermissionModel]:
    return db.query(PermissionModel).filter(PermissionModel.name == name).first()

def get_role_by_id(db: Session, role_id: int) -> Optional[RoleModel]:
     return db.query(RoleModel).options(selectinload(RoleModel.permissions)).filter(RoleModel.id == role_id).first()

def update_role_permissions(db: Session, role_id: int, permission_ids: List[int]) -> Optional[RoleModel]:
    db_role = get_role_by_id(db, role_id=role_id)
    if not db_role:
        return None 

    valid_permissions = []
    if permission_ids:
        valid_permissions = db.query(PermissionModel).filter(PermissionModel.id.in_(permission_ids)).all()
        if len(valid_permissions) != len(set(permission_ids)):
            found_ids = {perm.id for perm in valid_permissions}
            missing_ids = set(permission_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"One or more permissions not found: {missing_ids}"
            )

    db_role.permissions = valid_permissions 

    db.add(db_role)
    db.commit()
    db.refresh(db_role) 

    return db_role

def get_user_permission_names(user: UserModel) -> Set[str]:
     """Gets a set of permission names for a given user model."""
     all_perms = set()
     if user and user.roles: 
         for role in user.roles:
             if role.permissions: 
                 for perm in role.permissions:
                     all_perms.add(perm.name)
     return all_perms

def create_role(db: Session, role_in: RoleCreate) -> RoleModel:
    existing_role = db.query(RoleModel).filter(RoleModel.name == role_in.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{role_in.name}' already exists."
        )
    db_role = RoleModel(name=role_in.name, description=role_in.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role_details(db: Session, role_id: int, role_in: RoleUpdate) -> Optional[RoleModel]:
    db_role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not db_role:
        return None 

    update_data = role_in.model_dump(exclude_unset=True) 

    if "name" in update_data and update_data["name"] != db_role.name:
        existing_role = db.query(RoleModel).filter(RoleModel.name == update_data["name"]).first()
        if existing_role and existing_role.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{update_data['name']}' already exists."
            )

    for field, value in update_data.items():
        setattr(db_role, field, value)

    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_role_by_id(db: Session, role_id: int) -> Optional[RoleModel]:
    return db.query(RoleModel).filter(RoleModel.id == role_id).first()
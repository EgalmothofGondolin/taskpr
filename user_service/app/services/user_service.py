# app/services/user_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional, Any

from app.db.models.user import User as UserModel
from app.db.models.role import Role as RoleModel 
from app.schemas.user import UserCreate, UserUpdate, UserPasswordReset, UserRoleUpdate, UserPasswordUpdate 
from app.core.security import get_password_hash, verify_password 

def get_user(db: Session, user_id: int) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[UserModel]:
    return db.query(UserModel).offset(skip).limit(limit).all()

def create_user(db: Session, user_in: UserCreate) -> UserModel:
    existing_user_username = get_user_by_username(db, username=user_in.username)
    if existing_user_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered."
        )
    existing_user_email = get_user_by_email(db, email=user_in.email)
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered."
        )

    hashed_password = get_password_hash(user_in.password)

    user_data = user_in.model_dump(exclude={"password"})

    db_user = UserModel(**user_data, hashed_password=hashed_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user) 
    return db_user

def update_user(db: Session, user_id: int, user_in: UserUpdate) -> Optional[UserModel]:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return None

    update_data = user_in.model_dump(exclude_unset=True)

    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
        del update_data["password"] 

    if "username" in update_data and update_data["username"] != db_user.username:
        existing_user = get_user_by_username(db, username=update_data["username"])
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    if "email" in update_data and update_data["email"] != db_user.email:
        existing_user = get_user_by_email(db, email=update_data["email"])
        if existing_user and existing_user.id != user_id:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user) 
    db.commit()   
    db.refresh(db_user) 
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[UserModel]:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return None

    db_user.is_active = False

    db.add(db_user)
    db.commit()
    return db_user

def reset_user_password(db: Session, user_id: int, password_in: UserPasswordReset) -> Optional[UserModel]:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return None 

    hashed_password = get_password_hash(password_in.new_password)

    db_user.hashed_password = hashed_password

    db.add(db_user)
    db.commit()

    return db_user

def update_user_roles(db: Session, user_id: int, role_update_in: UserRoleUpdate) -> Optional[UserModel]:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return None 

    valid_roles = []
    if role_update_in.role_ids: 
        valid_roles = db.query(RoleModel).filter(RoleModel.id.in_(role_update_in.role_ids)).all()
        if len(valid_roles) != len(set(role_update_in.role_ids)):
             found_ids = {role.id for role in valid_roles}
             missing_ids = set(role_update_in.role_ids) - found_ids
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail=f"One or more roles not found: {missing_ids}"
             )

    db_user.roles = valid_roles 

    db.add(db_user)
    db.commit()
    db.refresh(db_user) 

    return db_user

def update_user_password(db: Session, user: UserModel, password_update: UserPasswordUpdate) -> bool:
    if not verify_password(password_update.current_password, user.hashed_password):
        return False 

    new_hashed_password = get_password_hash(password_update.new_password)

    user.hashed_password = new_hashed_password
    db.add(user)
    db.commit()
    return True 

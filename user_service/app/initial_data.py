# app/initial_data.py (Güncellenmiş)
import logging
from typing import List, Optional 

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.permission import Permission
from app.db.models.role import Role
from app.db.models.user import User
from app.schemas.user import UserCreate 
from app.services.user_service import get_user_by_email 

logger = logging.getLogger(__name__)

PERMISSIONS = {
    "users:read_self": "Read own user profile",
    "users:update_self": "Update own user profile",
    "users:delete_self": "Deactivate own user account", # Soft delete
    "users:read_all": "Read all users' profiles (Admin)",
    "users:update_any": "Update any user's profile (Admin)",
    "users:delete_any": "Deactivate any user's account (Admin)",
    "users:reset_password_any": "Reset password for any user (Admin)",
    "users:manage_roles": "Assign/remove roles for any user (Admin)",
    "addresses:create_own": "Create own addresses",
    "addresses:read_own": "Read own addresses",
    "addresses:update_own": "Update own addresses",
    "addresses:delete_own": "Delete own addresses",
    "contacts:create_own": "Create own contacts",
    "contacts:read_own": "Read own contacts",
    "contacts:update_own": "Update own contacts",
    "contacts:delete_own": "Delete own contacts",
    "products:create": "Create products (Admin)",
    "products:update": "Update products (Admin)",
    "products:delete": "Delete products (Admin)",
    # "cart:manage_own": "Manage own shopping cart",
    # "orders:create_own": "Create own orders",
    # "orders:read_own": "Read own orders",
}

ROLES = {
    "ADMIN": {
        "description": "Administrator with full system access",
        "permissions": list(PERMISSIONS.keys()) 
    },
    "USER": {
        "description": "Standard user with basic access",
        "permissions": [
            "users:read_self",
            "users:update_self",
            # "users:delete_self", 
            "addresses:create_own", "addresses:read_own", "addresses:update_own", "addresses:delete_own",
            "contacts:create_own", "contacts:read_own", "contacts:update_own", "contacts:delete_own",
            # "cart:manage_own",
            # "orders:create_own",
            # "orders:read_own",
        ]
    }
}


def get_or_create_permission(db: Session, name: str, description: Optional[str]) -> Permission:
    instance = db.query(Permission).filter(Permission.name == name).first()
    if not instance:
        instance = Permission(name=name, description=description)
        db.add(instance)
        db.flush() 
        logger.info(f"Permission '{name}' created.")
    elif description and instance.description != description:
         instance.description = description
         db.add(instance)
         logger.info(f"Permission '{name}' description updated.")
    return instance

def get_or_create_role(db: Session, name: str, description: Optional[str], permission_objs: List[Permission]) -> Role:
    instance = db.query(Role).filter(Role.name == name).first()
    if not instance:
        instance = Role(name=name, description=description)
        db.add(instance)
        db.flush() 
        logger.info(f"Role '{name}' created.")

    if description and instance.description != description:
        instance.description = description

    current_perm_ids = {p.id for p in instance.permissions}
    new_perm_ids = {p.id for p in permission_objs}
    if current_perm_ids != new_perm_ids:
        instance.permissions = permission_objs 
        logger.info(f"Permissions updated for role '{name}'.")

    db.add(instance) 
    return instance

def create_or_get_superuser(db: Session) -> User:
    """Ensures the first superuser exists and has the ADMIN role."""
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    if not admin_role:
        logger.error("CRITICAL: ADMIN role not found in database during superuser creation.")
        raise Exception("ADMIN role definition missing.") # Veya uygun bir exception

    user = get_user_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)

    if not user:
        logger.info(f"Creating superuser '{settings.FIRST_SUPERUSER_USERNAME}' with email '{settings.FIRST_SUPERUSER_EMAIL}'.")
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER_USERNAME,
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
        )
        hashed_password = get_password_hash(user_in.password)
        user_data = user_in.model_dump(exclude={"password"})

        db_user = User(**user_data, hashed_password=hashed_password, roles=[admin_role], is_active=True)
        db.add(db_user)
        logger.info(f"Superuser '{db_user.username}' will be created with role 'ADMIN'.")
        return db_user 
    else:
        logger.info(f"Superuser '{user.username}' already exists.")
        user_has_admin_role = any(role.name == "ADMIN" for role in user.roles)
        if not user_has_admin_role:
            logger.warning(f"Assigning ADMIN role to existing superuser '{user.username}'.")
            user.roles.append(admin_role)
            db.add(user)
        return user


def init_db(db: Session) -> None:
    try:
        logger.info("Starting initial data setup...")

        logger.info("Processing permissions...")
        permission_map = {
            name: get_or_create_permission(db, name, desc)
            for name, desc in PERMISSIONS.items()
        }
        db.flush() 

        logger.info("Processing roles and assigning permissions...")
        role_map = {}
        for role_name, role_data in ROLES.items():
            role_perms = [permission_map[p_name] for p_name in role_data["permissions"] if p_name in permission_map]
            role_obj = get_or_create_role(db, role_name, role_data["description"], role_perms)
            role_map[role_name] = role_obj
        db.flush()

        logger.info("Processing superuser...")
        create_or_get_superuser(db=db)
        db.flush()

        logger.info("Committing initial data changes...")
        db.commit()
        logger.info("Initial data setup finished successfully.")

    except Exception as e:
         logger.error(f"CRITICAL: Error during initial data setup: {e}", exc_info=True)
         logger.warning("Rolling back initial data changes...")
         db.rollback() 

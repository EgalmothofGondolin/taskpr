# app/db/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Table, ForeignKey
from sqlalchemy.orm import relationship


from app.db.database import Base 

user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions_table = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"  

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False) 
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False) 
    first_name = Column(String(50), index=True, nullable=True) 
    last_name = Column(String(50), index=True, nullable=True)
    is_active = Column(Boolean, default=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) 

    addresses = relationship(
        "Address",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select" 
    )

    contacts = relationship(
        "Contact",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select"
    )

    roles = relationship(
        "Role",
        secondary=user_roles_table, 
        back_populates="users",
        lazy="selectin" 
    )

    @property
    def permissions(self) -> set[str]:
        all_perms = set()
        for role in self.roles:
            for perm in role.permissions:
                all_perms.add(perm.name)
        return all_perms

    def has_permission(self, permission_name: str) -> bool:
        return permission_name in self.permissions

    def __repr__(self):
        role_names = ", ".join([r.name for r in self.roles])
        return f"<User(username='{self.username}', roles='{role_names}')>"
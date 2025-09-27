
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean,Text,DateTime, Table
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql.sqltypes import Float, Date


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    role = Column(String(255), index=True)

    # Relationships
    normal_user = relationship("normal_user", back_populates="user", uselist=False)
    admin = relationship("Admin", back_populates="user", uselist=False)


class normal_user(Base):
    __tablename__ = "normal_users"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="normal_user")


class Admin(Base):
    __tablename__ = "admins"
    
    ##permissions = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="admin")
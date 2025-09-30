from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, Table
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql.sqltypes import Float, Date
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    name = Column(String(255))
    profile_photo = Column(String(255), nullable=True)
    role = Column(String(255), index=True)
    
    # Relationship with Admin
    admin = relationship("Admin", back_populates="user", uselist=False)
    # Relationship with rooms (as creator)
    created_rooms = relationship("Room", back_populates="creator")
    # Relationship with room memberships
    room_memberships = relationship("RoomMember", back_populates="user")

class Admin(Base):
    __tablename__ = "admins"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="admin")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    max_members = Column(Integer, default=10)  # Maximum members allowed
    
    # Relationships
    creator = relationship("User", back_populates="created_rooms")
    members = relationship("RoomMember", back_populates="room")

class RoomMember(Base):
    __tablename__ = "room_members"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(50), default="member")  # member, admin, owner
    
    # Relationships
    room = relationship("Room", back_populates="members")
    user = relationship("User", back_populates="room_memberships")
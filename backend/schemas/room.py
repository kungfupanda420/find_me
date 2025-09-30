from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_members: Optional[int] = 10

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_members: Optional[int] = None
    is_active: Optional[bool] = None

class RoomResponse(RoomBase):
    id: int
    created_by: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class RoomMemberResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    role: str
    joined_at: datetime
    
    class Config:
        from_attributes = True

class RoomWithMembersResponse(RoomResponse):
    members: List[RoomMemberResponse] = []
    creator_name: str
    
    class Config:
        from_attributes = True
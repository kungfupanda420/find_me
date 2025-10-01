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
    code: str
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

class JoinRoomResponse(BaseModel):
    message: str
    room_id: int
    room_name: str

class LeaveRoomResponse(BaseModel):
    message: str

class DeleteRoomResponse(BaseModel):
    message: str

# Additional schemas for room operations
class RoomJoinRequest(BaseModel):
    room_code: str

class RoomInviteResponse(BaseModel):
    room_code: str
    room_name: str
    invite_url: Optional[str] = None

class RoomStatsResponse(BaseModel):
    room_id: int
    room_name: str
    total_members: int
    max_members: int
    created_at: datetime
    is_active: bool
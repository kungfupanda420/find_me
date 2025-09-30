from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.users import User, Room, RoomMember
from schemas.room import RoomCreate, RoomResponse, RoomUpdate, RoomWithMembersResponse
from security.oauth2 import get_current_user
from datetime import datetime

router = APIRouter(
    prefix="/api/rooms",
    tags=["Rooms"]
)


get_db = get_db
@router.post("/create_room", response_model=RoomResponse)
def create_room(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new room
    """
    # Check if room name already exists
    existing_room = db.query(Room).filter(Room.name == room_data.name).first()
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room name already exists"
        )
    
    # Create new room
    new_room = Room(
        name=room_data.name,
        description=room_data.description,
        max_members=room_data.max_members,
        created_by=current_user.id
    )
    
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    # Add creator as room member with owner role
    creator_member = RoomMember(
        room_id=new_room.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(creator_member)
    db.commit()
    
    return new_room

@router.get("/rooms", response_model=List[RoomWithMembersResponse])
def get_my_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all rooms where current user is a member
    """
    # Get room IDs where user is a member
    user_room_ids = db.query(RoomMember.room_id).filter(
        RoomMember.user_id == current_user.id
    ).all()
    user_room_ids = [room_id for (room_id,) in user_room_ids]
    
    # Get rooms with their members
    rooms = db.query(Room).filter(Room.id.in_(user_room_ids)).all()
    
    room_responses = []
    for room in rooms:
        # Get room members with user details
        members = db.query(RoomMember, User).join(
            User, RoomMember.user_id == User.id
        ).filter(RoomMember.room_id == room.id).all()
        
        member_responses = []
        for member, user in members:
            member_responses.append({
                "id": member.id,
                "user_id": user.id,
                "user_name": user.name,
                "user_email": user.email,
                "role": member.role,
                "joined_at": member.joined_at
            })
        
        # Get creator name
        creator = db.query(User).filter(User.id == room.created_by).first()
        
        room_responses.append({
            **room.__dict__,
            "members": member_responses,
            "creator_name": creator.name if creator else "Unknown"
        })
    
    return room_responses

@router.get("/rooms/{room_id}", response_model=RoomWithMembersResponse)
def get_room_details(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific room details
    """
    # Check if user is member of this room
    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Get room members with user details
    members = db.query(RoomMember, User).join(
        User, RoomMember.user_id == User.id
    ).filter(RoomMember.room_id == room_id).all()
    
    member_responses = []
    for member, user in members:
        member_responses.append({
            "id": member.id,
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email,
            "role": member.role,
            "joined_at": member.joined_at
        })
    
    # Get creator name
    creator = db.query(User).filter(User.id == room.created_by).first()
    
    return {
        **room.__dict__,
        "members": member_responses,
        "creator_name": creator.name if creator else "Unknown"
    }

@router.put("/rooms/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update room details (only room owner/admin can update)
    """
    # Check if user has permission to update (owner or admin role in room)
    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id,
        RoomMember.role.in_(["owner", "admin"])
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this room"
        )
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Update room fields
    update_data = room_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    
    return room

@router.post("/rooms/{room_id}/join")
def join_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Join a room
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    if not room.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is not active"
        )
    
    # Check if user is already a member
    existing_member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this room"
        )
    
    # Check if room has reached maximum members
    current_member_count = db.query(RoomMember).filter(
        RoomMember.room_id == room_id
    ).count()
    
    if current_member_count >= room.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room has reached maximum member limit"
        )
    
    # Add user as room member
    new_member = RoomMember(
        room_id=room_id,
        user_id=current_user.id,
        role="member"
    )
    
    db.add(new_member)
    db.commit()
    
    return {"message": "Successfully joined the room"}

@router.delete("/rooms/{room_id}/leave")
def leave_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Leave a room
    """
    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not a member of this room"
        )
    
    # If user is the owner, handle ownership transfer or delete room
    if membership.role == "owner":
        # Check if there are other members who could be made owner
        other_members = db.query(RoomMember).filter(
            RoomMember.room_id == room_id,
            RoomMember.user_id != current_user.id
        ).all()
        
        if other_members:
            # Transfer ownership to the first admin or member
            new_owner = next((m for m in other_members if m.role == "admin"), other_members[0])
            new_owner.role = "owner"
        else:
            # No other members, delete the room
            room = db.query(Room).filter(Room.id == room_id).first()
            db.delete(room)
    
    db.delete(membership)
    db.commit()
    
    return {"message": "Successfully left the room"}
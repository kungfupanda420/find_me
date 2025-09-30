from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from schemas.token import Token
from schemas.login import UserLogin, ForgotPasswordRequest, ChangePasswordRequest
from models.users import User, Admin
# from models.rounds import Round
from security.JWTtoken import create_access_token, create_refresh_token, verify_access_token
from database import get_db

from passlib.context import CryptContext

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from security.oauth2 import get_current_user

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
from dotenv import load_dotenv

from datetime import timedelta, datetime
import shutil

from urllib.parse import urlencode

import random
import string


router = APIRouter(
    prefix="/api",
    tags=["Login"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

get_db = get_db

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

# Define profile photos directory
PROFILE_PHOTOS_DIR = "profile_photos"
os.makedirs(PROFILE_PHOTOS_DIR, exist_ok=True)

conf = ConnectionConfig(
    MAIL_USERNAME='pratheek18183@gmail.com',
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_FROM='pratheek18183@gmail.com',
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

@router.post("/auth/google/login")
async def google_login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="No token provided")

    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo["email"]
    except Exception as e:
        print("Google token verification failed:", e)
        raise HTTPException(status_code=401, detail="Invalid Google token")
    
    # Commented out round check since Round model is not available
    # round = db.query(Round).filter(Round.id == 1).first()
    user = db.query(User).filter(User.email == email).first()
    
    # Commented out round-related logic
    # if user and user.role == "Verified Email" and (round.number == 3 and round.allow_reg == 0):
    #     raise HTTPException(status_code=403, detail="Student Internship Portal is not open for registration anymore")
        
    if not user:
        # Commented out round-related logic
        # if round.allow_reg == 0:
        #     raise HTTPException(status_code=403, detail="Student Internship Portal is not open for registration")
        
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))    
        user = User(
            email=email,
            password=pwd_context.hash(password),
            role="Verified Email"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # No need to create normal_user entry anymore

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user.role,
        "email": user.email
    }

@router.post('/login')  
def login(request: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not Found")
    if not pwd_context.verify(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    print(access_token)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        id=user.id,
        email=user.email,
        role=user.role
    )

@router.post('/forgot_password') 
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        return {"msg": "If this email exists, a reset link will be sent."}
    
    reset_token = create_access_token(
        data={"sub": request.email},
        expires_delta=timedelta(minutes=30)
    )
    frontend_url = os.getenv('FRONTEND_URL')
    reset_link = f"{frontend_url}/reset_password?token={reset_token}"

    message = MessageSchema(
        subject="Change password on NITC SIP Portal",
        recipients=[request.email],
        body=f"""
        <h3>Password Reset</h3>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_link}">{reset_link}</a>
        <p>If you didn't request this, you can ignore this email.</p>
        """,
        subtype="html"
    )
    fm = FastMail(conf)

    await fm.send_message(message)
    return {"msg": f"Password Reset email sent to {request.email}"}

@router.post('/change_password') 
async def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = verify_access_token(request.token)
        email = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password = pwd_context.hash(request.password)
    db.commit() 
    db.refresh(user)    
    return {"msg": "Password changed successfully"}


@router.post('/register')
async def register(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    profile_photo: UploadFile = File(None),  # Make it optional
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Handle profile photo upload
    profile_photo_path = None
    if profile_photo:
        # Validate file type
        allowed_content_types = ['image/jpeg', 'image/png', 'image/gif']
        if profile_photo.content_type not in allowed_content_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and GIF are allowed.")
        
        # Generate unique filename
        file_extension = profile_photo.filename.split('.')[-1]
        filename = f"{email}_{int(datetime.now().timestamp())}.{file_extension}"
        file_path = os.path.join(PROFILE_PHOTOS_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(profile_photo.file, buffer)
        
        profile_photo_path = file_path
    
    # Create user
    hashed_password = pwd_context.hash(password)
    new_user = User(
        email=email,
        password=hashed_password,
        name=name,  # Add name
        profile_photo=profile_photo_path,  # Add profile photo path
        role="Verified Email"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # No need to create normal_user entry anymore
    
    return {
        "msg": "User registered successfully", 
        "user_id": new_user.id, 
        "email": new_user.email,
        "name": new_user.name,
        "profile_photo": new_user.profile_photo
    }

# Updated endpoints for user type checking
@router.get('/user/{user_id}/type')
def get_user_type(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is an admin
    admin = db.query(Admin).filter(Admin.user_id == user_id).first()
    if admin:
        return {"user_type": "admin", "user_id": user_id}
    
    # If not admin, it's a regular user
    return {"user_type": "user", "user_id": user_id}

# Endpoint to promote a user to admin
@router.post('/user/{user_id}/promote-to-admin')
def promote_to_admin(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is already an admin
    existing_admin = db.query(Admin).filter(Admin.user_id == user_id).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="User is already an admin")
    
    # Add to admin
    admin_entry = Admin(user_id=user_id)
    db.add(admin_entry)
    db.commit()
    
    return {"msg": f"User {user_id} promoted to admin successfully"}

# Endpoint to demote an admin to regular user
@router.post('/user/{user_id}/demote-to-user')
def demote_to_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is an admin
    admin_entry = db.query(Admin).filter(Admin.user_id == user_id).first()
    if not admin_entry:
        raise HTTPException(status_code=400, detail="User is not an admin")
    
    # Remove from admin
    db.delete(admin_entry)
    db.commit()
    
    return {"msg": f"User {user_id} demoted to regular user successfully"}
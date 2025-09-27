from fastapi import APIRouter, Depends, HTTPException, status, Response, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from schemas.token import Token

from models.users import User,Admin

from security.JWTtoken import create_access_token
from database import get_db

from passlib.context import CryptContext

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from security.oauth2 import get_current_user

import pandas as pd
import random
import string


from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
import io
import os

from typing import List
router =APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

get_db=get_db

import os

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel


from dotenv import load_dotenv
load_dotenv()
conf = ConnectionConfig(
    MAIL_USERNAME='sip@nitc.ac.in',
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_FROM='sip@nitc.ac.in',
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS= False,
    USE_CREDENTIALS=True
)

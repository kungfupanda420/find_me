
from pydantic import BaseModel, EmailStr
from datetime import date

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    token:str
    password:str
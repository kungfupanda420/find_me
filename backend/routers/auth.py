from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from schemas.token import Token, RefreshTokenRequest
from models.users import User
from security.JWTtoken import create_access_token, create_refresh_token
from database import get_db

from passlib.context import CryptContext

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from security.oauth2 import get_current_user

from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from security import JWTtoken

router =APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

get_db=get_db

@router.post("/refresh_token")
def refresh_access_token(request:RefreshTokenRequest,db:Session=Depends(get_db)):
    
    try :
        payload= JWTtoken.jwt.decode(request.refresh_token,JWTtoken.REFRESH_SECRET_KEY, algorithms=[JWTtoken.ALGORITHM])
        email=payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    user=db.query(User).filter(User.email==email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    access_token=create_access_token(data={"sub":user.email})
    refresh_token=create_refresh_token(data={"sub":user.email})


    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        id=user.id,
        email=user.email,
        role=user.role
    )
    
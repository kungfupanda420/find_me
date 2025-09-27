from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

from models.users import User
from schemas.token import TokenData
from . import JWTtoken

from sqlalchemy.orm import Session
from database import get_db
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                     db: Session = Depends(get_db)
                     ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email: str = None
    try:
        payload = jwt.decode(token, JWTtoken.SECRET_KEY, algorithms=[JWTtoken.ALGORITHM])
        email= payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError as err:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()

    return user
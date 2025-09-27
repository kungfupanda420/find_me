from pydantic import BaseModel


class Token(BaseModel):
    id:int
    email: str
    role:str
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: str = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str
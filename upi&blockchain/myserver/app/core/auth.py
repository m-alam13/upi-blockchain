from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings
import bcrypt
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from fastapi import Request, HTTPException, status, Depends
from starlette.responses import RedirectResponse

# Set up password hashing context


# Function to hash the password
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))

# Function to verify the password against the hashed one
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    # return pwd_context.verify(plain_password, hashed_password)

# Function to create an access token (JWT)
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Function to verify the token and get the payload (decode JWT)
# def verify_access_token(token: str):
#     credentials_exception = JWTError("Could not validate credentials")
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         return payload
#     except JWTError:
#         raise credentials_exception

def verify_access_token_from_cookie(request: Request):
    token = request.cookies.get("jwt")
    if not token:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload  # Return decoded token data
    except JWTError:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="Token invalid")
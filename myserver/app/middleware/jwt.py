from starlette.status import HTTP_302_FOUND
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(data: dict, key= settings.SECRET_KEY, exp_time=settings.ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=exp_time)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, key, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_access_token(token, key=settings.SECRET_KEY):
    # token = request.cookies.get("jwt")
    if not token:
        raise #HTTPException(status_code=status.HTTP_302_FOUND, detail="Token not found")

    try:
        payload = jwt.decode(token, key, algorithms=[settings.ALGORITHM])
        return payload  # Return decoded token data
    except JWTError:
        raise #HTTPException(status_code=status.HTTP_302_FOUND, detail="Token invalid")
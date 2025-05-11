from app.schemas import user_schema
from app.models import user_model
from app.core.db import get_db
from fastapi import Depends

from sqlalchemy.orm import Session
from app.core.auth import create_access_token, verify_password, hash_password
from fastapi import HTTPException
from fastapi.responses import JSONResponse, Response, RedirectResponse
from app.core.config import settings


# Function to handle user signup
async def signup(user: user_schema.UserCreate, db):
    print(user)
    # Check if user already exists
    db_user = db.query(user_model.User).filter(user_model.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password before saving it (you can use a hashing function here)
    hashed_password = hash_password(user.password)
    print(hashed_password)
    db_user = user_model.User(email=user.email,name=user.name, mobile=user.mobile, password=hashed_password)
    db.add(db_user)
    db.commit()
    # print(user)
    token = create_access_token({"user_id":db_user.id,"email": db_user.email, 'uupi':db_user.uupi or 0 })
    res = JSONResponse(content={"message": "Created"}, status_code=201)
    res.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES *60
    )
    return res

# Example login function (you would normally check the password)
async def login(response ,user: user_schema.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(user_model.User).filter(user_model.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # print(db_user.id)
  
    token = create_access_token({"user_id":db_user.id,"email": db_user.email, 'uupi':db_user.uupi or 0 })
    # return {"access_token": token, "token_type": "bearer"}
    # res = JSONResponse(content={"message": "login successsfull"}, status_code=200)
    if not not getattr(db_user, "uupi", None):
        res = RedirectResponse(url="/complete-profile", status_code=302)
    else:
        res = JSONResponse(content={"message": "login successful"}, status_code=200)
    res.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES *60
    )
    return res
    # response.set_cookie(
    #     key="jwt",
    #     value=token,         # Ideally a secure token
    #     httponly=True,          # JS can't access this cookie
    #     secure=False,           # Set to True in production (HTTPS only)
    #     samesite="lax",         # 'lax', 'strict', or 'none'
    #     max_age=60            # Optional: cookie lifetime in seconds
    # )
    # # return {"access_token": token, "token_type": "bearer"}
    # return JSONResponse(content={"message": "Created"}, status_code=201)

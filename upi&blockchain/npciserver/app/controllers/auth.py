from app.schemas import user_schema
from app.models import user_model
from app.core.db import get_db
from fastapi import Depends

from sqlalchemy.orm import Session
from app.core.auth import create_access_token, verify_password, hash_password
from fastapi import HTTPException
from fastapi.responses import JSONResponse, Response, RedirectResponse
from app.core.config import settings
from app.middleware.jwt import create_access_token, verify_access_token
from urllib.parse import urlencode


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
    # token = create_access_token({"user_id":db_user.id,"email": db_user.email, 'uupi':db_user.uupi or 0 })
    # res = JSONResponse(content={"message": "Created"}, status_code=201)
    # res.set_cookie(
    #     key="jwt",
    #     value=token,
    #     httponly=True,
    #     secure=False,
    #     samesite="lax",
    #     max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES *60
    # )
    data = {
        'email': db_user.email,
        'callback_url': "http://localhost:8000/verify-callback"
    }
    server_token = create_access_token(data,settings.SERVER_TO_SERVER_SECRET_KEY, settings.SERVER_TO_SERVER_EXPIRE_MINUTES)
    callback_params = {
            "token": server_token,
            'callback_url': "http://localhost:8000/verify-callback"
        
        }
        # return JSONResponse(
        #     content={"redirect_url": f"{settings.KYC_SERVER}?{urlencode(callback_params)}"},
        #     status_code=200
        # )
    return RedirectResponse(f"{settings.KYC_SERVER}/verify?{urlencode(callback_params)}", status_code=303)
    # return RedirectResponse(f"{settings.KYC_SERVER}?{urlencode(callback_params)}", status_code=303)
    # return res

# Example login function (you would normally check the password)
async def login(response ,user: user_schema.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(user_model.User).filter(user_model.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # print(db_user.id)
    if not db_user.uupi:
        data = {
        'email': db_user.email,
        'callback_url': "http://localhost:8000/verify-callback"
    }
        server_token = create_access_token(data,settings.SERVER_TO_SERVER_SECRET_KEY, settings.SERVER_TO_SERVER_EXPIRE_MINUTES)
        callback_params = {
                "token": server_token,
                'callback_url': "http://localhost:8000/verify-callback"
            
            }
        # return JSONResponse(
        #     content={"redirect_url": f"{settings.KYC_SERVER}?{urlencode(callback_params)}"},
        #     status_code=200
        # )
        return RedirectResponse(f"{settings.KYC_SERVER}/verify?{urlencode(callback_params)}", status_code=303)
  
    token = create_access_token({"user_id":db_user.id,"email": db_user.email, 'uupi':db_user.uupi or 0 })
    # return {"access_token": token, "token_type": "bearer"}
    # res = JSONResponse(content={"message": "login successsfull"}, status_code=200)
    # if not getattr(db_user, "uupi", None):
    #     res = RedirectResponse(url="/complete-profile", status_code=302)
    # else:
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


def insert_uupi(db: Session, verification_token: str, status: str, tax_data: str = None):
    if status == 'success':
        try:
            data = verify_access_token(verification_token, settings.SERVER_TO_SERVER_SECRET_KEY)
            print(data)
            if len(data)>0:
                print(data.get('email'))
                user = db.query(user_model.User).filter(user_model.User.email == data.get('email')).first()
                print(user)
                if not user:
                    return RedirectResponse(url="/signup", status_code=302)

                user.uupi = data.get("uupi")
                db.commit()
                db.refresh(user)
                return RedirectResponse(url="/wallet", status_code=302)
            else:
                print(data.get('email'))
        except Exception as e:
            return RedirectResponse(url="/signup", status_code=302)
    
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from urllib.parse import urlencode
import base64
from fastapi import Form
from app.core.db import get_db
from sqlalchemy.orm import Session
import time
import random
import os
from pathlib import Path
from app.models.user_model import User
from app.middleware.jwt import verify_access_token, create_access_token
from app.core.config import settings
from typing import Optional

router = APIRouter(tags=["verification"])

# Verification Form (GET)
@router.get("/verify", response_class=HTMLResponse)
async def verification_page(
    request: Request,
    # verification_id: str,
    callback_url: str,
    token: Optional[str]
):  
    verify_token = None
    try:
        verify_token = verify_access_token(token, settings.SERVER_TO_SERVER_SECRET_KEY)
        if verify_token:
            return request.app.state.templates.TemplateResponse(
                "kyc.html",
                {
                    "request": request,
                    "token":token,
                    # "verification_id": verification_id,
                    "callback_url": callback_url
                }
            )
    except Exception as e:

        callback_params = {
        
        "status": "error",
    
        }
        callback_url = verify_token.get('callback_url') if verify_token and verify_token.get('callback_url') else callback_url
        return RedirectResponse(f"{callback_url}?{urlencode(callback_params)}", status_code=303)

# Process Verification (POST)

@router.post("/verify")
async def process_verification(
    request: Request,
    # token: str = Form(...),
    callback_url: str = Form(...),
    token: str = Form(...),  # JWT from the form
    pan: str = Form(...),
    name: str = Form(...),
    mobile: str = Form(...),
    # uupi: str = Form(...),
    selfie: str = Form(...),
    db: Session = Depends(get_db)
):
    # Decode base64 selfie image (data:image/png;base64,...)
    # try:
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #     verification_id = payload.get("verification_id")
    #     callback_url = payload.get("callback_url")

    #     if not verification_id or not callback_url:
    #         raise HTTPException(status_code=400, detail="Invalid token payload")

    # except JWTError:
    #     raise HTTPException(status_code=403, detail="Invalid or expired token")
    print("process_verification")
    verify_token = None
    try:
        
        verify_token = verify_access_token(token, settings.SERVER_TO_SERVER_SECRET_KEY)
        header, encoded = selfie.split(",", 1)
        selfie_bytes = base64.b64decode(encoded)
        numeric_id = str(int(time.time() * 1000) )+ str(random.randint(000, 999))[:16]
        upload_dir = Path("asset/selfies")
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{numeric_id}.png"
        file_path = upload_dir / filename

        existing_user = db.query(User).filter_by(pan=pan).first()

        if existing_user:
            # User exists, return existing uupi
            verify_token['uupi'] =  existing_user.uupi
            # return {"status": "exists", "uupi": existing_user.uupi}
        else:
            with open(file_path, "wb") as f:
                f.write(selfie_bytes)

            # Save user
            user = User(
                pan=pan,
                name=name,
                mobile=mobile,
                uupi=numeric_id,
                image_path=file_path
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            verify_token['uupi'] = numeric_id

        # Redirect to callback
        callback_url = verify_token.get('callback_url')
        
        verification_token = create_access_token(verify_token,settings.SERVER_TO_SERVER_SECRET_KEY, settings.SERVER_TO_SERVER_EXPIRE_MINUTES)
        callback_params = {
            "verification_token": verification_token,
            "status": "success",
          
        }
        print(f"{callback_url}?{urlencode(callback_params)}")
        return RedirectResponse(f"{callback_url}?{urlencode(callback_params)}", status_code=303)
    except Exception as e:
        callback_params = {
        
        "status": "error",
    
        }
        callback_url = verify_token.get('callback_url') if verify_token and verify_token.get('callback_url') else callback_url
        return RedirectResponse(f"{callback_url}?{urlencode(callback_params)}", status_code=303)